from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from apps.visualizer.models import User
from core.mixins import TimeStampedMixin, NoUpdateTimeStampedMixin


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


class NoApiSyncStatusError(Exception):
    pass


class ApiSyncStatus(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'api_sync_status'

    api_connection = models.ForeignKey(ApiConnection)
    resource = models.CharField(max_length=50, default='')
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(null=True, blank=True, default=None)
    extra_data = JSONField(default={})

    @staticmethod
    def add_sync_status(api_connection: ApiConnection, resource, start=None, extra_data=None):
        entry_start_time = timezone.now() if start is None else start
        entry_extra_data = {} if extra_data is None else extra_data
        status = ApiSyncStatus(
            api_connection=api_connection,
            resource=resource,
            start=entry_start_time,
            extra_data=entry_extra_data,
        )
        status.save()
        return status

    def add_end(self, end=None):
        entry_end_time = timezone.now() if end is None else end
        self.end = entry_end_time
        self.save()
        return self

    @staticmethod
    def get_last_completed_sync(api_connection: ApiConnection, resource):
        try:
            return ApiSyncStatus.objects.filter(api_connection=api_connection,
                                                resource=resource,
                                                end__isnull=False).latest(field_name='start')

        except Exception:
            raise NoApiSyncStatusError
