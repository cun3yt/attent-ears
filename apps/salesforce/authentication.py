from urllib.parse import urlencode
import requests


SALESFORCE_CONNECTION = {
    'consumer_key': '3MVG9i1HRpGLXp.oum9utXoxpin3yeYR32TKUm0hdDtB_gcVZbnP7l2H8_QBVHriPBY2jKhWONOGbmIQaGlOz',
    'consumer_secret': '3745620791270244934',
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
