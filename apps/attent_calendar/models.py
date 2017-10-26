from django.db import models

from apps.google_calendar.models import GoogleCalendar, GoogleCalendarEvent
from core.email_domains import is_email_address_personal
from core.mixins import TimeStampedMixin
from visualizer.models import Client


class AttentCalendar(TimeStampedMixin):
    class Meta:
        db_table = 'attent_calendar'

    google_calendar = models.ForeignKey(GoogleCalendar, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    email_address = models.CharField(db_index=True, max_length=255)
    timezone = models.CharField(max_length=50, default="America/Los_Angeles")
    first_name = models.CharField(max_length=30, default="")
    last_name = models.CharField(max_length=30, default="")
    title = models.CharField(max_length=40, default="")


class InternalAttendee(TimeStampedMixin):
    class Meta:
        db_table = 'internal_attendee'
    email_address = models.CharField(db_index=True, max_length=255)


class ExternalAttendee(TimeStampedMixin):
    class Meta:
        db_table = 'external_attendee'
    email_address = models.CharField(db_index=True, max_length=255)

    @property
    def is_business_email_address(self):
        return not is_email_address_personal(self.email_address)


class AttentCalendarEvent(TimeStampedMixin):
    class Meta:
        db_table = 'attent_calendar_event'

    google_calendar_event = models.ForeignKey(GoogleCalendarEvent, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    event_id = models.CharField(db_index=True, max_length=1024, default="", blank=True)    # Google Calendar Event Id

    summary = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_full_day = models.BooleanField(default=False)

    creator_email_address = models.CharField(max_length=255)
    organizer_email_address = models.CharField(max_length=255)

    event_type = models.CharField(max_length=10, default='')

    internal_attendees = models.ManyToManyField(
        InternalAttendee,
        through='AttentCalendarEventHasInternalAttendee',
        through_fields=('attent_calendar_event', 'internal_attendee'),
        related_name='attent_calendar_events',
        related_query_name='attent_calendar_event',
    )
    external_attendees = models.ManyToManyField(
        ExternalAttendee,
        through='AttentCalendarEventHasExternalAttendee',
        through_fields=('attent_calendar_event', 'external_attendee'),
        related_name='attent_calendar_events',
        related_query_name='attent_calendar_event',
    )


class AttentCalendarEventHasInternalAttendee(TimeStampedMixin):
    class Meta:
        db_table = 'attent_calendar_event_has_internal_attendee'
    attent_calendar_event = models.ForeignKey(AttentCalendarEvent, on_delete=models.CASCADE)
    internal_attendee = models.ForeignKey(InternalAttendee, on_delete=models.CASCADE)
    response_status = models.CharField(max_length=20, default='')

    index_together = ["attent_calendar_event", "internal_attendee"]


class AttentCalendarEventHasExternalAttendee(TimeStampedMixin):
    class Meta:
        db_table = 'attent_calendar_event_has_external_attendee'
    attent_calendar_event = models.ForeignKey(AttentCalendarEvent, on_delete=models.CASCADE)
    external_attendee = models.ForeignKey(ExternalAttendee, on_delete=models.CASCADE)
    response_status = models.CharField(max_length=20, default='')

    index_together = ["attent_calendar_event", "external_attendee"]
