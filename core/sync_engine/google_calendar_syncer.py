import httplib2
from apiclient import discovery
from visualizer.models import User, Client
from ears.auth_settings import GOOGLE_OAUTH2_KEY, GOOGLE_OAUTH2_SECRET, GOOGLE_TOKEN_URI
from oauth2client import client
import datetime
from google_calendar.models import GoogleCalendarListSyncState, GoogleCalendar, GoogleCalendarApiLogs, \
    GoogleCalendarEvent


class CalendarConnector:  # Google API connection for a given User
    _service = None

    def __init__(self, user: User):
        oauth2_user = user.get_google_oauth2_user()

        self._setup_client(oauth2_user)

    def _setup_client(self, oauth2_user):
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
        self._service = discovery.build('calendar', 'v3', http=http)

    def get_service(self):
        return self._service


class CalendarStorage:
    _logger_fn = None

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

            GoogleCalendar.objects.get_or_create(
                email_address=email_address,
                defaults={
                    'sync_user': sync_user,
                    'is_kept_in_sync': sync_user.client.is_email_address_in_domain(email_address),
                    'timezone': timezone,
                }
            )

    @staticmethod
    def get_last_calendar_sync_state(calendar: GoogleCalendar):
        return calendar.get_last_sync_state()

    # Wrap everything in a transaction to avoid half sync'ed state!

    @staticmethod
    def save_calendar_events(api_response, client: Client):
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
                'created': event_item.get('created'),
                'creator': event_item.get('creator', {}),
                'description': event_item.get('description', ''),
                'end': event_item.get('end', {}),
                'html_link': event_item.get('htmlLink', ''),
                'organizer': event_item.get('organizer', {}),
                'start': event_item.get('start', {}),
                'recurring_event_id': event_item.get('recurring_event_id', ''),
                'summary': event_item.get('summary', ''),
                'updated': event_item.get('updated'),
                'client': client,
            }

            if event_defaults.get('created') is None:
                raise Exception("Empty 'created' field", event_item)
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
                       'attendees,created,creator(displayName,email),description,' \
                       'end,htmlLink,id,organizer(displayName,email),recurringEventId,' \
                       'start,status,summary,updated' \
                       '),' \
                       'nextPageToken,nextSyncToken,timeZone'

    CAL_EVENT_TIME_MIN = '2017-01-01T00:00:00+00:00'

    _user = None
    _connector = None
    _storage = None

    def __init__(self, user: User, storage: CalendarStorage):
        self._user = user
        self._connector = CalendarConnector(user=user)
        self._storage = storage

    def sync_calendar_list(self):
        sync_state = self._storage.get_last_calendar_list_sync_state(self._user)
        self._sync_calendar_list_from_state(sync_state)

    def _sync_calendar_list_from_state(self, sync_state):
        fields = self.CAL_LIST_FIELDS
        service = self._connector.get_service()

        page_token = sync_state.get('page_token')
        sync_token = sync_state.get('sync_token')

        while True:
            response = service.calendarList().list(fields=fields, pageToken=page_token, syncToken=sync_token).execute()
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

    def sync_calendar_events(self, calendar: GoogleCalendar):
        sync_state = self._storage.get_last_calendar_sync_state(calendar)
        self._sync_calendar_events_from_state(calendar, sync_state)

    def _sync_calendar_events_from_state(self, calendar: GoogleCalendar, sync_state):
        fields = self.CAL_EVENT_FIELDS
        service = self._connector.get_service()

        page_token = sync_state.get('page_token')
        sync_token = sync_state.get('sync_token')

        while True:
            query_params={
                'calendarId': calendar.email_address,
                'fields': fields,
                'pageToken': page_token,
                'syncToken': sync_token,
            }

            if sync_state.get(GoogleCalendar.KV_SYNC_STATE_KEY) == GoogleCalendar.KV_SYNC_STATE_VAL_UNINITIALIZED:
                query_params['timeMin'] = self.CAL_EVENT_TIME_MIN

            response = service.events().list(**query_params).execute()

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
            calendar.save()

            if not page_token:
                break


class SyncEnvironment:
    """ Sync Environment is specific for a given application client

    @todo Check: What happens when you start a calendar's
    sync with one user and later try to use the same syncToken with
    another user?

    @todo How-to: How can we do sync from scratch when syncToken is broken
    (error code: 410, https://developers.google.com/google-apps/calendar/v3/errors#410_gone).
    Other errors need to be handled, too.
    """
    _client = None      # type: Client
    _storage = None     # type: CalendarStorage
    _syncers = {}

    def __init__(self, app_client: Client):
        self._client = app_client
        self._storage = CalendarStorage(GoogleCalendarApiLogs.log)

    def sync(self):
        for user in self._client.user_set.all():
            syncer = CalendarSyncer(user=user, storage=self._storage)
            syncer.sync_calendar_list()
            self._syncers[user.email] = syncer

        calendars_list = self._storage.get_calendars(self._client)

        for calendar in calendars_list:
            user = calendar.sync_user
            self._syncers[user.email].sync_calendar_events(calendar)
