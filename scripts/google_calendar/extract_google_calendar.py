import logging
import sys
import traceback

import daiquiri
from oauth2client.client import HttpAccessTokenRefreshError

from apps.visualizer.models import Client, CLIENT_STATUS_ACTIVE
from core.sync_engine.google_calendar_syncer import SyncEnvironment

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()


def run():
    logger.info("Script: Extract Google Calendar Script Runs")

    clients = Client.objects.filter(status=CLIENT_STATUS_ACTIVE)

    logger.info("Number of clients to keep in sync: {}".format(len(clients)))

    try:
        for client in clients:
            logger.info(" -> Sync for client id: {} email domain: {}".format(client.id, client.email_domain))
            sync_environment = SyncEnvironment(app_client=client)
            sync_environment.sync()
    except HttpAccessTokenRefreshError as exc:
        logger.info("Log This: Refresh Token is Failed Exception Details: {}".format(exc))
    except Exception as exc:
        logger.info("Log This: Unexpected Exception. Exception Details: {}".format(exc))
        logger.info("-"*60)
        traceback.print_exc(file=sys.stdout)
        logger.info("-"*60)
