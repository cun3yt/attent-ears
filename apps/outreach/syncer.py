from urllib.parse import urlencode
import requests
import json
from datetime import datetime
from apps.api_connection.models import ApiConnection
from .models import OutreachAccount, OutreachProspect, OutreachUser, OutreachMailing, OutreachCall
from visualizer.models import Client

OUTREACH_CONNECTION = {
    'client_id': '269ba724e0cd0a12ca3b46439c31bb2f13f19cd9c862b965081846d766fe07fa',
    'client_secret': '4c6b1788a9757363c29f8da2e4cee741f4c85393c545de2cd49c4c68e8ceb405',
    'scope': [
        'profile', 'email', 'read_prospects', 'read_sequences', 'read_accounts', 'read_activities',
        'read_mailings', 'read_mappings', 'read_users', 'read_calls', 'read_call_purposes', 'read_call_dispositions',
        'accounts.all', 'callDispositions.all', 'callPurposes.all', 'calls.all', 'events.all',
        'mailings.all', 'mailboxes.all', 'personas.all', 'prospects.all', 'sequenceStates.all',
        'sequenceSteps.all', 'sequences.all', 'stages.all', 'taskPriorities.all', 'users.all', 'tags.all',
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


class OutreachClient:
    def __init__(self, redirect_uri, api_connection: ApiConnection):
        self.redirect_uri = redirect_uri
        connection = outreach_refresh_access_token_if_needed(api_connection, redirect_uri)
        data = json.loads(connection.data)
        self.headers = {'Authorization': 'Bearer {}'.format(data['access_token'])}
        self.outreach_resource_v1 = 'https://api.outreach.io/1.0/{}'
        self.outreach_resource_v2 = 'https://api.outreach.io/api/v2/{}'

    def get_resource_v2(self, resource, params=None, **kwargs):
        return requests.get(self.outreach_resource_v2.format(resource),
                            params=params, headers=self.headers, **kwargs)


class OutreachApiPageIterator:
    def __init__(self, offset=0, limit=100):
        self.offset = offset
        self.limit = limit

    def get_params(self):
        return {'page[offset]': self.offset, 'page[limit]': self.limit}

    def next(self):
        self.offset += self.limit


class OutreachSyncer:
    def __init__(self, client: Client, redirect_uri, api_connection: ApiConnection):
        self.client = client
        self.outreach_client = OutreachClient(redirect_uri, api_connection)

    def sync_resource(self, resource_name, sync_resource_batch_fn):
        iterator = OutreachApiPageIterator()

        while True:
            print("Fetching {} resource with offset: {} & limit: {}".format(
                resource_name, iterator.offset, iterator.limit))
            res = self.outreach_client.get_resource_v2(resource_name, iterator.get_params())
            res_json = res.json()

            accounts_batch = res_json.get('data', [])
            sync_resource_batch_fn(accounts_batch)

            if not res_json.get('links', {}).get('last', False):
                break

            iterator.next()

    def sync_accounts(self):
        self.sync_resource('accounts', self._sync_accounts_batch)

    def sync_prospects(self):
        self.sync_resource('prospects', self._sync_prospects_batch)

    def sync_users(self):
        self.sync_resource('users', self._sync_users_batch)

    def sync_mailings(self):
        self.sync_resource('mailings', self._sync_mailings_batch)

    def sync_calls(self):
        self.sync_resource('calls', self._sync_calls_batch)

    def _log(self, resource):
        pass

    def test(self):
        return self.outreach_client.get_resource_v2('calls', params={'page[limit]': 2, 'page[offset]': 0})

    @staticmethod
    def _get_attribute(dictionary, field, default_val):
        value = dictionary.get(field, None)
        return value if value is not None else default_val

    def _sync_accounts_batch(self, accounts):
        for account in accounts:
            attributes = account.get('attributes', {})

            outreach_account, _ = OutreachAccount.objects.update_or_create(
                outreach_id=account.get('id'),
                client=self.client,
                defaults={
                    'name': self._get_attribute(attributes, 'name', ''),
                    'natural_name': self._get_attribute(attributes, 'naturalName', ''),
                    'company_type': self._get_attribute(attributes, 'companyType', ''),
                    'domain': self._get_attribute(attributes, 'domain', ''),
                    'website_url': self._get_attribute(attributes, 'websiteUrl', ''),
                    'created_at': self._get_attribute(attributes, 'createdAt', None),
                    'updated_at': self._get_attribute(attributes, 'updatedAt', None),
                }
            )

    def _sync_prospects_batch(self, prospects):
        for prospect in prospects:
            atts = prospect.get('attributes')
            relations = prospect.get('relationships')
            account_id = self._get_attribute(relations.get('account', {}), 'data', {}).get('id')
            owner_id = self._get_attribute(relations.get('owner', {}), 'data', {}).get('id')

            outreach_prospect, _ = OutreachProspect.objects.update_or_create(
                client=self.client,
                outreach_id=prospect.get('id'),
                outreach_account_id=account_id,
                defaults={
                    'outreach_owner_user_id': owner_id,
                    'engaged_score': self._get_attribute(atts, 'engagedScore', None),
                    'first_name': self._get_attribute(atts, 'firstName', ''),
                    'last_name': self._get_attribute(atts, 'lastName', ''),
                    'middle_name': self._get_attribute(atts, 'middleName', ''),
                    'occupation': self._get_attribute(atts, 'occupation', ''),
                    'title': self._get_attribute(atts, 'title', ''),
                    'open_count': self._get_attribute(atts, 'openCount', 0),
                    'reply_count': self._get_attribute(atts, 'replyCount', 0),
                    'click_count': self._get_attribute(atts, 'clickCount', 0),
                    'engaged_at': self._get_attribute(atts, 'engagedAt', None),
                    'opted_out_at': self._get_attribute(atts, 'optedOutAt', None),
                    'created_at': self._get_attribute(atts, 'createdAt', None),
                    'updated_at': self._get_attribute(atts, 'updatedAt', None),
                }
            )

    def _sync_users_batch(self, users):
        for user in users:
            atts = user.get('attributes')
            outreach_user, _ = OutreachUser.objects.update_or_create(
                client=self.client,
                outreach_id=user.get('id'),
                defaults={
                    'email_address': self._get_attribute(atts, 'email', ''),
                    'first_name': self._get_attribute(atts, 'firstName', ''),
                    'last_name': self._get_attribute(atts, 'lastName', ''),
                    'username': self._get_attribute(atts, 'username', ''),
                }
            )

    def _sync_mailings_batch(self, mailings):
        for mailing in mailings:
            atts = mailing.get('attributes')
            relations = mailing.get('relationships')
            prospect_id = self._get_attribute(relations.get('prospect', {}), 'data', {}).get('id')

            outreach_mailing, _ = OutreachMailing.objects.update_or_create(
                client=self.client,
                outreach_id=mailing.get('id'),
                defaults={
                    'outreach_prospect_id': prospect_id,
                    'mailing_type': self._get_attribute(atts, 'mailingType', ''),
                    'mailbox_address': self._get_attribute(atts, 'mailboxAddress', ''),
                    'subject': self._get_attribute(atts, 'subject', None),
                    'body_text': self._get_attribute(atts, 'bodyText', None),
                    'open_count': self._get_attribute(atts, 'openCount', None),
                    'click_count': self._get_attribute(atts, 'clickCount', None),
                    'opened_at': self._get_attribute(atts, 'openedAt', None),
                    'replied_at': self._get_attribute(atts, 'repliedAt', None),
                    'bounced_at': self._get_attribute(atts, 'bouncedAt', None),
                    'marked_as_spam_at': self._get_attribute(atts, 'markedAsSpamAt', None),
                    'scheduled_at': self._get_attribute(atts, 'scheduledAt', None),
                    'created_at': self._get_attribute(atts, 'createdAt', None),
                    'updated_at': self._get_attribute(atts, 'updatedAt', None),
                }
            )

    def _sync_calls_batch(self, calls):
        for call in calls:
            atts = call.get('attributes')
            relations = call.get('relationships')
            prospect_id = self._get_attribute(relations.get('prospect', {}), 'data', {}).get('id')
            user_id = self._get_attribute(relations.get('user', {}), 'data', {}).get('id')

            outreach_call, _ = OutreachCall.objects.update_or_create(
                client=self.client,
                outreach_id=call.get('id'),
                defaults={
                    'outreach_prospect_id': prospect_id,
                    'outreach_user_id': user_id,
                    'outcome': self._get_attribute(atts, 'outcome', None),
                    'answered_at': self._get_attribute(atts, 'answeredAt', None),
                    'completed_at': self._get_attribute(atts, 'completedAt', None),
                    'direction': self._get_attribute(atts, 'direction', ''),
                    'state': self._get_attribute(atts, 'state', ''),
                    'record_url': self._get_attribute(atts, 'recordUrl', None),
                    'created_at': self._get_attribute(atts, 'createdAt', None),
                    'updated_at': self._get_attribute(atts, 'updatedAt', None),
                }
            )
