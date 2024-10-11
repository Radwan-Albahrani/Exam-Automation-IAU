import datetime as dt

import ics
from commons import print_success
from schema import CalendarEventRequest


def add_exams_to_ics_calendar(exams: list[CalendarEventRequest]):
    calendar = ics.Calendar()
    for exam in exams:
        event = ics.Event()
        event.name = exam.summary
        event.begin = exam.start.dateTime.astimezone(dt.timezone.utc).replace(tzinfo=None)
        event.end = exam.end.dateTime.astimezone(dt.timezone.utc).replace(tzinfo=None)
        event.location = exam.location
        event.description = exam.description
        calendar.events.add(event)

    with open("calendar.ics", "w") as f:
        f.writelines(calendar.serialize_iter())

    print_success("ICS file generated successfully")
