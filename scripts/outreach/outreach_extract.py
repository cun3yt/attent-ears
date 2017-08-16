from visualizer.models import User
from django.urls import reverse

import traceback
import sys

from apps.outreach.syncer import OutreachSyncer


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


def _print_usage_and_terminate():
    print('usage: <script_name> --script-args <type of extract: "full" "partial">')
    exit()


def run(*args):
    try:
        user = User.objects.get(id=1)
        syncer = _setup_syncer(user)

        if len(args) < 1:
            _print_usage_and_terminate()

        if args[0] == 'full':
            full_sync(syncer)
        elif args[0] == 'partial':
            partial_sync(syncer)
        else:
            _print_usage_and_terminate()

    except Exception as ex:
        print("Log This: Unexpected Exception Exception Details: {}".format(ex))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
