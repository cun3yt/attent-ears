import json
import logging
import sys
import traceback
from random import random
from time import sleep

import daiquiri
import unicodecsv
from salesforce_bulk import SalesforceBulk
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceExpiredSession
from tenacity import retry, stop_after_attempt

from apps.api_connection.models import ApiConnection, ApiSyncStatus
from apps.salesforce.authentication import refresh_access_token
from apps.salesforce.models import *
from apps.visualizer.models import CLIENT_STATUS_ACTIVE

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()

SALESFORCE_API_VERSION = '40.0'
BULK_API_UNSUPPORTED_TYPES = ['address', 'geolocation']


class Syncer:
    def __init__(self, user: User):
        self.user = user
        self.instance_url = None
        self.token = None
        self.bulk = None
        self.salesforce = None

        conn_set = user.api_connections.filter(type='salesforce')

        self.connection = conn_set[0]
        self.set_syncer_with_connection()

    def set_syncer_with_connection(self):
        self.instance_url = self.connection.data['instance_url']
        self.token = self.connection.data['access_token']

        self.bulk = SalesforceBulk(
            host=self.instance_url,
            sessionId=self.token,
            API_version=SALESFORCE_API_VERSION,
        )

        self.salesforce = Salesforce(
            instance=self._url_with_no_scheme(self.instance_url),
            session_id=self.token,
            version=SALESFORCE_API_VERSION,
        )

    @staticmethod
    def _url_with_no_scheme(url):
        segments = url.split('://')
        return segments[-1:][0]


class RetryNeededError(Exception):
    pass


