from core.sync_engine.google_calendar_syncer import SyncEnvironment
from visualizer.models import Client, CLIENT_STATUS_ACTIVE
from oauth2client.client import HttpAccessTokenRefreshError

import sys
import traceback


def run():
    print("Script: Extract Google Calendar Script Runs")

    clients = Client.objects.filter(status=CLIENT_STATUS_ACTIVE)

    print("Number of clients to keep in sync: {}".format(len(clients)))

    try:
        for client in clients:
            print(" -> Sync for client id: {} email domain: {}".format(client.id, client.email_domain))
            sync_environment = SyncEnvironment(app_client=client)
            sync_environment.sync()
    except HttpAccessTokenRefreshError as exc:
        print("Log This: Refresh Token is Failed Exception Details: {}".format(exc))
    except Exception as exc:
        print("Log This: Unexpected Exception. Exception Details: {}".format(exc))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
