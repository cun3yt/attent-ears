from django.contrib.postgres.fields import JSONField
from django.db import models
from core.mixins import NoUpdateTimeStampedMixin, TimeStampedMixin
from visualizer.models import User


class OutreachUser(TimeStampedMixin):
    class Meta:
        db_table = 'outreach_user'

    user = models.ForeignKey(User)
    data = JSONField(default={})



class OutreachApiLog(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'outreach_api_log'

    outreach_user = models.ForeignKey(OutreachUser)
    resource = models.CharField(max_length=50, default='')
    args = JSONField(default={})
    response = JSONField(default={})

    @staticmethod
    def log(outreach_user: OutreachUser, resource, args, response):
        new_log = OutreachApiLog(outreach_user=outreach_user,
                                 resource=resource,
                                 args=args,
                                 response=response)
        new_log.save()
