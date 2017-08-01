from core.sync_engine.google_calendar_syncer import SyncEnvironment
from visualizer.models import Client
from oauth2client.client import HttpAccessTokenRefreshError

import sys
import traceback

example_client = Client.objects.get(id=1)       # @todo Get this from args

try:
    sync_environment = SyncEnvironment(app_client=example_client)
    sync_environment.sync()
except HttpAccessTokenRefreshError as exc:
    print("Log This: Refresh Token is Failed for Client: {}, Exception Details: {}".format(example_client.id, exc))
except Exception as exc:
    print("Log This: Unexpected Exception for Client: {}, Exception Details: {}".format(example_client.id, exc))
    print("-"*60)
    traceback.print_exc(file=sys.stdout)
    print("-"*60)
