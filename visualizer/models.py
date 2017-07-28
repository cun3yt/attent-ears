from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from email_split import email_split
import binascii
import hmac
import hashlib
from urllib.parse import urlencode
import json
from . import exceptions

from core.mixins import TimeStampedMixin


class Client(TimeStampedMixin):
    class Meta:
        db_table = 'client'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    email_domain = models.CharField(max_length=255)
    extra_info = JSONField(default={})

    def is_email_address_in_domain(self, email_address: str):
        email = email_split(email_address)
        return email.domain == self.email_domain


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


@receiver(post_save, sender=User)
def set_client_of_user(sender, instance, **kwargs):
    user = instance

    if user.client:
        return

    email = email_split(user.email)
    client, _ = Client.objects.get_or_create(email_domain=email.domain)
    user.client = client
    user.save()
