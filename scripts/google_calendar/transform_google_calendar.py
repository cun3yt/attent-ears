import sys
import traceback

from apps.attent_calendar.models import AttentCalendar
from apps.google_calendar.models import GoogleCalendar


def run():
    print("Script: Transform Google Calendar Script Runs")

    try:
        # Google Calendars set to be kept in sync get created or updated as Attent Calendar
        calendars_to_update_or_create = GoogleCalendar.objects.filter(is_kept_in_sync=True)

        for calendar in calendars_to_update_or_create:
            _, is_created = AttentCalendar.objects.update_or_create(
                email_address=calendar.email_address,
                defaults={
                    'google_calendar': calendar,
                    'client': calendar.sync_user.client,
                    'timezone': calendar.timezone,
                }
            )
            msg = "Attent Calendar is Created: {}" if is_created else "Attent Calendar is Updated: {}"
            print(msg.format(calendar.email_address))

        # Calendars with `is_kept_in_sync` == FALSE get deleted
        calendars_to_delete_due_to_sync_state = AttentCalendar.objects.filter(google_calendar__is_kept_in_sync=False)

        for attent_calendar in calendars_to_delete_due_to_sync_state:
            print("Attent Calendar Gets Deleted: {}".format(attent_calendar.email_address))
            attent_calendar.delete()

        # Calendars that doesn't exists in GoogleCalendar get deleted
        calendars_to_delete_due_to_non_existence = AttentCalendar.objects.filter(google_calendar__isnull=True)

        for attent_calendar in calendars_to_delete_due_to_non_existence:
            print("Attent Calendar Gets Deleted: {}".format(attent_calendar.email_address))
            attent_calendar.delete()

    except Exception as exc:
        print("Log This: Unexpected Exception Exception Details: {}".format(exc))
        print("-"*60)
        traceback.print_exc(file=sys.stdout)
        print("-"*60)
