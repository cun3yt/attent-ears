import datetime
import json
import sys

import httplib2
from apiclient import discovery
from django.utils import timezone
from googleapiclient.errors import HttpError
from oauth2client import client

from apps.google_calendar.models import GoogleCalendarListSyncState, GoogleCalendar, GoogleCalendarApiLogs, \
    GoogleCalendarEvent
from apps.visualizer.models import User, Client
from ears.env_variables import GOOGLE_OAUTH2_KEY, GOOGLE_OAUTH2_SECRET
from ears.auth_settings import GOOGLE_TOKEN_URI


class RetrySync(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class CalendarConnector:  # Google API connection for a given User
    def __init__(self, user: User):
        oauth2_user = user.get_google_oauth2_user()
        self._service = self._setup_client(oauth2_user)

    @staticmethod
    def _setup_client(oauth2_user):
        auth_details = oauth2_user.extra_data

        credentials = client.OAuth2Credentials(
            access_token=auth_details['access_token'],
            client_id=GOOGLE_OAUTH2_KEY,
            client_secret=GOOGLE_OAUTH2_SECRET,
            refresh_token=auth_details['refresh_token'],
            token_expiry=datetime.datetime.fromtimestamp(
                auth_details['auth_time'] + auth_details['expires']
            ),
            token_uri=GOOGLE_TOKEN_URI,
            user_agent='attent-user-agent/1.0',
        )

        http = credentials.authorize(httplib2.Http())
        return discovery.build('calendar', 'v3', http=http)

    def get_service(self):
        return self._service


class CalendarStorage:
    def __init__(self, logger_fn):
        self._logger_fn = logger_fn

    @staticmethod
    def get_last_calendar_list_sync_state(user: User):
        last_sync = GoogleCalendarListSyncState.get_last_sync(user)
        if last_sync is None:
            return {
                GoogleCalendar.KV_SYNC_STATE_KEY: GoogleCalendar.KV_SYNC_STATE_VAL_UNINITIALIZED,
            }

        return {
            GoogleCalendar.KV_SYNC_STATE_KEY: GoogleCalendar.KV_SYNC_STATE_VAL_INITIALIZED,
            'page_token': last_sync.get_page_token(),
            'sync_token': last_sync.get_sync_token(),
        }

    @staticmethod
    def get_calendars(app_client: Client):
        return GoogleCalendar.objects.filter(sync_user__client=app_client).filter(is_kept_in_sync=True)

    @staticmethod
    def save_calendars(api_response, sync_user: User):
        calendars = api_response.get('items', None)
        for cal in calendars:
            email_address = cal.get('id')
            timezone = cal.get('timeZone')

            access_role = cal.get('accessRole', 'freeBusyReader')
            to_be_in_sync = sync_user.client.is_email_address_in_domain(email_address) \
                and not (access_role == 'freeBusyReader')

            calendar, _ = GoogleCalendar.objects.get_or_create(
                email_address=email_address,
                defaults={
                    'sync_user': sync_user,
                    'is_kept_in_sync': to_be_in_sync,
                    'timezone': timezone,
                    'sync_user_access_role': access_role,
                }
            )

            if calendar.sync_user.id != sync_user.id:           # Will this cause flip flops and sync state problems?
                history_item = {'user_id': calendar.sync_user.id,
                                'end': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                calendar.sync_user_history['list'] = calendar.sync_user_history.get('list', [])
                calendar.sync_user_history['list'].append(history_item)

            calendar.sync_user = sync_user
            calendar.is_kept_in_sync = to_be_in_sync
            calendar.timezone = timezone
            calendar.sync_user_access_role = access_role
            calendar.save()

    @staticmethod
    def get_last_calendar_sync_state(calendar: GoogleCalendar):
        return calendar.get_last_sync_state()

    # Wrap everything in a transaction to avoid half sync'ed state!

    @staticmethod
    def save_calendar_events(api_response, app_client: Client):
        event_list = api_response.get('items')

        for event_item in event_list:

            event_status = event_item.get('status')
            if event_status == 'cancelled':
                print("A cancelled event. Will delete if exists: {}".format(event_item.get('id')))
                try:
                    event = GoogleCalendarEvent.objects.get(event_id=event_item.get('id'))
                    event.delete()
                except GoogleCalendarEvent.DoesNotExist:
                    pass
                continue

            event_defaults = {
                'attendees': event_item.get('attendees', {}),
                'created': event_item.get('created', event_item.get('updated')),
                'creator': event_item.get('creator', {}),
                'description': event_item.get('description', ''),
                'end': event_item.get('end', {}),
                'html_link': event_item.get('htmlLink', ''),
                'organizer': event_item.get('organizer', {}),
                'start': event_item.get('start', {}),
                'recurring_event_id': event_item.get('recurringEventId', ''),
                'summary': event_item.get('summary', ''),
                'updated': event_item.get('updated'),
                'client': app_client,
                'status': event_item.get('status'),
            }

            if event_defaults.get('updated') is None:
                raise Exception("Empty 'updated' field", event_item)

            GoogleCalendarEvent.objects.update_or_create(event_id=event_item.get('id'),
                                                         defaults=event_defaults)

    def log(self, **kwargs):
        self._logger_fn(**kwargs)


class CalendarSyncer:
    CAL_LIST_FIELDS = 'items(accessRole,deleted,description,hidden,id,location,' \
                      'primary,summary,summaryOverride,timeZone),nextPageToken,nextSyncToken'

    CAL_EVENT_FIELDS = 'items(' \
                       'attendees(additionalGuests,displayName,email,id,optional,resource,responseStatus),' \
                       'created,creator(displayName,email),description,' \
                       'end,htmlLink,id,organizer(displayName,email),recurringEventId,' \
                       'start,status,summary,updated' \
                       '),' \
                       'nextPageToken,nextSyncToken,timeZone'

    CAL_EVENT_TIME_MIN = '2015-01-01T00:00:00+00:00'

    def __init__(self, user: User, storage: CalendarStorage):
        self._user = user
        self._connector = CalendarConnector(user=user)
        self._storage = storage

    def sync_calendar_list(self):
        print("Syncing Calendar List for {}".format(self._user.email))
        for trial in range(3):
            try:
                sync_state = self._storage.get_last_calendar_list_sync_state(self._user)
                self._sync_calendar_list_from_state(sync_state)
                break
            except RetrySync as e:
                if e.status_code == 410:
                    print("Wiping out list sync state for user: {}".format(self._user.id))
                    sync_object = GoogleCalendarListSyncState(user=self._user)
                    sync_object.save()
            except Exception as e:
                print("Unexpected error: {}", sys.exc_info()[0])

    def _sync_calendar_list_from_state(self, sync_state):
        fields = self.CAL_LIST_FIELDS
        service = self._connector.get_service()

        page_token = sync_state.get('page_token')
        sync_token = sync_state.get('sync_token')

        while True:
            try:
                print(" fetching page of calendar list")
                response = service.calendarList().list(fields=fields, pageToken=page_token, syncToken=sync_token)\
                    .execute()
            except HttpError as exception:
                status_code = exception.resp.status
                error_msg = json.loads(exception.content)['error']['errors'][0]['message']
                print("Error: Code ['{}'], Message ['{}']".format(status_code, error_msg))
                self._storage.log(email_address=self._user.email,
                                  resource='calendarList',
                                  args={'fields': fields,
                                        'pageToken': page_token,
                                        'syncToken': sync_token},
                                  response={'statusCode': status_code, 'errorMsg': error_msg})
                raise RetrySync(status_code)

            self._storage.save_calendars(response, self._user)

            self._storage.log(email_address=self._user.email,
                              resource='calendarList',
                              args={
                                  'fields': fields,
                                  'pageToken': page_token,
                                  'syncToken': sync_token,
                              },
                              response=response)
            sync_detail = {}

            sync_token = None
            if 'nextSyncToken' in response:
                sync_detail[GoogleCalendarListSyncState.KEY_SYNC_TOKEN] = response['nextSyncToken']
                sync_token = response['nextSyncToken']

            page_token = None
            if 'nextPageToken' in response:
                sync_detail[GoogleCalendarListSyncState.KEY_PAGE_TOKEN] = response['nextPageToken']
                page_token = response['nextPageToken']

            sync_object = GoogleCalendarListSyncState(user=self._user)
            sync_object.sync_detail = sync_detail
            sync_object.save()

            if not page_token:
                break
        print(' calendar list fetching function is done')

    def sync_calendar_events(self, calendar: GoogleCalendar):
        sync_state = self._storage.get_last_calendar_sync_state(calendar)
        self._sync_calendar_events_from_state(calendar, sync_state)

    def _sync_calendar_events_from_state(self, calendar: GoogleCalendar, sync_state):
        fields = self.CAL_EVENT_FIELDS
        service = self._connector.get_service()

        page_token = sync_state.get('page_token')
        sync_token = sync_state.get('sync_token')

        while True:
            query_params = {
                'calendarId': calendar.email_address,
                'fields': fields,
                'pageToken': page_token,
                'syncToken': sync_token,
            }

            if sync_state.get(GoogleCalendar.KV_SYNC_STATE_KEY) == GoogleCalendar.KV_SYNC_STATE_VAL_UNINITIALIZED:
                query_params['timeMin'] = self.CAL_EVENT_TIME_MIN

            print(" Fetching a page of events for calendar: {}".format(calendar.email_address))

            try:
                response = service.events().list(**query_params).execute()
            except HttpError as exception:
                print("Exception has occurred!")
                status_code = exception.resp.status
                error_msg = json.loads(exception.content)['error']['errors'][0]['message']
                print("Error: Code ['{}'], Message ['{}']".format(status_code, error_msg))
                return

            self._storage.save_calendar_events(response, calendar.sync_user.client)
            self._storage.log(email_address=calendar.email_address,
                              resource='events',
                              args=query_params,
                              response=response)
            sync_detail = {
                GoogleCalendar.KV_SYNC_STATE_KEY: GoogleCalendar.KV_SYNC_STATE_VAL_INITIALIZED
            }

            sync_token = None
            next_sync_token = response.get('nextSyncToken', None)
            if next_sync_token:
                sync_detail[GoogleCalendar.KEY_SYNC_TOKEN] = next_sync_token
                sync_token = next_sync_token

            page_token = None
            next_page_token = response.get('nextPageToken', None)
            if next_page_token:
                sync_detail[GoogleCalendar.KEY_PAGE_TOKEN] = next_page_token
                page_token = next_page_token

            calendar.sync_detail = sync_detail
            calendar.last_sync_datetime = timezone.now()
            calendar.save()

            if not page_token:
                break

        print(" Calendar Event Fetching is Done for {}".format(calendar.email_address))


class SyncEnvironment:
    """ Sync Environment is specific for a given application client

    @todo Check: What happens when you start a calendar's
    sync with one user and later try to use the same syncToken with
    another user?

    @todo How-to: How can we do sync from scratch when syncToken is broken
    (error code: 410, https://developers.google.com/google-apps/calendar/v3/errors#410_gone).
    Other errors need to be handled, too.
    """

    def __init__(self, app_client: Client):
        self._client = app_client       # type: Client
        self._storage = CalendarStorage(GoogleCalendarApiLogs.log)  # type: CalendarStorage
        self._syncers = {}

    def sync(self):
        for user in self._client.user_set.all():
            syncer = CalendarSyncer(user=user, storage=self._storage)
            syncer.sync_calendar_list()
            self._syncers[user.email] = syncer

        calendars_list = self._storage.get_calendars(self._client)

        for calendar in calendars_list:
            user = calendar.sync_user
            print("Syncing Calendar Events for {}, sync user: {}".format(calendar.email_address, user.email))
            self._syncers[user.email].sync_calendar_events(calendar)
