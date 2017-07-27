import httplib2
from apiclient import discovery
from visualizer.models import User, Client
from ears.auth_settings import GOOGLE_OAUTH2_KEY, GOOGLE_OAUTH2_SECRET, GOOGLE_TOKEN_URI
from oauth2client import client, tools
import datetime
from google_calendar.models import GoogleCalendarListSync, GoogleCalendar, GoogleCalendarApiLogs
from django.db.models import prefetch_related_objects


class GoogleCalendarConnector:
    """ Setting the Google API connection for the given User
    """

    user = None
    _email_address = None
    _auth_details = None
    _google_service = None

    def __init__(self, user: User):
        oauth2_user = user.get_google_oauth2_user()

        self.user = user
        self._email_address = oauth2_user.uid
        self._auth_details = oauth2_user.extra_data
        self._setup_client()

    def _setup_client(self):
        credentials = client.OAuth2Credentials(
            access_token=self._auth_details['access_token'],
            client_id=GOOGLE_OAUTH2_KEY,
            client_secret=GOOGLE_OAUTH2_SECRET,
            refresh_token=self._auth_details['refresh_token'],
            token_expiry=datetime.datetime.fromtimestamp(
                self._auth_details['auth_time'] + self._auth_details['expires']
            ),
            token_uri=GOOGLE_TOKEN_URI,
            user_agent='my-user-agent/1.0',
        )

        http = credentials.authorize(httplib2.Http())
        self._google_service = discovery.build('calendar', 'v3', http=http)

    def get_user(self):
        return self.user

    def get_service(self):
        return self._google_service


class SyncState:
    STATE_ZERO = 'state_zero'
    state = None
    page_token = None
    sync_token = None

    def __init__(self, state=None, page_token=None, sync_token=None):
        self.state = state
        self.page_token = page_token
        self.sync_token = sync_token

    def is_state_zero(self):
        return self.state == self.STATE_ZERO


class GoogleCalendarStorage:
    _logger = None

    def __init__(self, logger):
        self._logger = logger

    @staticmethod
    def get_last_calendar_list_sync_state(user: User):
        last_sync = GoogleCalendarListSync.get_last_sync(user)
        if last_sync is None:
            return SyncState(SyncState.STATE_ZERO)

        return SyncState(page_token=last_sync.get_page_token(),
                         sync_token=last_sync.get_sync_token())

    @staticmethod
    def get_calendars(app_client: Client):
        return GoogleCalendar.objects.filter(sync_user__client=app_client)

    def log(self, **kwargs):
        self._logger.log(**kwargs)


class GoogleCalendarLogger:
    @staticmethod
    def log(email_address, resource, args, response):
        new_log = GoogleCalendarApiLogs(user_email_address=email_address,
                                        resource=resource,
                                        args=args,
                                        response=response)
        new_log.save()


class GoogleCalendarSyncer:
    CAL_LIST_FIELDS = 'etag,items(accessRole,deleted,description,etag,hidden,id,location,' \
                      'primary,summary,summaryOverride,timeZone),nextPageToken,nextSyncToken'

    _connector = None
    _storage = None

    def __init__(self, user: User, storage: GoogleCalendarStorage):
        self._connector = GoogleCalendarConnector(user=user)
        self._storage = storage

    def sync_calendar_list(self):
        sync_state = self._storage.get_last_calendar_list_sync_state(self._connector.get_user()) # type: SyncState

        if sync_state.is_state_zero():
            self._do_full_calendar_list_sync()
        else:
            self._sync_calendar_list_from_state(sync_state)

    def _do_full_calendar_list_sync(self):
        fields = self.CAL_LIST_FIELDS
        service = self._connector.get_service()

        page_token = None
        sync_token = None

        while True:
            response = service.calendarList().list(fields=fields, pageToken=page_token, syncToken=sync_token).execute()
            self._storage.log(email_address=self._connector.get_user().email,
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
                sync_detail[GoogleCalendarListSync.KEY_SYNC_TOKEN] = response['nextSyncToken']
                sync_token = response['nextSyncToken']

            page_token = None
            if 'nextPageToken' in response:
                sync_detail[GoogleCalendarListSync.KEY_PAGE_TOKEN] = response['nextPageToken']
                page_token = response['nextPageToken']

            sync_object = GoogleCalendarListSync(user=self._connector.get_user(),
                                                 sync_detail=sync_detail)
            sync_object.save()

            if len(response['items']) == 0:
                break

    def _sync_calendar_list_from_state(self, state: SyncState):
        fields = self.CAL_LIST_FIELDS
        pass

    def sync_calendar_meta(self, calendar_id):
        """ calendar_id is the email address associated with the calendar
        """
        pass

    def sync_calendar_events(self, calendar_id):
        """ calendar_id is the email address associated with the calendar
        """
        pass

    def _do_full_calendar_meta_sync(self, calendar_id):
        """
        @todo This may not be necessary, I will check this
        """
        pass

    def _do_full_calendar_event_sync(self, calendar_id):
        pass


class GoogleCalendarSyncEnvironment:
    """ Sync Environment is specific for a given application client

    @todo Check: What happens when you start a calendar's
    sync with one user and later try to use the same syncToken with
    another user?

    @todo How-to: How can we do sync from scratch when syncToken is broken
    (error code: 410, https://developers.google.com/google-apps/calendar/v3/errors#410_gone).
    Other errors need to be handled, too.
    """
    _client = None      # type: Client
    _storage = None     # type: GoogleCalendarStorage
    _syncers = {}       # type: dict

    def __init__(self, app_client: Client):
        self._client = app_client
        self._storage = GoogleCalendarStorage(GoogleCalendarLogger())

    def sync(self):
        for user in self._client.user_set.all():
            syncer = GoogleCalendarSyncer(user=user, storage=self._storage)
            syncer.sync_calendar_list()
            self._syncers[user.email] = syncer

        calendars_list = self._storage.get_calendars(self._client)

        import ipdb
        ipdb.set_trace()

        for calendar in calendars_list:
            user = calendar.sync_user
            self._syncers[user.email].sync_calendar_meta(calendar.email_address)
            self._syncers[user.email].sync_calendar_events(calendar.email_address)
