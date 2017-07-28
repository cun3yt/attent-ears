from django.contrib.postgres.fields import JSONField
from django.db import models
from core.mixins import TimeStampedMixin, NoUpdateTimeStampedMixin

from visualizer.models import User


class GoogleCalendarListSync(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'google_calendar_list_sync'

    KEY_PAGE_TOKEN = 'page_token'
    KEY_SYNC_TOKEN = 'sync_token'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User)
    sync_detail = JSONField()

    @staticmethod
    def get_last_sync(user: User):
        try:
            return GoogleCalendarListSync.objects.filter(user__id=user.id).order_by('-created_at')[0]
        except IndexError:
            return None

    def get_page_token(self):
        if self.KEY_PAGE_TOKEN in self.sync_detail:
            return self.sync_detail[self.KEY_PAGE_TOKEN]
        return None

    def get_sync_token(self):
        if self.KEY_SYNC_TOKEN in self.sync_detail:
            return self.sync_detail[self.KEY_SYNC_TOKEN]
        return None


class GoogleCalendarApiLogs(NoUpdateTimeStampedMixin):
    class Meta:
        db_table = 'google_calendar_api_log'

    id = models.AutoField(primary_key=True)
    user_email_address = models.CharField(max_length=127)
    resource = models.CharField(max_length=50)
    args = JSONField()
    response = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class GoogleCalendar(TimeStampedMixin):
    class Meta:
        db_table = 'google_calendar'

    KEY_SYNC_STATE = 'sync_state'
    VAL_SYNC_STATE_UNINITIALIZED = 'uninitialized'
    VAL_SYNC_STATE_INITIALIZED = 'initialized'

    id = models.AutoField(primary_key=True)
    email_address = models.CharField(max_length=255)
    sync_detail = JSONField(default={KEY_SYNC_STATE: VAL_SYNC_STATE_UNINITIALIZED})
    sync_user = models.ForeignKey(User)
    sync_user_history = JSONField(default={})
    last_sync_datetime = models.DateTimeField(auto_now=True)
