from protocols import CalendarService
from schema import CalendarsResponse


def get_specific_calendar(service: CalendarService, calendar_name: str) -> CalendarsResponse | None:
    calendars = service.calendarList().list().execute()
    for calendar in calendars["items"]:
        if calendar_name.lower() in calendar["summary"].lower():
            return CalendarsResponse.model_validate(calendar)
    return None
