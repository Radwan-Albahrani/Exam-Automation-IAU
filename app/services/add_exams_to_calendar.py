import datetime as dt

from commons import print_error
from protocols import CalendarService
from schema import AddEventsResponse, CalendarEventRequest, CalendarEventResponse


def add_exams_to_calendar(
    service: CalendarService,
    exams: list[CalendarEventRequest],
    calendarId: str,
) -> AddEventsResponse:
    for exam in exams:
        check = _check_conflict(service, exam, calendarId)
        if check:
            confirmation = input("Do you want to add event anyways? (y/n): ")
            if confirmation.lower() != "y":
                print("Skipping event")
                continue

        try:
            service.events().insert(calendarId=calendarId, body=exam.model_dump()).execute()
        except Exception as e:
            return AddEventsResponse(code=500, message=str(e), event=exam)

    return AddEventsResponse(code=200, message="Events added successfully")


def _check_conflict(service: CalendarService, event: CalendarEventRequest, calendarId: str) -> bool:
    start_time_isoformat = (event.start.dateTime - dt.timedelta(hours=1)).isoformat() + "+03:00"
    start_time_datetime = event.start.dateTime.timestamp()
    end_time_datetime = event.end.dateTime.timestamp()

    calendar_events = (
        service.events()
        .list(
            calendarId=calendarId,
            timeMin=start_time_isoformat,
            maxResults=1,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    if not calendar_events:
        return False

    for calendar_event in calendar_events["items"]:
        calendar_event = CalendarEventResponse.model_validate(calendar_event)
        calendar_event_start_time = calendar_event.start.dateTime.timestamp()
        calendar_event_end_time = calendar_event.end.dateTime.timestamp()

        if start_time_datetime < calendar_event_end_time and end_time_datetime > calendar_event_start_time:
            print_error(f"Event {event.summary} conflicts with event {calendar_event.summary}")
            return True

        if start_time_datetime == calendar_event_start_time and end_time_datetime == calendar_event_end_time:
            print_error(f"Event {event.summary} conflicts with event {calendar_event.summary}")
            return True

        if start_time_datetime > calendar_event_start_time and end_time_datetime < calendar_event_end_time:
            print_error(f"Event {event.summary} conflicts with event {calendar_event.summary}")
            return True

    return False
