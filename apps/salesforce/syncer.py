from visualizer.models import User
from time import sleep
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceExpiredSession
from tenacity import retry, stop_after_attempt
from apps.salesforce.authentication import refresh_access_token
from apps.salesforce.models import SalesforceAccount
from apps.api_connection.models import ApiConnection
import daiquiri
import logging
from salesforce_bulk import SalesforceBulk
from cached_property import cached_property

import unicodecsv
import sys
import json

daiquiri.setup(level=logging.WARNING)
logger = daiquiri.getLogger()

SALESFORCE_API_VERSION = '40.0'


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

    def update_connection(self, refresh_access_token_response):
        self.connection.data = refresh_access_token_response.json()
        self.connection.save()
        self.set_syncer_with_connection()

    @staticmethod
    def _url_with_no_scheme(url):
        segments = url.split('://')
        return segments[-1:][0]


class RetryNeededError(Exception):
    pass


@retry(stop=stop_after_attempt(3))
def call_with_refresh_token_wrap(func, connection: ApiConnection, *args, **kwargs):
    try:
        # TODO It cannot update the `connection` variable when an error is raised although DB entry is updated
        return func(*args, **kwargs)
    except SalesforceExpiredSession:
        resp = refresh_access_token(connection.data)
        new_connection_data = connection.data.copy()
        new_connection_data.update(resp.json())
        ApiConnection.objects.update_or_create(type='salesforce',
                                               user=connection.user,
                                               defaults={'data': new_connection_data})
        raise RetryNeededError("Retry")
    except Exception:
        raise RetryNeededError("Retry")


def get_salesforce_entity(salesforce, entity_name):
    print("get_contact_metadata is called")
    entity = getattr(salesforce, entity_name)
    return entity


def describe_entity(entity):
    # logger.warning("Meta Data for {}".format(entity.name))
    # for k, v in entity.metadata()['objectDescribe'].items():
    #     print("{}: {}".format(k, v))


    # logger.warning("Entity Description")
    # for k, v in entity.describe().items():
    #     print("{}:".format(k))
    #     print(json.dumps(v, indent=2, sort_keys=True))
    #     print("-----\n-----\n-----\n")

    logger.warning("Fields of {}".format(entity.name))

    vals = [(field['name'], field['type']) for field in entity.describe()['fields']]

    agg = {}
    for (name, t) in vals:
        agg[t] = agg.get(t, [])
        agg[t].append(name)

    print(json.dumps(agg, indent=2, sort_keys=True))
    return None


class EntityExtractor:
    def __init__(self, syncer: Syncer, entity):
        self.syncer = syncer
        self.entity = entity

    def fetch(self):
        job = self.syncer.bulk.create_queryall_job(self.entity.name)
        query = self._build_bulk_query()
        batch = self.syncer.bulk.query(job, query)
        self.syncer.bulk.close_job(job)

        while not self.syncer.bulk.is_batch_done(batch):
            sleep(10)

        return self.syncer.bulk.get_all_results_for_query_batch(batch)

    def save_results(self, result_iterator):
        for result in result_iterator:
            reader = unicodecsv.DictReader(result, encoding='utf-8')
            for row in reader:
                self._save_as_model(row)

    def _save_as_model(self, row):
        logger.warning("SAVE WITH: ")
        print(json.dumps(dict(row), indent=2, sort_keys=True))

        save_fn = self.get_model_class_method(self.get_model_class(), 'save_from_bulk_row')
        save_fn(row, self.syncer.user.client)

    def _build_bulk_query(self):
        select_section = ",".join(self.get_fields_to_fetch())
        return "select {} from {}".format(select_section, self.entity.name)

    @staticmethod
    def get_model_class_method(model_name, method_name):
        klass = getattr(sys.modules[__name__], model_name)
        return getattr(klass, method_name)

    def get_fields_to_fetch(self):
        all_fields = self.entity.describe()['fields']
        return [field['name']
                for field in all_fields
                if field['type'] not in ['address', 'geolocation']]

    def get_model_class(self):
        raise NotImplementedError


class AccountExtractor(EntityExtractor):
    def __init__(self, syncer: Syncer):
        account_entity = call_with_refresh_token_wrap(func=get_salesforce_entity,
                                                      connection=syncer.connection,
                                                      salesforce=syncer.salesforce,
                                                      entity_name='Account',
                                                      )
        super(AccountExtractor, self).__init__(syncer=syncer,
                                               entity=account_entity)

    def get_model_class(self):
        return 'SalesforceAccount'


# Path 1:
#   * Fetch the entity description (field definitions)
#   * Save entity description in DB
#   * Construct query for all fields
#   * Save the result as CSV
#
# Path 2:
#   * Fetch the entity description (field definitions)
#   * Save entity description in DB
#   * Construct query for standard fields only
#   * Save the result as CSV
#   * Construct another query for the desired fields (according to the specifications described by the admin)
#   * Save the result as CSV
#
# Custom Field Mapping:
#   * One entry per client and salesforce entity
#   * A key/value store for custom fields is reserved. Number of custom fields is upper bounded by 15.
#
# Loaded Data:
#   * One table per salesforce entity
#   * Each table will have the standard fields and the 15 custom fields


def ini():
    user = User.objects.get(id=3)
    syncer = Syncer(user)

    account_extractor = AccountExtractor(syncer=syncer)

    result_iterator = call_with_refresh_token_wrap(func=account_extractor.fetch,
                                                   connection=syncer.connection)
    account_extractor.save_results(result_iterator)

    # entities = ['Account', 'AccountHistory', 'Contact', 'ContactHistory', 'Opportunity', 'OpportunityHistory',
    #             'OpportunityFieldHistory', 'Lead', 'Task', 'User', 'UserRole', 'Event']
    #
    # for entity_name in entities:
    #     entity = call_with_refresh_token_wrap(get_salesforce_entity,
    #                                           connection=syncer.connection,
    #                                           entity_name=entity_name,
    #                                           salesforce=syncer.salesforce,
    #                                           )
    #     call_with_refresh_token_wrap(describe_entity,
    #                                  connection=syncer.connection,
    #                                  entity=entity)
