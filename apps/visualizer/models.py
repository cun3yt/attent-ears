import binascii
import hashlib
import hmac
import json
from urllib.parse import urlencode

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from email_split import email_split

from core.email_domains import is_email_address_in_domain
from core.email_domains import is_email_address_personal
from core.mixins import TimeStampedMixin
from . import exceptions
from datetime import datetime
from django.utils.dateformat import format

from ears.settings import EARS_ENV


CLIENT_STATUS_APPLIED = 'Applied'
CLIENT_STATUS_ACTIVE = 'Active'
CLIENT_STATUS_TERMINATED = 'Terminated'

CLIENT_STATUS_CHOICES = (
    (CLIENT_STATUS_APPLIED, CLIENT_STATUS_APPLIED),
    (CLIENT_STATUS_ACTIVE, CLIENT_STATUS_ACTIVE),
    (CLIENT_STATUS_TERMINATED, CLIENT_STATUS_TERMINATED),
)


class Client(TimeStampedMixin):
    class Meta:
        db_table = 'client'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    email_domain = models.CharField(max_length=255)
    extra_info = JSONField(default={})
    status = models.TextField(choices=CLIENT_STATUS_CHOICES, default=CLIENT_STATUS_APPLIED)
    warehouse_view_name = models.TextField(null=True, default=None)
    warehouse_view_definition = models.TextField(null=True, default=None)

    def create_warehouse_view(self):
        if self.warehouse_view_name is not None:
            raise Exception("View Name is not Empty")
        self.warehouse_view_name = "view_{}_client_{}_{}".format(EARS_ENV, self.id, format(datetime.now(), 'U'))
        self.save()
        sql = """CREATE OR REPLACE VIEW {} AS
SELECT DISTINCT attent_calendar_event.id AS meeting_id,
  timezone('PDT'::character varying::text, timezone('UTC'::character varying::text, attent_calendar_event."start")) AS meeting_date,
  attent_calendar.first_name,
  attent_calendar.title AS role,
  attent_calendar_event.summary,
  attent_calendar_event.description,
  salesforce_contact.email,
  salesforce_contact.name AS contact_name,
  salesforce_contact.title AS contact_title,
  salesforce_account.name AS account_name,
  salesforce_account."type" AS account_type,
  salesforce_account.number_of_employees,
  salesforce_account.created_date,
  salesforce_account.billing_city,
  salesforce_account.billing_state,
  salesforce_account.billing_country,
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
  attent_calendar.email_address::text = attent_calendar_event.organizer_email_address::text
  AND attent_calendar_event.id::text = attent_calendar_event_has_external_attendee.attent_calendar_event_id::character varying::text
  AND attent_calendar_event_has_external_attendee.external_attendee_id::character varying::text = external_attendee.id::text
  AND external_attendee.email_address::text = salesforce_contact.email::text
  AND salesforce_contact.account_id::text = salesforce_account.sfdc_id::text
  AND salesforce_account.sfdc_id::text = salesforce_opportunity.account_id::text
  AND attent_calendar.client_id = {}
  AND attent_calendar_event.event_type::text = 'External'::character varying::text""".format(self.warehouse_view_name, self.id)
        from django.db import connections
        cursor = connections['warehouse'].cursor()
        cursor.execute(sql, [])

    def get_warehouse_view_model(self):
        if self.warehouse_view_name is None:
            self.create_warehouse_view()

        view_name = self.warehouse_view_name

        class WarehouseMetaclass(models.base.ModelBase):
            def __new__(cls, name, bases, attrs):
                name += view_name
                return models.base.ModelBase.__new__(cls, name, bases, attrs)

        class WarehouseView(models.Model):
            __metaclass__ = WarehouseMetaclass

            class Meta:
                db_table = view_name
                managed = False

            meeting_id = models.TextField(primary_key=True)
            first_name = models.TextField()
            role = models.TextField()
            summary = models.TextField()
            description = models.TextField()
            email = models.TextField()
            contact_name = models.TextField()
            contact_title = models.TextField()
            account_name = models.TextField()

        return WarehouseView

    def is_email_address_in_domain(self, email_address: str):
        return is_email_address_in_domain(email_address, self.email_domain)

    def __str__(self):
        return '%s (%s)' % (self.name, self.email_domain)


class User(AbstractUser, TimeStampedMixin):
    class Meta:
        db_table = 'user'
    client = models.ForeignKey(Client, null=True, on_delete=models.SET_NULL)

    def get_google_oauth2_user(self):
        query_set = self.social_auth.filter(provider='google-oauth2')

        if query_set.count() < 1:
            exception_msg = "No Authentication Found for User Email: {}".format(self.email)
            raise exceptions.OAuth2UserNotAvailable(message=exception_msg)
        elif query_set.count() > 1:
            exception_msg = "More Than One Authentication Found for User Email: {}".format(self.email)
            raise exceptions.OAuth2UserNotAvailable(message=exception_msg)

        return query_set[0]


class PeriscopeDashboard(TimeStampedMixin):
    class Meta:
        db_table = 'periscope_dashboard'

    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    periscope_dashboard_id = models.CharField(max_length=10)
    dashboard_name = models.CharField(max_length=255, default='')
    is_visible = models.BooleanField(default=False)

    @staticmethod
    def get_url():
        return "https://www.periscopedata.com"

    def get_embed_url(self, api_key):
        data = {
            'dashboard': self.periscope_dashboard_id,
            'embed': 'v2',
            'filters': [],
        }

        path = '/api/embedded_dashboard?%s' % urlencode({'data': json.dumps(data)})
        sign = binascii.hexlify(hmac.new(bytes(api_key, encoding='utf8'), msg=path.encode('utf-8'),
                                         digestmod=hashlib.sha256).digest()).decode("utf-8")
        url = '{}{}&signature={}'.format(self.get_url(), path, sign)
        return url


@receiver(post_save, sender=User) # inanc's suggestion: social auth pipeline alternative
def set_client_of_user(sender, instance, **kwargs):
    user = instance

    if user.client:
        return

    email = email_split(user.email)

    if is_email_address_personal(email.domain):     # admin user may be from a personal domain
        return

    client, _ = Client.objects.get_or_create(email_domain=email.domain)
    user.client = client
    user.save()
