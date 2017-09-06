from django.contrib.postgres.fields import JSONField, HStoreField
from django.db import models
from core.mixins import TimeStampedMixin
from visualizer.models import User, Client

from stringcase import pascalcase


class SalesforceCustomFieldMapping(TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_custom_field_mapping'

    client = models.ForeignKey(Client)
    entity = models.CharField(max_length=50, db_index=True, blank=False, null=False)

    # Sample Data: "field1_mapped_to"=>"ARR", "field1_sfdc_name"=>"ARR__c"
    # Update Query: update salesforce_custom_field_mapping set
    #               "mapping" = 'field1_sfdc_name=>ARR__c,field1_mapped_to=>ARR'::hstore
    #               where id = 1;
    mapping = HStoreField()


class SalesforceEntityMixin(models.Model):
    class Meta:
        abstract = True

    custom_field1 = models.TextField(blank=True, default=None, null=True)
    custom_field2 = models.TextField(blank=True, default=None, null=True)
    custom_field3 = models.TextField(blank=True, default=None, null=True)
    custom_field4 = models.TextField(blank=True, default=None, null=True)
    custom_field5 = models.TextField(blank=True, default=None, null=True)
    custom_field6 = models.TextField(blank=True, default=None, null=True)
    custom_field7 = models.TextField(blank=True, default=None, null=True)
    custom_field8 = models.TextField(blank=True, default=None, null=True)
    custom_field9 = models.TextField(blank=True, default=None, null=True)
    custom_field10 = models.TextField(blank=True, default=None, null=True)
    custom_field11 = models.TextField(blank=True, default=None, null=True)
    custom_field12 = models.TextField(blank=True, default=None, null=True)
    custom_field13 = models.TextField(blank=True, default=None, null=True)
    custom_field14 = models.TextField(blank=True, default=None, null=True)
    custom_field15 = models.TextField(blank=True, default=None, null=True)

    @classmethod
    def field_mapping_overrides(cls):
        raise NotImplementedError

    @classmethod
    def field_names(cls):
        return [f.name for f in cls._meta.fields]

    @classmethod
    def save_from_bulk_row(cls, row, client: Client):
        print('save_from_bulk_row is called')

        import ipdb
        ipdb.set_trace()

        field_names = cls.field_names()
        overrides = cls.field_mapping_overrides()

        entity_dict = {}

        for field_name in field_names:
            row_index = pascalcase(field_name)
            try:
                row[row_index]
            except KeyError:
                continue

            if field_name in overrides:
                entity_dict[overrides[field_name]] = row[row_index]
            else:
                entity_dict[field_name] = row[row_index]

        entity_dict['client'] = client

        cls.objects.update_or_create(
            client=client,
            sfdc_id=entity_dict['sfdc_id'],
            defaults=entity_dict,
        )


class SalesforceAccount(SalesforceEntityMixin, TimeStampedMixin):
    class Meta:
        db_table = 'salesforce_account'

    client = models.ForeignKey(Client)
    sfdc_id = models.TextField(db_index=True)
    is_deleted = models.TextField()
    master_record_id = models.TextField()
    name = models.TextField()
    type = models.TextField()

    website = models.TextField()
    number_of_employees = models.TextField()

    owner_id = models.TextField()
    created_date = models.TextField()
    created_by_id = models.TextField()
    last_modified_date = models.TextField()
    last_modified_by_id = models.TextField()

    last_activity_date = models.TextField()
    last_viewed_date = models.TextField()
    account_source = models.TextField()

    @classmethod
    def field_mapping_overrides(cls):
        return {
            'id': 'sfdc_id',
        }
