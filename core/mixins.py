from django.db import models


class TimeStampedMixin(models.Model):
    class Meta:
        abstract = True
    db_updated_at = models.DateTimeField(auto_now=True)
    db_created_at = models.DateTimeField(auto_now_add=True)


class NoUpdateTimeStampedMixin(models.Model):
    class Meta:
        abstract = True
    db_created_at = models.DateTimeField(auto_now_add=True)
