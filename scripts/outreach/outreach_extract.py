from visualizer.models import User
from django.urls import reverse

import traceback
import sys

from apps.outreach.syncer import OutreachSyncer


def full_sync():
    user = User.objects.get(id=1)

    redirect_uri = 'https://cuneyt-dev-attent-ears.herokuapp.com' + reverse('outreach-redirect')
    conn_set = user.api_connections.filter(type='outreach')
    connection = conn_set[0]

    syncer = OutreachSyncer(user.client, redirect_uri, connection)
    syncer.sync_accounts()
    syncer.sync_prospects()
    syncer.sync_users()
    syncer.sync_mailings()
    syncer.sync_calls()


def run():
    try:
        full_sync()
    except Exception as ex:
        print("Log This: Unexpected Exception Exception Details: {}".format(ex))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
