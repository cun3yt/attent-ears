import json
import math
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from tenacity import retry, wait_exponential, stop_after_attempt

from apps.api_connection.models import ApiConnection, ApiSyncStatus, NoApiSyncStatusError
from apps.visualizer.models import Client
from .models import OutreachAccount, OutreachProspect, OutreachProspectV1, OutreachUser, OutreachMailing, OutreachCall

from ears.env_variables import OUTREACH_CLIENT_ID, OUTREACH_CLIENT_SECRET

OUTREACH_CONNECTION = {
    'client_id': OUTREACH_CLIENT_ID,
    'client_secret': OUTREACH_CLIENT_SECRET,
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
        self.outreach_resource_v1 = 'https://api.outreach.io/1.0/{}'
        self.outreach_resource_v2 = 'https://api.outreach.io/api/v2/{}'
        self.api_connection = api_connection
        self.headers = {}
        self._refresh_token_if_necessary_and_update_header()

    def _refresh_token_if_necessary_and_update_header(self):
        connection = outreach_refresh_access_token_if_needed(self.api_connection, self.redirect_uri)
        data = json.loads(connection.data)
        self.headers = {'Authorization': 'Bearer {}'.format(data['access_token'])}

    def get_resource_v1(self, resource, params=None, **kwargs):
        self._refresh_token_if_necessary_and_update_header()
        return requests.get(self.outreach_resource_v1.format(resource),
                            params=params, headers=self.headers, **kwargs)

    def get_resource_v2(self, resource, params=None, **kwargs):
        self._refresh_token_if_necessary_and_update_header()
        return requests.get(self.outreach_resource_v2.format(resource),
                            params=params, headers=self.headers, **kwargs)


class OutreachApiPageIterator:      # Outreach API doesn't allow offset > 10K
    def __init__(self, offset=0, limit=100, time_limit=None):
        self.offset = offset
        self.limit = limit
        self.time_limit = time_limit

    def get_params(self):
        raise Exception("Not Implemented")

    def next(self, alternative_offset=0):
        self.offset = max(self.offset + self.limit, alternative_offset)


class OutreachApiRangeIterator(OutreachApiPageIterator):
    def get_params(self):
        lower_limit = self.offset
        upper_limit = '99999999'
        params = {'filter[id]': '{}..{}'.format(lower_limit, upper_limit), 'page[limit]': self.limit}
        if self.time_limit is not None:
            params['filter[updatedAt]'] = "{}..inf".format(self.time_limit)
        return params

    def is_end(self, total_num_entries, num_in_batch):
        return not total_num_entries


class OutreachApiV1PageIterator(OutreachApiPageIterator):
    def get_params(self):
        page_size = self.limit
        page_number = math.ceil((self.offset+1)/page_size)
        params = {'page[size]': page_size, 'page[number]': page_number}
        if self.time_limit is not None:
            params['filter[metadata/updated/after]'] = "{}".format(self.time_limit)
        return params

    def is_end(self, total):
        return total < self.offset


class OutreachApiTimeLimitIterator(OutreachApiPageIterator):
    def get_params(self):
        return {
            'filter[updatedAt]': '{}..inf'.format(self.time_limit),
            'page[limit]': self.limit,
            'page[offset]': self.offset,
        }

    def next(self, alternative_offset=0):
        self.offset = self.offset + self.limit

    def is_end(self, total_num_entries, num_in_batch):
        return not num_in_batch


class OutreachSyncer:
    def __init__(self, client: Client, redirect_uri, api_connection: ApiConnection):
        self.client = client
        self.api_connection = api_connection
        self.outreach_client = OutreachClient(redirect_uri, self.api_connection)

    def test(self):
        import ipdb
        ipdb.set_trace()

        iterator = OutreachApiV1PageIterator(time_limit='2017-08-20')
        res_json = self._fetch_resource_from_outreach('v1', 'prospects', iterator)
        print(res_json['meta']['results']['total'])

        iterator = OutreachApiV1PageIterator(time_limit='2017-08-20T00:0013:00:30+00')
        res_json = self._fetch_resource_from_outreach('v1', 'prospects', iterator)
        print(res_json['meta']['results']['total'])

        iterator = OutreachApiV1PageIterator(time_limit='2017-08-20T23:59')
        res_json = self._fetch_resource_from_outreach('v1', 'prospects', iterator)
        print(res_json['meta']['results']['total'])

        # iterator = OutreachApiRangeIterator(offset=0)
        #
        # res_json = self._fetch_resource_from_outreach('v2', 'prospects', iterator)
        # print(self._fetch_resource_from_outreach.retry.statistics)

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(10))
    def _fetch_resource_from_outreach(self, api_version, resource_name, iterator):
        possible_api_versions = ['v1', 'v2']

        if api_version not in possible_api_versions:
            raise Exception("Wrong API version is provided, possible values: {}".format(
                ', '.join(possible_api_versions)))

        print("Fetching {} resource from API {} with offset: {}, limit: {} & time_limit: {}".format(
            resource_name, api_version, iterator.offset, iterator.limit, iterator.time_limit))

        fetch_fn = self.outreach_client.get_resource_v1 if api_version == 'v1' else self.outreach_client.get_resource_v2

        res = fetch_fn(resource_name, iterator.get_params())
        try:
            res_json = res.json()
        except json.decoder.JSONDecodeError as exc:
            print(" Error: json.decoder.JSONDecodeError", exc.msg)
            print(res.status_code)
            print(res.text)
            raise Exception("Retry Please")

        return res_json

    def sync_resource(self, resource_name, sync_resource_batch_fn, offset, time_limit=None):
        if time_limit:
            iterator = OutreachApiTimeLimitIterator(offset=offset, time_limit=time_limit)
        else:
            iterator = OutreachApiRangeIterator(offset=offset)

        while True:
            res_json = self._fetch_resource_from_outreach('v2', resource_name, iterator)
            print(" >> Stats: {}".format(self._fetch_resource_from_outreach.retry.statistics))

            resource_instances = res_json.get('data', [])
            total_num_entries = res_json.get('metadata', {}).get('count')
            batch_num_entries = len(resource_instances)

            print(" Total # of Entries: {}, In this batch: {}".format(total_num_entries, batch_num_entries))

            if total_num_entries is None:
                print("Total number is None, printing the content of API response: {}".format(res_json))

            if iterator.is_end(total_num_entries=total_num_entries, num_in_batch=batch_num_entries):
                break

            sync_resource_batch_fn(resource_instances, covering_api_offset=iterator.offset)

            try:
                max_id = resource_instances[-1].get('id', 0)
            except IndexError:
                max_id = -1

            iterator.next(max_id + 1)

    def sync_resource_api_v1(self, resource_name, sync_resources_batch_fn, offset, time_limit=None):
        time_lower_limit = (time_limit - timedelta(days=1)).date()  # Due to API limitation on timezone, extended time

        iterator = OutreachApiV1PageIterator(offset=offset, limit=50, time_limit=time_lower_limit)

        while True:
            res_json = self._fetch_resource_from_outreach('v1', resource_name, iterator)
            print(" >> Stats: {}".format(self._fetch_resource_from_outreach.retry.statistics))

            resource_instances = res_json.get('data', [])
            total_num_entries = res_json.get('meta', {}).get('results', {}).get('total')

            print(" Total # Entries: {}, in the batch: {}".format(total_num_entries, len(resource_instances)))

            if iterator.is_end(total_num_entries):
                break

            sync_resources_batch_fn(resource_instances)
            iterator.next()

    def sync_accounts(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachAccount.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource('accounts', self._sync_accounts_batch, offset, time_limit)
        sync_status.add_end()

    def sync_prospects(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachProspect.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource('prospects', self._sync_prospects_batch, offset, time_limit)
        sync_status.add_end()

    def sync_prospects_api_v1(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachProspectV1.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource_api_v1('prospects', self._sync_prospects_v1_batch, offset, time_limit)
        sync_status.add_end()

    def sync_users(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachUser.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource('users', self._sync_users_batch, offset, time_limit)
        sync_status.add_end()

    def sync_mailings(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachMailing.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource('mailings', self._sync_mailings_batch, offset, time_limit)
        sync_status.add_end()

    def sync_calls(self, offset=0, time_limit=None):
        sync_status = ApiSyncStatus.add_sync_status(api_connection=self.api_connection,
                                                    resource=OutreachCall.RESOURCE_NAME,
                                                    extra_data={'start_offset': offset})
        self.sync_resource('calls', self._sync_calls_batch, offset, time_limit)
        sync_status.add_end()

    def sync_all_resources(self):
        """
        Full Sync For All Resources
        """
        self.sync_accounts()
        self.sync_prospects()
        self.sync_prospects_api_v1()
        self.sync_users()
        self.sync_calls()
        self.sync_mailings()

    def sync_all_resources_partial(self):
        """
        * Sync'ing only the last items based on offset of the record created recently, e.g. last one month
        * Sync'ing items based on some criteria, e.g. update time > (now() - 1 month)
        """
        self.sync_resource_partial(OutreachAccount, self.sync_accounts)
        self.sync_resource_partial(OutreachProspect, self.sync_prospects)
        self.sync_resource_partial(OutreachProspectV1, self.sync_prospects_api_v1)
        self.sync_resource_partial(OutreachUser, self.sync_users)
        self.sync_resource_partial(OutreachMailing, self.sync_mailings)
        self.sync_resource_partial(OutreachCall, self.sync_calls)

    def sync_resource_partial(self, model, sync_fn):
        try:
            sync_status = ApiSyncStatus.get_last_completed_sync(api_connection=self.api_connection,
                                                                resource=model.RESOURCE_NAME)
            sync_fn(offset=0, time_limit=sync_status.start)

        except NoApiSyncStatusError:
            print("Cannot do partial sync, consider doing full sync!")

    @staticmethod
    def _get_attribute(dictionary, field, default_val):
        value = dictionary.get(field, None)
        return value if value is not None else default_val

    def _sync_accounts_batch(self, accounts, covering_api_offset):
        for account in accounts:
            attributes = account.get('attributes', {})

            outreach_account, _ = OutreachAccount.objects.update_or_create(
                outreach_id=account.get('id'),
                client=self.client,
                defaults={
                    'name': self._get_attribute(attributes, 'name', '')[0:100],
                    'natural_name': self._get_attribute(attributes, 'naturalName', '')[0:100],
                    'company_type': self._get_attribute(attributes, 'companyType', '')[0:20],
                    'domain': self._get_attribute(attributes, 'domain', '')[0:255],
                    'website_url': self._get_attribute(attributes, 'websiteUrl', '')[0:255],
                    'created_at': self._get_attribute(attributes, 'createdAt', None),
                    'updated_at': self._get_attribute(attributes, 'updatedAt', None),
                    'covering_api_offset': covering_api_offset,
                }
            )

    def _sync_prospects_batch(self, prospects, covering_api_offset):
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
                    'first_name': self._get_attribute(atts, 'firstName', '')[0:20],
                    'last_name': self._get_attribute(atts, 'lastName', '')[0:20],
                    'middle_name': self._get_attribute(atts, 'middleName', '')[0:20],
                    'occupation': self._get_attribute(atts, 'occupation', '')[0:50],
                    'title': self._get_attribute(atts, 'title', '')[0:100],
                    'open_count': self._get_attribute(atts, 'openCount', 0),
                    'reply_count': self._get_attribute(atts, 'replyCount', 0),
                    'click_count': self._get_attribute(atts, 'clickCount', 0),
                    'engaged_at': self._get_attribute(atts, 'engagedAt', None),
                    'opted_out_at': self._get_attribute(atts, 'optedOutAt', None),
                    'created_at': self._get_attribute(atts, 'createdAt', None),
                    'updated_at': self._get_attribute(atts, 'updatedAt', None),
                    'covering_api_offset': covering_api_offset,
                }
            )

    def _sync_prospects_v1_batch(self, prospects):
        for prospect in prospects:
            outreach_id = prospect.get('id')
            atts = prospect.get('attributes', {})
            contact = atts.get('contact', {})
            phone_list = contact.get('phone', {})

            OutreachProspectV1.objects.update_or_create(
                client=self.client,
                outreach_id=outreach_id,
                defaults={
                    'email_address': self._get_attribute(contact, 'email', '')[0:255],
                    'phone_number_personal': self._get_attribute(phone_list, 'personal', '')[0:20],
                    'phone_number_work': self._get_attribute(phone_list, 'work', '')[0:20],
                }
            )

    def _sync_users_batch(self, users, covering_api_offset):
        for user in users:
            atts = user.get('attributes')
            outreach_user, _ = OutreachUser.objects.update_or_create(
                client=self.client,
                outreach_id=user.get('id'),
                defaults={
                    'email_address': self._get_attribute(atts, 'email', ''),
                    'first_name': self._get_attribute(atts, 'firstName', '')[0:30],
                    'last_name': self._get_attribute(atts, 'lastName', '')[0:30],
                    'username': self._get_attribute(atts, 'username', '')[0:30],
                    'covering_api_offset': covering_api_offset,
                }
            )

    def _sync_mailings_batch(self, mailings, covering_api_offset):
        for mailing in mailings:
            atts = mailing.get('attributes')
            relations = mailing.get('relationships')
            prospect_id = self._get_attribute(relations.get('prospect', {}), 'data', {}).get('id')

            outreach_mailing, _ = OutreachMailing.objects.update_or_create(
                client=self.client,
                outreach_id=mailing.get('id'),
                defaults={
                    'outreach_prospect_id': prospect_id,
                    'mailing_type': self._get_attribute(atts, 'mailingType', '')[0:30],
                    'mailbox_address': self._get_attribute(atts, 'mailboxAddress', '')[0:255],
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
                    'covering_api_offset': covering_api_offset,
                }
            )

    def _sync_calls_batch(self, calls, covering_api_offset):
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
                    'direction': self._get_attribute(atts, 'direction', '')[0:20],
                    'state': self._get_attribute(atts, 'state', '')[0:20],
                    'record_url': self._get_attribute(atts, 'recordUrl', None),
                    'created_at': self._get_attribute(atts, 'createdAt', None),
                    'updated_at': self._get_attribute(atts, 'updatedAt', None),
                    'covering_api_offset': covering_api_offset,
                }
            )
