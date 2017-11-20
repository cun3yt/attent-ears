from django.db import models


def create_view_sql_for_event_contact(warehouse_view_name, client_id):
    return """CREATE OR REPLACE VIEW {view_name} AS
    SELECT DISTINCT attent_calendar_event.id AS meeting_id,
      timezone('PDT'::character varying::text, timezone('UTC'::character varying::text, attent_calendar_event."start")) AS meeting_date,
      attent_calendar.first_name,
      attent_calendar.title AS role,
      attent_calendar_event.summary,
      attent_calendar_event.description,
      salesforce_contact.sfdc_id as contact_sfdc_id,
      salesforce_contact.email,
      salesforce_contact.name AS contact_name,
      salesforce_contact.title AS contact_title
    FROM
      attent_calendar,
      attent_calendar_event,
      attent_calendar_event_has_external_attendee,
      external_attendee,
      salesforce_contact
    WHERE
      attent_calendar.client_id = {client_id}
      AND attent_calendar_event.event_type::text = 'External'::character varying::text
      AND attent_calendar.email_address::text = attent_calendar_event.organizer_email_address::text
      AND attent_calendar_event.id::text = attent_calendar_event_has_external_attendee.attent_calendar_event_id::character varying::text
      AND attent_calendar_event_has_external_attendee.external_attendee_id::character varying::text = external_attendee.id::text
      AND external_attendee.email_address::text = salesforce_contact.email::text
      """.format(view_name=warehouse_view_name, client_id=client_id)


def create_view_sql_for_event_contact_account_oppty(warehouse_view_name, client_id):
    return """CREATE OR REPLACE VIEW {} AS
    SELECT DISTINCT attent_calendar_event.id AS meeting_id,
      timezone('PDT'::character varying::text, timezone('UTC'::character varying::text, attent_calendar_event."start")) AS meeting_date,
      attent_calendar.first_name,
      attent_calendar.title AS role,
      attent_calendar_event.summary,
      attent_calendar_event.description,
      salesforce_contact.sfdc_id as contact_sfdc_id,
      salesforce_contact.email,
      salesforce_contact.name AS contact_name,
      salesforce_contact.title AS contact_title,
      salesforce_account.sfdc_id AS account_sfdc_id,
      salesforce_account.name AS account_name,
      salesforce_account."type" AS account_type,
      salesforce_account.number_of_employees,
      salesforce_account.created_date,
      salesforce_account.billing_city,
      salesforce_account.billing_state,
      salesforce_account.billing_country,
      salesforce_opportunity.sfdc_id AS opportunity_sfdc_id,
      salesforce_opportunity.name AS opportunity_name,
      salesforce_opportunity."type" AS opportunity_type,
      salesforce_opportunity.stage_name,
      salesforce_opportunity.amount,
      salesforce_opportunity.close_date
    FROM
      attent_calendar,
      attent_calendar_event,
      attent_calendar_event_has_external_attendee,
      external_attendee,
      salesforce_contact,
      salesforce_account,
      salesforce_opportunity
    WHERE
      attent_calendar.client_id = {}
      AND attent_calendar_event.event_type::text = 'External'::character varying::text
      AND attent_calendar.email_address::text = attent_calendar_event.organizer_email_address::text
      AND attent_calendar_event.id::text = attent_calendar_event_has_external_attendee.attent_calendar_event_id::character varying::text
      AND attent_calendar_event_has_external_attendee.external_attendee_id::character varying::text = external_attendee.id::text
      AND external_attendee.email_address::text = salesforce_contact.email::text
      AND salesforce_contact.account_id::text = salesforce_account.sfdc_id::text
      AND salesforce_account.sfdc_id::text = salesforce_opportunity.account_id::text
      """.format(warehouse_view_name, client_id)


def get_model_for_view_contact(view_name):
    class WarehouseMetaClassContact(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += view_name
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class WarehouseViewContact(models.Model):
        __metaclass__ = WarehouseMetaClassContact

        class Meta:
            db_table = view_name
            managed = False

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

    return WarehouseViewContact


def get_model_for_view_oppty(view_name):
    class WarehouseMetaClassOppty(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += view_name
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class WarehouseViewOppty(models.Model):
        __metaclass__ = WarehouseMetaClassOppty

        class Meta:
            db_table = view_name
            managed = False

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
        account_sfdc_id = models.TextField()
        account_name = models.TextField()
        account_type = models.TextField(null=True)
        number_of_employees = models.PositiveIntegerField()
        billing_city = models.TextField()
        billing_state = models.TextField()
        billing_country = models.TextField()
        opportunity_sfdc_id = models.TextField()
        opportunity_name = models.TextField()
        opportunity_type = models.TextField()
        stage_name = models.TextField()
        amount = models.PositiveIntegerField()
        close_date = models.DateTimeField()

    return WarehouseViewOppty
