from django.db import models


class TimeStampedMixin(models.Model):
    class Meta:
        abstract = True
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class NoUpdateTimeStampedMixin(models.Model):
    class Meta:
        abstract = True
    created_at = models.DateTimeField(auto_now_add=True)
