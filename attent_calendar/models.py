from django.db import models
from core.mixins import TimeStampedMixin
from google_calendar.models import GoogleCalendar
from visualizer.models import Client


class AttentCalendar(TimeStampedMixin):
    class Meta:
        db_table = 'attent_calendar'

    google_calendar = models.ForeignKey(GoogleCalendar)
    email_address = models.CharField(max_length=255)
    client = models.ForeignKey(Client)
    timezone = models.CharField(max_length=50, default="America/Los_Angeles")
