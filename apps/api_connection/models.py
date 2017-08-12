from django.db import models
from django.contrib.postgres.fields import JSONField
from core.mixins import TimeStampedMixin, NoUpdateTimeStampedMixin
from visualizer.models import User


class ApiConnection(TimeStampedMixin):
    class Meta:
        db_table = 'api_connection'

    user = models.ForeignKey(User,
                             related_name='api_connections',
                             related_query_name='api_connection')
    type = models.CharField(max_length=30, default='')
    data = JSONField(default={})


class ApiConnectionLog(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'api_connection_log'

    api_connection = models.ForeignKey(ApiConnection)
    resource = models.CharField(max_length=50, default='')
    args = JSONField(default={})
    response = JSONField(default={})

    @staticmethod
    def log(api_connection: ApiConnection, resource, args, response):
        new_log = ApiConnectionLog(api_connection=api_connection,
                                   resource=resource,
                                   args=args,
                                   response=response)
        new_log.save()
