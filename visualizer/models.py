from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
from django.core.paginator import Paginator
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from email_split import email_split

from core.mixins import TimeStampedMixin


class Client(TimeStampedMixin):
    class Meta:
        db_table = 'client'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    email_domain = models.CharField(max_length=255)
    extra_info = JSONField(default={})


class User(AbstractUser, TimeStampedMixin):
    class Meta:
        db_table = 'user'
    client = models.ForeignKey(Client, null=True, on_delete=models.SET_NULL)
    # calendar = models.ForeignKey(Calendar, null=True, on_delete=models.SET_NULL)

    @staticmethod
    def users_without_calendar():
        users_list = User.objects.filter(calendar__isnull=True).order_by('id')
        return Paginator(users_list, 10)


class PeriscopeDashboard(TimeStampedMixin):
    class Meta:
        db_table = 'periscope_dashboard'

    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    periscope_dashboard_id = models.CharField(max_length=10)
    dashboard_name = models.CharField(max_length=255, default='')
    is_visible = models.BooleanField(default=False)


@receiver(post_save, sender=User)
def set_client_of_user(sender, instance, **kwargs):
    user = instance

    if user.client:
        return

    email = email_split(user.email)
    client, _ = Client.objects.get_or_create(email_domain=email.domain)
    user.client = client
    user.save()
