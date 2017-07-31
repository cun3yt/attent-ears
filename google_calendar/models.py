from django.contrib.postgres.fields import JSONField
from django.db import models
from core.mixins import TimeStampedMixin, NoUpdateTimeStampedMixin

from visualizer.models import User


class GoogleCalendarListSyncState(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'google_calendar_list_sync_state'

    user = models.ForeignKey(User)
    sync_detail = JSONField(default={})

    KEY_PAGE_TOKEN = 'page_token'
    KEY_SYNC_TOKEN = 'sync_token'

    def get_page_token(self):
        return self.sync_detail.get(self.KEY_PAGE_TOKEN, None)

    def get_sync_token(self):
        return self.sync_detail.get(self.KEY_SYNC_TOKEN, None)

    @staticmethod
    def get_last_sync(user: User):
        try:
            return GoogleCalendarListSyncState.objects.filter(user__id=user.id).order_by('-created_at')[0]
        except IndexError:
            return None


class GoogleCalendarApiLogs(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'google_calendar_api_log'

    user_email_address = models.CharField(max_length=255)
    resource = models.CharField(max_length=50)
    args = JSONField()
    response = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def log(email_address, resource, args, response):
        new_log = GoogleCalendarApiLogs(user_email_address=email_address,
                                        resource=resource,
                                        args=args,
                                        response=response)
        new_log.save()



class GoogleCalendar(TimeStampedMixin):
    class Meta:
        db_table = 'google_calendar'

    KV_SYNC_STATE_KEY = 'sync_state'
    KV_SYNC_STATE_VAL_UNINITIALIZED = 'uninitialized'
    KV_SYNC_STATE_VAL_INITIALIZED = 'initialized'

    KEY_PAGE_TOKEN = 'page_token'
    KEY_SYNC_TOKEN = 'sync_token'

    email_address = models.CharField(max_length=255)
    etag = models.CharField(max_length=20, default="")
    sync_detail = JSONField(default={KV_SYNC_STATE_KEY: KV_SYNC_STATE_VAL_UNINITIALIZED})
    sync_user = models.ForeignKey(User)
    sync_user_history = JSONField(default={})
    last_sync_datetime = models.DateTimeField(null=True, default=None)
    is_kept_in_sync = models.BooleanField(default=True)

    def get_page_token(self):
        return self.sync_detail.get(self.KEY_PAGE_TOKEN, None)

    def get_sync_token(self):
        return self.sync_detail.get(self.KEY_SYNC_TOKEN, None)

    def get_last_sync_state(self):
        return self.sync_detail


class GoogleCalendarEvent(TimeStampedMixin):
    class Meta:
        db_table = 'google_calendar_event'


