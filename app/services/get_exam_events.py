import datetime as dt
import re

from commons import print_error, print_success
from pandas import DataFrame
from schema import CalendarEventRequest, EventDateTime


def get_exam_events(major: str, level: int, exam_table: DataFrame) -> list[CalendarEventRequest]:
    # find all rows where the major
    major_level_rows = exam_table[
        (exam_table["Offered to"].str.contains(major, case=False)) & (exam_table["Level"].str.contains(str(level)))
    ]

    events: list[CalendarEventRequest] = []
    for index, row in major_level_rows.iterrows():
        # Parse the "Level" column
        level_match = re.search(r"(\d+)(?:\s+for\s+(\w+))?", row["Level"])
        if level_match:
            row_level = int(level_match.group(1))
            row_major = level_match.group(2)

            # Check if the level matches, or if it's a special case (e.g., "7 for AI")
            if row_level != level or (row_major is not None and row_major.lower() != major.lower()):
                continue
        else:
            print_error("Unexpected level format")
            # If the level format is unexpected, skip this row
            continue

        date_time = f"{row['Date']} {row['Time']}"
        date_time_start = date_time.split("\r")[1].split(" to ")[0]
        date_time_end = date_time.split("\r")[1].split(" to ")[1]

        # if there is a space between hours and minutes, remove it

        date_time_start = date_time_start.replace(" ", "")
        date_time_end = date_time_end.replace(" ", "")

        dt_obj_start = dt.datetime.strptime(date_time_start, "%d/%m/%Y%H:%M")
        dt_obj_end = dt.datetime.strptime(date_time_end, "%H:%M")
        dt_obj_end = dt_obj_start.replace(hour=dt_obj_end.hour, minute=dt_obj_end.minute)

        title = f"{row['Course code']} - {row['Course name']} Exam"

        event = CalendarEventRequest(
            summary=title,
            start=EventDateTime(dateTime=dt_obj_start, timeZone="Africa/Cairo"),
            end=EventDateTime(dateTime=dt_obj_end, timeZone="Africa/Cairo"),
        )
        events.append(event)
    if len(events) == 0:
        print_error("No exams found")
        exit()

    print_success(f"Found {len(events)} events")
    for event in events:
        print(f"{event.summary} - {event.start.dateTime} - {event.end.dateTime}")

    return events
