from django.contrib.postgres.fields import JSONField
from django.db import models
from core.mixins import TimeStampedMixin
from visualizer.models import User


class OutreachProspect(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_prospect'
    pass


class OutreachMailing(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_mailing'
    pass
