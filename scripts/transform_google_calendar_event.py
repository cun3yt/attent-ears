from django.db.models import F
from google_calendar.models import GoogleCalendarEvent
from attent_calendar.models import AttentCalendarEvent, InternalAttendee, ExternalAttendee, \
    AttentCalendarEventHasInternalAttendee, AttentCalendarEventHasExternalAttendee
from core.email_domains import is_email_address_personal
from django.utils import timezone
from django.utils import dateparse

import sys
import traceback


def transform_event_to_attent_event(gc_event: GoogleCalendarEvent):
    print("Transform event id: {}".format(gc_event.id))
    client = gc_event.client

    start_dict = gc_event.start
    end_dict = gc_event.end
    is_full_day_event = 'date' in start_dict

    start = dateparse.parse_datetime("{}T00:00+00".format(start_dict['date'])) if is_full_day_event \
        else dateparse.parse_datetime(start_dict['dateTime'])
    end = dateparse.parse_datetime("{}T00:00+00".format(end_dict['date'])) if is_full_day_event \
        else dateparse.parse_datetime(end_dict['dateTime'])

    defaults = {
        'google_calendar_event': gc_event,
        'client': client,
        'summary': gc_event.summary,
        'description': gc_event.description,
        'creator_email_address': gc_event.creator.get('email', ''),
        'organizer_email_address': gc_event.organizer.get('email', ''),
        'start': start,
        'end': end,
        'is_full_day': is_full_day_event
    }
    event, _ = AttentCalendarEvent.objects.update_or_create(event_id=gc_event.event_id, defaults=defaults)

    # process attendees
    for gc_attendee in gc_event.attendees:
        attendee_e_address = gc_attendee.get('email')
        response_status = gc_attendee.get('responseStatus')
        if client.is_email_address_in_domain(attendee_e_address):
            attendee, _ = InternalAttendee.objects.get_or_create(email_address=attendee_e_address)

            AttentCalendarEventHasInternalAttendee.objects.update_or_create(attent_calendar_event=event,
                                                                            internal_attendee=attendee,
                                                                            defaults={
                                                                                'response_status': response_status
                                                                            })

        else:
            attendee, _ = ExternalAttendee.objects.get_or_create(email_address=attendee_e_address)
            AttentCalendarEventHasExternalAttendee.objects.update_or_create(attent_calendar_event=event,
                                                                            external_attendee=attendee,
                                                                            defaults={
                                                                                'response_status': response_status
                                                                            })

    # set event type
    external_atts = [att for att in gc_event.attendees if not client.is_email_address_in_domain(att.get('email'))]
    business_email_atts = [att for att in external_atts if not is_email_address_personal(att.get('email'))]

    if len(external_atts) == 0:
        event.event_type = 'Internal'
    elif len(business_email_atts) > 0:
        event.event_type = 'External'
    else:
        event.event_type = 'Other'

    event.save()

    gc_event.process_time = timezone.now()
    gc_event.save()


print("Script: Transform Google Calendar Event Script Runs")

try:
    gc_events_not_processed = GoogleCalendarEvent.objects.filter(process_time__isnull=True)

    for gc_event in gc_events_not_processed:
        # update or create an entry in AttentCalendarEvent.
        # Possibility: google_calendar_event is repopulated
        transform_event_to_attent_event(gc_event)

    gc_events_updated = GoogleCalendarEvent.objects.filter(process_time__isnull=False, process_time__lt=F('updated'))

    for gc_event in gc_events_updated:
        # update or create an entry in AttentCalendarEvent.
        # Creation should not be needed, just in case.
        transform_event_to_attent_event(gc_event)


except Exception as exc:
    print("Log This: Unexpected Exception Exception Details: {}".format(exc))
    print("-"*60)
    traceback.print_exc(file=sys.stdout)
    print("-"*60)



