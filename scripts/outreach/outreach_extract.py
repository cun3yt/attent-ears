from visualizer.models import User
from django.urls import reverse
from apps.outreach.syncer import OutreachSyncer
import traceback
import sys

ALLOWED_FNS = ['full_sync', 'partial_sync', 'test_sync']


def _setup_syncer(user: User):
    redirect_uri = 'https://cuneyt-dev-attent-ears.herokuapp.com' + reverse('outreach-redirect')
    conn_set = user.api_connections.filter(type='outreach')
    connection = conn_set[0]
    return OutreachSyncer(user.client, redirect_uri, connection)


def full_sync(syncer: OutreachSyncer):
    print("Running Full Sync")
    syncer.sync_all_resources()


def partial_sync(syncer: OutreachSyncer):
    print("Running Partial Sync")
    syncer.sync_all_resources_partial()


def test_sync(syncer: OutreachSyncer):
    print("Running Test Sync")
    syncer.test()


def _print_usage_and_terminate():
    allowed_functions = '"{}"'.format('", "'.join(ALLOWED_FNS))
    print('usage: <script_name> --script-args <type of extract: {}>'.format(allowed_functions))
    exit()


def run(*args):
    try:
        user = User.objects.get(id=1)
        syncer = _setup_syncer(user)

        if len(args) < 1:
            _print_usage_and_terminate()

        fn_name = args[0]

        if fn_name not in ALLOWED_FNS:
            _print_usage_and_terminate()

        fn = globals()[fn_name]
        fn(syncer)

    except Exception as ex:
        print("Log This: Unexpected Exception Exception Details: {}".format(ex))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
