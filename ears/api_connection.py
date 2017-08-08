from urllib.parse import urlencode
import requests

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
