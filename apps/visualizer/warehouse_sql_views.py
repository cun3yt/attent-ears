from django.db import models


class SQLViewGenerator:
    def __init__(self, view_name, client_id):
        self.view_name = view_name
        self.client_id = client_id
        self.select_list = []
        self.from_list = []
        self.where_list = []

    def get_create_view_query(self, is_distinct=True):
        if not self.select_list or not self.from_list or not self.where_list:
            raise Exception("select, from and where lists must be all non empty")

        sql = "CREATE OR REPLACE VIEW {view_name} AS SELECT " \
              + ("DISTINCT " if is_distinct else "")\
              + ",\n".join(self.select_list) \
              + " FROM " + ",\n".join(self.from_list) \
              + " WHERE " + "\nAND ".join(self.where_list)
        return sql.format(view_name=self.view_name, client_id=self.client_id)


class SQLViewGeneratorForContact(SQLViewGenerator):
    seniority_levels = [
        {
            'seniority': 'Other',
            'sql_generated': False,
            'order': 8
        },
        {
            'seniority': 'Null',
            'matching_op': 'is null',
            'order': 7
        },
        {
            'seniority': 'Coordinator',
            'matching_op': "~* '.*coordinator.*'",
            'order': 6
        },
        {
            'seniority': 'Supervisor',
            'matching_op': "~* '.*supervisor.*'",
            'order': 5
        },
        {
            'seniority': 'Manager',
            'matching_op': "~* '.*(manager|mgr).*'",
            'order': 4
        },
        {
            'seniority': 'Director',
            'matching_op': "~* '.*(head|dir).*'",
            'order': 3
        },
        {
            'seniority': 'VP',
            'matching_op': "~* '.*(vp|vice president).*'",
            'order': 2
        },
        {
            'seniority': 'C-level',
            'matching_op': "~* '.*(president|chief|ceo|cfo|cio|cto|chro|cpo|co-founder|coo).*'",
            'order': 1
        },
    ]

    def __init__(self, view_name, client_id):
        SQLViewGenerator.__init__(self, view_name, client_id)

        self.from_list = [
            'attent_calendar ACAL',
            'attent_calendar_event EVENT',
            'attent_calendar_event_has_external_attendee EHA',
            'external_attendee A',
            'salesforce_contact C'
        ]

        self.where_list = [
            'ACAL.client_id = {client_id}',
            "EVENT.event_type::text = 'External'::character varying::text",
            'ACAL.email_address::text = EVENT.organizer_email_address::text',
            'EVENT.id::text = EHA.attent_calendar_event_id::character varying::text',
            'EHA.external_attendee_id::character varying::text = A.id::text',
            'A.email_address::text = C.email::text'
        ]

        seniority_cases = " ".join(["when C.title {matching_op} then '{sen}'"
                                   .format(matching_op=s_level.get('matching_op'),
                                           sen=s_level.get('seniority')) for s_level in self.seniority_levels
                                    if s_level.get('sql_generated', True)])

        self.select_list = [
            "EVENT.id AS meeting_id",
            "timezone('PDT'::character varying::text, timezone('UTC'::character varying::text, EVENT.\"start\")) AS meeting_date",
            "ACAL.first_name",
            "ACAL.title AS role",
            "EVENT.summary",
            "EVENT.description",
            "C.sfdc_id as contact_sfdc_id",
            "C.email",
            "C.name AS contact_name",
            "C.title AS contact_title",
            "case {cases} else 'Other' end AS contact_seniority".format(cases=seniority_cases)
        ]

    @classmethod
    def seniority_to_order(cls):
        return {level['seniority']: level['order'] for level in cls.seniority_levels}


