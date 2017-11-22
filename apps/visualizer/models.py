import binascii
import hashlib
import hmac
import json
from urllib.parse import urlencode

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db import connections as database_connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from email_split import email_split

from core.email_domains import is_email_address_in_domain
from core.email_domains import is_email_address_personal
from core.mixins import TimeStampedMixin
from . import exceptions
from datetime import datetime
from django.utils.dateformat import format
from .warehouse_sql_views import create_view_sql_for_event_contact, create_view_sql_for_event_oppty, \
    create_view_sql_for_event_account, get_model_for_view_contact, get_model_for_view_account, get_model_for_view_oppty

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
    warehouse_view_name_contact = models.TextField(null=True, default=None)
    warehouse_view_name_account = models.TextField(null=True, default=None)
    warehouse_view_name_oppty = models.TextField(null=True, default=None)
    slack_team_id = models.TextField(db_index=True, null=True, default=None)

    def is_active(self):
        return self.status == CLIENT_STATUS_ACTIVE

    def is_email_address_in_domain(self, email_address: str):
        return is_email_address_in_domain(email_address, self.email_domain)

    def __str__(self):
        return '%s (%s)' % (self.name, self.email_domain)

    def create_warehouse_view_contact(self):
        if self.warehouse_view_name_contact is not None:
            raise Exception("View Name is not Empty")
        self.warehouse_view_name_contact = "view_{}_contact_client_{}_{}".format(EARS_ENV, self.id,
                                                                                 format(datetime.now(), 'U'))
        self.save()
        sql = create_view_sql_for_event_contact(self.warehouse_view_name_contact, self.id)
        cursor = database_connection['warehouse'].cursor()
        cursor.execute(sql, [])

    def create_warehouse_view_account(self):
        if self.warehouse_view_name_account is not None:
            raise Exception("View Name is not Empty")
        self.warehouse_view_name_account = "view_{}_account_client_{}_{}".format(EARS_ENV, self.id,
                                                                                 format(datetime.now(), 'U'))
        self.save()
        sql = create_view_sql_for_event_account(self.warehouse_view_name_account, self.id)
        cursor = database_connection['warehouse'].cursor()
        cursor.execute(sql, [])

    def create_warehouse_view_oppty(self):
        if self.warehouse_view_name_oppty is not None:
            raise Exception("View Name is not Empty")
        self.warehouse_view_name_oppty = "view_{}_oppty_client_{}_{}".format(EARS_ENV, self.id,
                                                                             format(datetime.now(), 'U'))
        self.save()
        sql = create_view_sql_for_event_oppty(self.warehouse_view_name_oppty, self.id)
        cursor = database_connection['warehouse'].cursor()
        cursor.execute(sql, [])

    def get_warehouse_view_model_for_contact(self):
        if self.warehouse_view_name_contact is None:
            self.create_warehouse_view_contact()
        view_name = self.warehouse_view_name_contact
        return get_model_for_view_contact(view_name)

    def get_warehouse_view_model_for_account(self):
        if self.warehouse_view_name_account is None:
            self.create_warehouse_view_account()
        view_name = self.warehouse_view_name_account
        return get_model_for_view_account(view_name)

    def get_warehouse_view_model_for_oppty(self):
        if self.warehouse_view_name_oppty is None:
            self.create_warehouse_view_oppty()
        view_name = self.warehouse_view_name_oppty
        return get_model_for_view_oppty(view_name)


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
