from visualizer.models import User, Client, CLIENT_STATUS_ACTIVE
from apps.api_connection.models import ApiConnection
from django.urls import reverse
from apps.outreach.syncer import OutreachSyncer
import traceback
import sys
import daiquiri
import logging

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()

ALLOWED_FNS = ['full_sync', 'partial_sync', 'test_sync']


def _setup_syncer(user: User):
    redirect_uri = 'https://cuneyt-dev-attent-ears.herokuapp.com' + reverse('outreach-redirect')
    conn_set = user.api_connections.filter(type='outreach')
    connection = conn_set[0]
    return OutreachSyncer(user.client, redirect_uri, connection)


def full_sync(syncer: OutreachSyncer):
    logger.info("Running Full Sync")
    syncer.sync_all_resources()


def partial_sync(syncer: OutreachSyncer):
    logger.info("Running Partial Sync")
    syncer.sync_all_resources_partial()


def test_sync(syncer: OutreachSyncer):
    logger.info("Running Test Sync")
    syncer.test()


def _print_usage_and_terminate():
    allowed_functions = '"{}"'.format('", "'.join(ALLOWED_FNS))
    print('usage: <script_name> --script-args <type of extract: {}>'.format(allowed_functions))
    exit()


def sync_client(client: Client, fn_name):
    logger.info("Running sync'ing for Client id: {}, domain: {}".format(client.id, client.email_domain))

    client_outreach_connection = ApiConnection.objects.filter(user__client=client, type='outreach') \
        .order_by('id')
    count = client_outreach_connection.count()

    if count == 0:
        logger.warning("There is no Outreach API Connection for Client: {} {}".format(client.id, client.email_domain))
        return

    api_connection = client_outreach_connection[0]
    user = api_connection.user

    if count > 1:
        logger.warning("There are {} Outreach API Connection for Client id: {} domain: {}".format(count,
                                                                                                  client.id,
                                                                                                  client.email_domain
                                                                                                  ))
        logger.warning("Using the first user for the client, id: {} email: {}".format(user.id, user.email))

    user = User.objects.get(id=1)
    syncer = _setup_syncer(user)

    fn = globals()[fn_name]
    fn(syncer)


def run(*args):
    if len(args) < 1:
        _print_usage_and_terminate()

    fn_name = args[0]

    if fn_name not in ALLOWED_FNS:
        _print_usage_and_terminate()

    try:
        logger.info("Script: Outreach Syncer Script Runs")

        clients = Client.objects.filter(status=CLIENT_STATUS_ACTIVE)

        logger.info("Number of clients to keep in sync: {}".format(len(clients)))

        for client in clients:
            sync_client(client, fn_name)

    except Exception as ex:
        logger.error("Log This: Unexpected Exception Exception Details: {}".format(ex))
        logger.error("-"*60)
        traceback.print_exc(file=sys.stdout)
        logger.error("-"*60)
