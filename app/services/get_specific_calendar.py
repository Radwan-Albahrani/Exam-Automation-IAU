from protocols import CalendarService
from schema import CalendarsResponse


def get_specific_calendar(service: CalendarService) -> CalendarsResponse | None:
    calendars = service.calendarList().list().execute()
    for calendar in calendars["items"]:
        print(calendar["summary"])
    calendar_name = input("Enter the name of the calendar to add the events to: ")
    for calendar in calendars["items"]:
        if calendar_name.lower() in calendar["summary"].lower():
            return CalendarsResponse.model_validate(calendar)

    return None
