from django.contrib.postgres.fields import JSONField
from django.db import models
from core.mixins import TimeStampedMixin
from visualizer.models import User, Client


class OutreachAccount(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_account'

    client = models.ForeignKey(Client, null=True)

    outreach_id = models.IntegerField(db_index=True)

    name = models.CharField(max_length=100, blank=True, default='')
    natural_name = models.CharField(max_length=100, blank=True, default='')
    company_type = models.CharField(max_length=20, blank=True, default='')
    domain = models.CharField(max_length=255, blank=True, default='')
    website_url = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(db_index=True, null=True, blank=True)

    covering_api_offset = models.IntegerField(default=0)


class OutreachProspect(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_prospect'

    client = models.ForeignKey(Client, null=True)

    outreach_id = models.IntegerField(db_index=True)
    outreach_account_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)
    outreach_owner_user_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)

    all_email_addresses = models.TextField(default='')
    engaged_score = models.IntegerField(blank=True, default=None, null=True)
    first_name = models.CharField(max_length=20, blank=True, default='')
    last_name = models.CharField(max_length=20, blank=True, default='')
    middle_name = models.CharField(max_length=20, blank=True, default='')
    occupation = models.CharField(max_length=50, blank=True, default='')
    title = models.CharField(max_length=100, blank=True, default='')
    open_count = models.IntegerField(blank=True, default=0)
    reply_count = models.IntegerField(blank=True, default=0)
    click_count = models.IntegerField(blank=True, default=0)
    engaged_at = models.DateTimeField(null=True, blank=True, default=None)
    opted_out_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(db_index=True, null=True, blank=True)

    covering_api_offset = models.IntegerField(default=0)


class OutreachProspectV1(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_prospect_v1'

    client = models.ForeignKey(Client, null=True)

    outreach_id = models.IntegerField(db_index=True)
    email_address = models.CharField(max_length=255, blank=True, default='')
    phone_number_personal = models.CharField(max_length=20, blank=True, default='')
    phone_number_work = models.CharField(max_length=20, blank=True, default='')


class OutreachUser(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_user'

    client = models.ForeignKey(Client)

    outreach_id = models.IntegerField(db_index=True)
    email_address = models.CharField(max_length=255, db_index=True, default='')
    first_name = models.CharField(max_length=30, blank=True, default='')
    last_name = models.CharField(max_length=30, blank=True, default='')
    username = models.CharField(max_length=30, blank=True, default='')

    covering_api_offset = models.IntegerField(default=0)


class OutreachMailing(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_mailing'

    client = models.ForeignKey(Client)

    outreach_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)
    outreach_prospect_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)

    mailing_type = models.CharField(max_length=30, blank=True, default='')
    mailbox_address = models.CharField(max_length=255, blank=True, default='', db_index=True)

    subject = models.CharField(max_length=255, blank=True, default="", null=True)
    body_text = models.TextField(blank=True, default="", null=True)
    open_count = models.IntegerField(blank=True, default=0, null=True)
    click_count = models.IntegerField(blank=True, default=0, null=True)

    opened_at = models.DateTimeField(null=True, blank=True, default=None)
    replied_at = models.DateTimeField(null=True, blank=True, default=None)
    bounced_at = models.DateTimeField(null=True, blank=True, default=None)
    marked_as_spam_at = models.DateTimeField(null=True, blank=True, default=None)

    scheduled_at = models.DateTimeField(null=True, blank=True, default=None)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(db_index=True, null=True, blank=True)

    covering_api_offset = models.IntegerField(default=0)


class OutreachCall(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_call'

    client = models.ForeignKey(Client)
    outreach_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)

    outreach_prospect_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)
    outreach_user_id = models.IntegerField(db_index=True, blank=True, default=None, null=True)

    outcome = models.CharField(max_length=20, blank=True, default=None, null=True)
    answered_at = models.DateTimeField(null=True, blank=True, default=None)
    completed_at = models.DateTimeField(null=True, blank=True, default=None)
    direction = models.CharField(max_length=20, blank=True, default='')
    state = models.CharField(max_length=20, blank=True, default='')
    record_url = models.CharField(max_length=2000, blank=True, default=None, null=True)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(db_index=True, null=True, blank=True)

    covering_api_offset = models.IntegerField(default=0)
