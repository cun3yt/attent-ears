from core.sync_engine.google_calendar_syncer import SyncEnvironment
from visualizer.models import Client
from oauth2client.client import HttpAccessTokenRefreshError

import sys
import traceback

print("Script: Extract Google Calendar Script Runs")

clients = Client.objects.filter(keep_in_sync=True)

print("Number of clients to keep in sync: {}".format(len(clients)))

try:
    for client in clients:
        print(" -> Sync for client id: {} email domain: {}".format(client.id, client.email_domain))
        sync_environment = SyncEnvironment(app_client=client)
        sync_environment.sync()
except HttpAccessTokenRefreshError as exc:
    print("Log This: Refresh Token is Failed for Client: {}, Exception Details: {}".format(example_client.id, exc))
except Exception as exc:
    print("Log This: Unexpected Exception for Client: {}, Exception Details: {}".format(example_client.id, exc))
    print("-"*60)
    traceback.print_exc(file=sys.stdout)
    print("-"*60)