@retry(stop=stop_after_attempt(3))
def call_with_refresh_token_wrap(func, syncer: Syncer, extra_update_fn=None, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except SalesforceExpiredSession:
        connection = syncer.connection
        resp = refresh_access_token(connection.data)
        new_connection_data = connection.data.copy()
        new_connection_data.update(resp.json())
        new_connection, _ = ApiConnection.objects.update_or_create(type='salesforce',
                                                                   user=connection.user,
                                                                   defaults={'data': new_connection_data})
        syncer.connection = new_connection
        syncer.set_syncer_with_connection()

        if extra_update_fn:
            extra_update_fn(syncer=syncer)

        raise RetryNeededError("Retry")
    except Exception:
        raise RetryNeededError("Retry")


def get_salesforce_entity(salesforce, entity_name):
    entity = getattr(salesforce, entity_name)
    return entity


def describe_entity(entity_syncer: Syncer, entity_name):
    salesforce = entity_syncer.salesforce
    entity = get_salesforce_entity(salesforce, entity_name)

    logger.info("Meta Data for {}".format(entity.name))
    for k, v in entity.metadata()['objectDescribe'].items():
        print("{}: {}".format(k, v))

    logger.info("Fields of {}".format(entity.name))
    values = [(field['name'], field['type']) for field in entity.describe()['fields']]

    agg = {}
    for (name, t) in values:
        agg[t] = agg.get(t, [])
        agg[t].append(name)

    print(json.dumps(agg, indent=2, sort_keys=True))
    return None


class EntityExtractor:
    BATCH_LIMIT = 100_000
    OFFSET_CHECK_POINT_PROBABILITY = 0.001   # Interval [0,1)

    def __init__(self, syncer: Syncer):
        self.syncer = None
        self.set_syncer(syncer=syncer)

    def set_syncer(self, syncer: Syncer):
        self.syncer = syncer

    def get_sfdc_entity(self):
        return get_salesforce_entity(salesforce=self.syncer.salesforce,
                                     entity_name=self.get_sfdc_entity_name())

    def get_last_sync_state(self):
        return ApiSyncStatus.objects.filter(api_connection=self.syncer.connection,
                                            resource=self.get_sfdc_entity_name()).latest(field_name='start')

    def generate_api_sync_entry(self):
        offset = None
        comparison_op = '>='

        try:
            previous_status = self.get_last_sync_state()
            offset = previous_status.extra_data['last_offset_check_point']
            comparison_op = '>' if previous_status.extra_data['is_whole_fetch_complete'] \
                else comparison_op
        except ApiSyncStatus.DoesNotExist:
            pass

        return comparison_op,\
               ApiSyncStatus.add_sync_status(api_connection=self.syncer.connection,
                                             resource=self.get_sfdc_entity_name(),
                                             extra_data={
                                                 'batch_size': self.BATCH_LIMIT,
                                                 'start_offset': offset,
                                                 'last_offset_check_point': offset,
                                                 'is_whole_fetch_complete': False,  # reference, no logic around on it
                                             })

    def fetch(self):
        comparison_op, sync_status = self.generate_api_sync_entry()
        offset = sync_status.extra_data.get('start_offset', None)

        pagination_field = self.get_pagination_field()
        where_clause = "{} {} {}".format(pagination_field, comparison_op, offset) if offset else None

        job = self.syncer.bulk.create_queryall_job(self.get_sfdc_entity_name())
        query = self._build_bulk_query(where=where_clause, order_by=pagination_field, limit=self.BATCH_LIMIT)

        logger.debug("QUERY: {}".format(query))

        batch = self.syncer.bulk.query(job, query)
        self.syncer.bulk.close_job(job)

        while not self.syncer.bulk.is_batch_done(batch):
            sleep(6)

        return self.syncer.bulk.get_all_results_for_query_batch(batch), sync_status

    def save_results(self, result_iterator, sync_status: ApiSyncStatus) -> bool:

        logger.info("save results fn is called")

        total_entries_fetched = 0
        pagination_field = self.get_pagination_field()
        last_pagination_item = None

        for result in result_iterator:
            reader = unicodecsv.DictReader(result, encoding='utf-8')

            for row in reader:
                pagination_item = row[pagination_field]
                self._save_as_model(row)

                if random() < self.OFFSET_CHECK_POINT_PROBABILITY:
                    self._push_save_commits()
                    logger.info("UPDATE ON Sync_Status. Last pagination value: {}".format(pagination_item))
                    sync_status.extra_data['last_offset_check_point'] = pagination_item
                    sync_status.save()

                last_pagination_item = pagination_item
                total_entries_fetched += 1

            self._push_save_commits()

        last_pagination_item = last_pagination_item if last_pagination_item \
            else sync_status.extra_data['last_offset_check_point']

        sync_status.extra_data['last_offset_check_point'] = last_pagination_item

        is_whole_fetch_complete = True if total_entries_fetched < self.BATCH_LIMIT else False
        sync_status.extra_data['is_whole_fetch_complete'] = is_whole_fetch_complete
        sync_status.add_end()

        return is_whole_fetch_complete

    @staticmethod
    def get_model_class_method(model_name, method_name):
        klass = getattr(sys.modules[__name__], model_name)
        return getattr(klass, method_name)

    def fetch_and_save_entity_field_description(self):
        all_fields = self._get_all_fetchable_fields()
        standard_fields = [{'name': field['name'], 'type': field['type']} for field in all_fields
                           if not field['name'].endswith("__c")]
        custom_fields = [{'name': field['name'], 'type': field['type']} for field in all_fields
                         if field['name'].endswith("__c")]

        SalesforceEntityDescription.objects.update_or_create(
            client=self.syncer.user.client,
            entity_name=self.get_sfdc_entity_name(),
            defaults={
                'standard_fields': standard_fields,
                'custom_fields': custom_fields,
            })

    def _get_all_fetchable_fields(self):
        entity = self.get_sfdc_entity()
        all_fields = entity.describe()['fields']
        return [{'name': field['name'], 'type': field['type']}
                for field in all_fields
                if field['type'] not in BULK_API_UNSUPPORTED_TYPES]

    def _save_as_model(self, row):
        save_fn = self.get_model_class_method(self.get_model_class(), 'commit_or_delete_from_bulk_row')
        save_fn(row, self.syncer.user.client)

    def _push_save_commits(self):
        push_fn = self.get_model_class_method(self.get_model_class(), 'push_save_commits')
        push_fn()

    def _build_bulk_query(self, where=None, order_by=None, limit=BATCH_LIMIT):
        all_fields = self._get_all_fetchable_fields()
        fetchable_field_names = [field['name'] for field in all_fields]
        select_section = ",".join(fetchable_field_names)
        where_section = "WHERE {}".format(where) if where else ""
        order_section = "ORDER BY {}".format(order_by) if order_by else ""
        limit = "LIMIT {}".format(limit) if limit else ""

        return "select {} from {} {} {} {}".format(select_section,
                                                   self.get_sfdc_entity_name(),
                                                   where_section,
                                                   order_section,
                                                   limit)

    @classmethod
    def get_sfdc_entity_name(cls):
        return cls.get_specs()['entity']

    @classmethod
    def get_model_class(cls):
        return cls.get_specs()['model_class']

    @classmethod
    def get_pagination_field(cls):
        return cls.get_specs().get('pagination_field', 'SystemModstamp')

    @classmethod
    def get_specs(cls):
        raise NotImplemented


class AccountExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Account',
                'model_class': 'SalesforceAccount'}


class AccountHistoryExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'AccountHistory',
                'model_class': 'SalesforceAccountHistory',
                'pagination_field': 'CreatedDate'}


class ContactExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Contact',
                'model_class': 'SalesforceContact'}


class ContactHistoryExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'ContactHistory',
                'model_class': 'SalesforceContactHistory',
                'pagination_field': 'CreatedDate'}


class OpportunityExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Opportunity',
                'model_class': 'SalesforceOpportunity'}


class OpportunityHistoryExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'OpportunityHistory',
                'model_class': 'SalesforceOpportunityHistory'}


class OpportunityFieldHistoryExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'OpportunityFieldHistory',
                'model_class': 'SalesforceOpportunityFieldHistory',
                'pagination_field': 'CreatedDate'}


class LeadExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Lead',
                'model_class': 'SalesforceLead'}


class TaskExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Task',
                'model_class': 'SalesforceTask'}


class UserExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'User',
                'model_class': 'SalesforceUser'}


class UserRoleExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'UserRole',
                'model_class': 'SalesforceUserRole'}


class EventExtractor(EntityExtractor):
    @classmethod
    def get_specs(cls):
        return {'entity': 'Event',
                'model_class': 'SalesforceEvent'}


def sync_client(client: Client):
    logger.info("Running sync'ing for Client id: {}, domain: {}".format(client.id, client.email_domain))

    client_salesforce_connection = ApiConnection.objects.filter(user__client=client, type='salesforce').order_by('id')
    count = client_salesforce_connection.count()

    if count == 0:
        logger.warning("There is no Salesforce API Connection for Client: {} {}".format(client.id, client.email_domain))
        return

    api_connection = client_salesforce_connection[0]
    user = api_connection.user

    if count > 1:
        logger.warning("There are {} Salesforce API Connection for Client id: {} domain: {}".format(count,
                                                                                                    client.id,
                                                                                                    client.email_domain
                                                                                                    ))
        logger.warning("Using the first user for the client, id: {} email: {}".format(user.id, user.email))

    # TODO For Syncer: consider taking client and the primary user for the sync
    # TODO Attent admins and application admins can assign the primary user for the client
    syncer = Syncer(user)

    extractor_classes = [
        'AccountExtractor',
        'ContactExtractor',
        'OpportunityExtractor',
        'LeadExtractor',
        'TaskExtractor',
        'UserExtractor',
        'UserRoleExtractor',
        'EventExtractor',

        # 'AccountHistoryExtractor',
        # 'ContactHistoryExtractor',
        # 'OpportunityHistoryExtractor',
        # 'OpportunityFieldHistoryExtractor',
    ]

    for extractor_class_name in extractor_classes:
        try:
            logger.info("Running for {}".format(extractor_class_name))

            extractor_class = getattr(sys.modules[__name__], extractor_class_name)
            extractor = extractor_class(syncer=syncer)
            call_with_refresh_token_wrap(func=extractor.fetch_and_save_entity_field_description,
                                         syncer=syncer,
                                         extra_update_fn=extractor.set_syncer)

            while True:
                logger.info("Fetching a Batch with {}".format(extractor_class_name))

                result_iterator, sync_status = call_with_refresh_token_wrap(func=extractor.fetch,
                                                                            syncer=syncer,
                                                                            extra_update_fn=extractor.set_syncer)

                is_finalized = extractor.save_results(result_iterator, sync_status)

                if is_finalized:
                    break
        except Exception as exc:
            logger.error("Log This: Unexpected Exception, Details: {}".format(exc))
            logger.error("-"*60)
            traceback.print_exc(file=sys.stdout)
            logger.error("-"*60)


def ini():
    logger.info("Script: Salesforce Syncer Script Runs")

    clients = Client.objects.filter(status=CLIENT_STATUS_ACTIVE)

    logger.info("Number of clients to keep in sync: {}".format(len(clients)))

    for client in clients:
        sync_client(client)
