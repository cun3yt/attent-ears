import os
import requests
from urllib.parse import urlencode


SALESFORCE_CONNECTION = {
    'consumer_key': os.environ.get('SALESFORCE_CONSUMER_KEY'),
    'consumer_secret': os.environ.get('SALESFORCE_CONSUMER_SECRET'),
    'scope': [
        'full',
        'refresh_token',
        'offline_access',
    ],
}


def salesforce_connect_url(redirect_uri):
    query = {
        'client_id': SALESFORCE_CONNECTION['consumer_key'],
        'response_type': 'code',
        'redirect_uri': redirect_uri,
    }

    return 'https://login.salesforce.com/services/oauth2/authorize?{}'.format(urlencode(query))


def salesforce_exchange_for_access_token(authorization_code, redirect_uri):
    return requests.post('https://login.salesforce.com/services/oauth2/token',
                         {
                             'client_id': SALESFORCE_CONNECTION['consumer_key'],
                             'client_secret': SALESFORCE_CONNECTION['consumer_secret'],
                             'redirect_uri': redirect_uri,
                             'grant_type': 'authorization_code',
                             'code': authorization_code,
                         })


def refresh_access_token(data_object):
    print("Refresh Access Token is Called with data_object")
    return requests.post('https://login.salesforce.com/services/oauth2/token',
                         {
                             'client_id': SALESFORCE_CONNECTION['consumer_key'],
                             'client_secret': SALESFORCE_CONNECTION['consumer_secret'],
                             'grant_type': 'refresh_token',
                             'refresh_token': data_object['refresh_token'],
                             'format': 'json',
                         })
