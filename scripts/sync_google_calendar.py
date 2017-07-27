from core.sync_engine.google_calendar_syncer import GoogleCalendarSyncEnvironment, GoogleCalendarConnector
from visualizer.models import User, Client
from oauth2client.client import HttpAccessTokenRefreshError

import sys, traceback

example_client = Client.objects.get(id=1)

try:
    sync_environment = GoogleCalendarSyncEnvironment(app_client=example_client)
    sync_environment.sync()
except HttpAccessTokenRefreshError as exc:
    print("Log This: Refresh Token is Failed for Client: {}, Exception Details: {}".format(example_client.id, exc))
except Exception as exc:
    print("Log This: Unexpected Exception for Client: {}, Exception Details: {}".format(example_client.id, exc))
    print("-"*60)
    traceback.print_exc(file=sys.stdout)
    print("-"*60)


def fetch_calendar_list(user: User):
    syncer = GoogleCalendarConnector(user=user)
    cal_service = syncer.get_service()
    fields = 'etag,items(accessRole,deleted,description,etag,hidden,id,location,' \
             'primary,summary,summaryOverride,timeZone),nextPageToken,nextSyncToken'
    calendar_list = cal_service.calendarList().list(pageToken=None, fields=fields, syncToken=None).execute()
    return calendar_list

# example_user = User.objects.get(id=2)
# calendar_list = fetch_calendar_list(example_user)
# print(calendar_list)
