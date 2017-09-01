from visualizer.models import User
from time import sleep
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceExpiredSession
from tenacity import retry, stop_after_attempt
from apps.salesforce.authentication import refresh_access_token
from apps.api_connection.models import ApiConnection
import daiquiri
import logging
from salesforce_bulk import SalesforceBulk

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
    logger.warning("Meta Data for {}".format(entity.name))
    for k, v in entity.metadata()['objectDescribe'].items():
        print("{}: {}".format(k, v))

    logger.warning("Fields of {}".format(entity.name))
    for field in entity.describe()['fields']:
        print("{}".format(field['name']))

    return None


class EntityExtractor:
    def __init__(self, syncer: Syncer, entity):
        self.syncer = syncer
        self.entity = entity

    def fetch_and_save(self):
        import ipdb
        ipdb.set_trace()

        job = self.syncer.bulk.create_queryall_job(self.get_entity_name())
        query = self._build_bulk_query()
        batch = self.syncer.bulk.query(job, query)
        self.syncer.bulk.close_job(job)

        while not self.syncer.bulk.is_batch_done(job, batch):
            sleep(10)

        for result in self.syncer.bulk.get_all_results_from_batch(batch):
            for row in result:
                self._save_as_model(row)

    def _save_as_model(self, row):
        logger.warning("Needs to be saved as {} with user {}: {}".format(
            self.get_model_class(), self.syncer.user.id, row))

    def _build_bulk_query(self):
        select_section = ",".join(self.get_fields_to_fetch())
        return "select {} from {}".format(select_section, self.get_entity_name())

    def get_fields_to_fetch(self):
        raise NotImplementedError

    def get_entity_name(self):
        raise NotImplementedError

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

    def get_fields_to_fetch(self):
        return ['Id', 'Name', 'OwnerId', 'AnnualRevenue',
                'BillingAddress', 'NumberOfEmployees',
                'Industry', 'Type', 'Website',
                'Site', 'AccountSource', 'CreatedBy',
                'Jigsaw', 'Description', 'Fax', 'LastModifiedBy',
                'Ownership', 'Parent', 'Phone', 'Rating',
                'ShippingAddress', 'Sic', 'SicDesc', 'TickerSymbol']

    def get_entity_name(self):
        return 'Account'

    def get_model_class(self):
        return 'SalesforceAccount'


def ini():
    user = User.objects.get(id=3)
    syncer = Syncer(user)

    account_extractor = AccountExtractor(syncer=syncer)

    import ipdb
    ipdb.set_trace()

    call_with_refresh_token_wrap(func=account_extractor.fetch_and_save,
                                 connection=syncer.connection)



    # entity = call_with_refresh_token_wrap(get_salesforce_entity,
    #                                       connection=self.syncer.connection,
    #                                       entity_name='Account',
    #                                       salesforce=self.syncer.salesforce,
    #                                       )
    #
    # call_with_refresh_token_wrap(describe_entity,
    #                              connection=self.syncer.connection,
    #                              entity=entity)

    # for k, v in entity.metadata()['objectDescribe'].items():
    #     print("{}: {}".format(k, v))

    # descr = syncer.salesforce.Contact.describe()
    # desc['name']
    # desc['label']
    # desc['fields'][0]['name']
    # fields = desc['fields']
    # [field['name'] for field in fields]
    # print(description)

    # job = syncer.bulk.create_query_job('Contact')
    # batch = syncer.bulk.query(job, "select Id, LastName from Contact")
    #
    # syncer.bulk.close_job(job)
    # while not syncer.bulk.is_batch_done(job, batch):
    #     sleep(10)
    #
    # for result in syncer.bulk.get_all_results_for_batch(batch):
    #     for row in result:
    #         print(row)
    # print('----')