class SQLViewGeneratorForAccount(SQLViewGeneratorForContact):
    regions = [
        {
            'text': "West",
            'matching_op': "ACC.billing_state ~* '(colorado|wyoming|montana|idaho|washington|oregon|utah|nevada|california|alaska|hawaii)'",
            'order': 1
        },
        {
            'text': "Southwest",
            'matching_op': "ACC.billing_state ~* '(texas|oklahoma|new mexico|arizona)'",
            'order': 2
        },
        {
            'text': "Southeast",
            'matching_op': "ACC.billing_state ~* '(arkansas|tennessee|north carolina|south carolina|virginia|louisiana|georgia|florida|alabama|mississippi|kentucky)'",
            'order': 3
        },
        {
            'text': "Midwest",
            'matching_op': "ACC.billing_state ~* '(north dakota|south dakota|illinois|wisconsin|kansas|nebraska|ohio|indiana|michigan|missouri|minnesota|iowa|west virginia)'",
            'order': 4
        },
        {
            'text': "Northeast",
            'matching_op': "ACC.billing_state ~* '(new york|connecticut|district of columbia|new jersey|pennsylvania|maryland|massachusetts|maine|vermont|new hampshire|rhode island)'",
            'order': 5
        },
        {
            'text': "non-US",
            'matching_op': "ACC.billing_country !~* 'united states'",
            'order': 6
        },
        {
            'text': "None",
            'sql_generated': False,
            'order': 7
        },
    ]

    targets = [
        {
            'text': "<51",
            'matching_op': "ACC.number_of_employees < 51",
            'order': 1
        },
        {
            'text': "51-200",
            'matching_op': "51 <= ACC.number_of_employees AND ACC.number_of_employees <= 200",
            'order': 2
        },
        {
            'text': "201-500",
            'matching_op': "201 <= ACC.number_of_employees AND ACC.number_of_employees <= 500",
            'order': 3
        },
        {
            'text': "501-1000",
            'matching_op': "501 <= ACC.number_of_employees AND ACC.number_of_employees <= 1000",
            'order': 4
        },
        {
            'text': ">1000",
            'matching_op': "ACC.number_of_employees > 1000",
            'order': 5
        },
        {
            'text': "Empty",
            'matching_op': "ACC.billing_country !~* 'united states'",
            'order': 6
        },
    ]

    def __init__(self, view_name, client_id):
        SQLViewGeneratorForContact.__init__(self, view_name, client_id)

        self.from_list += ['salesforce_account ACC']
        self.where_list += ['C.account_id::text = ACC.sfdc_id::text']

        regions_cases = " ".join(["when {matching_op} then '{text}'"
                                 .format(matching_op=region.get('matching_op'),
                                         text=region.get('text')) for region in self.regions
                                  if region.get('sql_generated', True)])

        target_cases = " ".join(["when {matching_op} then '{text}'"
                                 .format(matching_op=target.get('matching_op'),
                                         text=target.get('text')) for target in self.targets
                                  if target.get('sql_generated', True)])

        self.select_list += ['ACC.sfdc_id AS account_sfdc_id',
                             'ACC.name AS account_name',
                             'ACC."type" AS account_type',
                             'ACC.number_of_employees',
                             'ACC.created_date',
                             'ACC.billing_city',
                             'ACC.billing_state',
                             'ACC.billing_country',
                             "case {regions_cases} else 'None' end AS account_region".format(
                                 regions_cases=regions_cases),
                             "case {target_cases} else 'Empty' end AS account_target".format(
                                 target_cases=target_cases),
                             ]


class SQLViewGeneratorForOppty(SQLViewGeneratorForAccount):
    def __init__(self, view_name, client_id):
        SQLViewGeneratorForAccount.__init__(self, view_name, client_id)

        self.from_list += ['salesforce_opportunity O']
        self.where_list += ['ACC.sfdc_id::text = O.account_id::text']
        self.select_list += ['O.sfdc_id AS opportunity_sfdc_id',
                             'O.name AS opportunity_name',
                             'O."type" AS opportunity_type',
                             'O.stage_name',
                             'O.amount',
                             'O.close_date']


def create_view_sql_for_event_contact(warehouse_view_name, client_id):
    gen = SQLViewGeneratorForContact(warehouse_view_name, client_id)
    return gen.get_create_view_query()


def create_view_sql_for_event_account(warehouse_view_name, client_id):
    gen = SQLViewGeneratorForAccount(warehouse_view_name, client_id)
    return gen.get_create_view_query()


def create_view_sql_for_event_oppty(warehouse_view_name, client_id):
    gen = SQLViewGeneratorForOppty(warehouse_view_name, client_id)
    return gen.get_create_view_query()


class WarehouseContactMixin(models.Model):
    class Meta:
        abstract = True
    meeting_id = models.TextField(primary_key=True)
    meeting_date = models.DateTimeField()
    first_name = models.TextField()
    role = models.TextField()
    summary = models.TextField()
    description = models.TextField()
    contact_sfdc_id = models.TextField()
    email = models.TextField()
    contact_name = models.TextField()
    contact_title = models.TextField()
    contact_seniority = models.TextField()


class WarehouseAccountMixin(WarehouseContactMixin):
    class Meta:
        abstract = True
    account_sfdc_id = models.TextField()
    account_name = models.TextField()
    account_type = models.TextField(null=True)
    number_of_employees = models.PositiveIntegerField()
    billing_city = models.TextField()
    billing_state = models.TextField()
    billing_country = models.TextField()
    account_region = models.TextField()
    account_target = models.TextField()


def get_model_for_view_contact(view_name):
    class WarehouseMetaClassContact(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += view_name
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class WarehouseViewContact(WarehouseContactMixin):
        __metaclass__ = WarehouseMetaClassContact

        class Meta:
            db_table = view_name
            managed = False

    return WarehouseViewContact


def get_model_for_view_account(view_name):
    class WarehouseMetaClassAccount(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += view_name
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class WarehouseViewAccount(WarehouseAccountMixin):
        __metaclass__ = WarehouseMetaClassAccount

        class Meta:
            db_table = view_name
            managed = False

    return WarehouseViewAccount


def get_model_for_view_oppty(view_name):
    class WarehouseMetaClassOppty(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += view_name
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class WarehouseViewOppty(WarehouseAccountMixin):
        __metaclass__ = WarehouseMetaClassOppty

        class Meta:
            db_table = view_name
            managed = False

        opportunity_sfdc_id = models.TextField()
        opportunity_name = models.TextField()
        opportunity_type = models.TextField()
        stage_name = models.TextField()
        amount = models.PositiveIntegerField()
        close_date = models.DateTimeField()

    return WarehouseViewOppty
