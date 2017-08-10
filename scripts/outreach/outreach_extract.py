from visualizer.models import User
from ears.api_connection import outreach_refresh_access_token_if_needed
from django.urls import reverse

import traceback
import sys
import json
import requests


user = User.objects.get(id=3)
conn_set = user.api_connections.filter(type='outreach')
connection = conn_set[0]

try:
    import ipdb
    ipdb.set_trace()

    redirect_uri = 'https://cuneyt-dev-attent-ears.herokuapp.com' + reverse('outreach-redirect')
    con = outreach_refresh_access_token_if_needed(connection, redirect_uri)
    data = json.loads(con.data)
    headers = {'Authorization': 'Bearer {}'.format(data['access_token'])}
    outreach_resource = 'https://api.outreach.io/1.0/{}'

    response = requests.get(outreach_resource.format('accounts'), headers=headers)
    response = requests.get(outreach_resource.format('activities?filter[prospect/id]=51628'), headers=headers)
    response = requests.get(outreach_resource.format('calls'), headers=headers)
    response = requests.get(outreach_resource.format('call_dispositions'), headers=headers)
    response = requests.get(outreach_resource.format('call_purposes'), headers=headers)
    response = requests.get(outreach_resource.format('info'), headers=headers)
    response = requests.get(outreach_resource.format('mailings/65349'), headers=headers)
    response = requests.get(outreach_resource.format('plugins'), headers=headers)           # authentication needed
    # ^^^^ the documentation resource wrong? http://bit.ly/2urablf ^^^^
    response = requests.get(outreach_resource.format('prospects?page[size]=10'), headers=headers)
    response = requests.get(outreach_resource.format('sequences?page[size]=150'), headers=headers)
    response = requests.get(outreach_resource.format('sequences?id=288'), headers=headers)
    response = requests.get(outreach_resource.format('users'), headers=headers)

except Exception as ex:
    print("Log This: Unexpected Exception Exception Details: {}".format(ex))
    print("-"*60)
    traceback.print_exc(file=sys.stdout)
    print("-"*60)
