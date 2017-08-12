from urllib.parse import urlencode
import requests
import json
from datetime import datetime
from apps.api_connection.models import ApiConnection

OUTREACH_CONNECTION = {
    'client_id': '269ba724e0cd0a12ca3b46439c31bb2f13f19cd9c862b965081846d766fe07fa',
    'client_secret': '4c6b1788a9757363c29f8da2e4cee741f4c85393c545de2cd49c4c68e8ceb405',
    'scope': [
        'profile',
        'email',
        'read_prospects',
        'read_sequences',
        'read_accounts',
        'read_activities',
        'read_mailings',
        'read_mappings',
        'read_users',
        'read_calls',
        'read_call_purposes',
        'read_call_dispositions',
        'profile',
        'email',
        'create_prospects',
        'read_prospects',
        'update_prospects',
        'read_sequences',
        'update_sequences',
        'read_tags',
        'read_accounts',
        'create_accounts',
        'read_activities',
        'read_mailings',
        'read_mappings',
        'read_plugins',
        'read_users',
        'create_calls',
        'read_calls',
        'read_call_purposes',
        'read_call_dispositions',
    ],
}


def outreach_connect_url(redirect_uri):
    scope_str = ' '.join(OUTREACH_CONNECTION['scope'])
    query = {
        'client_id': OUTREACH_CONNECTION['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope_str,
    }
    return 'https://api.outreach.io/oauth/authorize?{}'.format(urlencode(query))


def outreach_exchange_for_access_token(authorization_code, redirect_uri):
    return requests.post('https://api.outreach.io/oauth/token',
                         {
                             'client_id': OUTREACH_CONNECTION['client_id'],
                             'client_secret': OUTREACH_CONNECTION['client_secret'],
                             'redirect_uri': redirect_uri,
                             'grant_type': 'authorization_code',
                             'code': authorization_code,
                         })


def _is_outreach_token_about_to_expire(user_api_connection: ApiConnection):
    precision_in_seconds = 15

    data = json.loads(user_api_connection.data)
    current_ts = int(datetime.timestamp(datetime.now()))
    return (data['expires_in'] + data['created_at'] + precision_in_seconds) <= current_ts


def outreach_refresh_access_token_if_needed(user_api_connection: ApiConnection, redirect_uri):
    if user_api_connection.type != 'outreach':
        raise Exception("ApiConnection object is not of type 'outreach'")

    if not _is_outreach_token_about_to_expire(user_api_connection):
        return user_api_connection

    data = json.loads(user_api_connection.data)
    resp = requests.post('https://api.outreach.io/oauth/token',
                         {
                             'client_id': OUTREACH_CONNECTION['client_id'],
                             'client_secret': OUTREACH_CONNECTION['client_secret'],
                             'redirect_uri': redirect_uri,
                             'grant_type': 'refresh_token',
                             'refresh_token': data['refresh_token'],
                         })

    if resp.status_code != 200:
        raise Exception("Refresh Token Failure for Outreach with ApiConnection ID: {} - Response: {}"
                        .format(user_api_connection.id, resp.text))

    user_api_connection.data = resp.text
    user_api_connection.save()
    return user_api_connection
