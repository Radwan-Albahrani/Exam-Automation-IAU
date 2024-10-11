from commons import print_success
from protocols import CalendarService
from schema import CalendarsResponse


def get_specific_calendar(service: CalendarService) -> CalendarsResponse | None:
    calendars = service.calendarList().list().execute()
    calendars["items"] = sorted(calendars["items"], key=lambda x: x["summary"])
    print_success("============================= Available Calendars =============================")
    for calendar in calendars["items"]:
        print(calendar["summary"])
    print_success("=================================================================================")
    calendar_name = input("Enter the name of the calendar to add the events to: ")
    for calendar in calendars["items"]:
        if calendar_name.lower() in calendar["summary"].lower():
            return CalendarsResponse.model_validate(calendar)

    return None
