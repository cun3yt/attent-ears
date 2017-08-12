from .extract_google_calendar import run as extract_run
from .transform_google_calendar import run as transform_calendar_run
from .transform_google_calendar_event import run as transform_event_run


def run():
    extract_run()
    transform_calendar_run()
    transform_event_run()
