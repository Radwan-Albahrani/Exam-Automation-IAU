import datetime as dt

from commons import print_error, print_success
from pandas import DataFrame
from schema import CalendarEventRequest, EventDateTime


def get_exam_events(major: str, level: int, exam_table: DataFrame) -> list[CalendarEventRequest]:
    # find all rows where the major

    print(exam_table)

    major_level_rows = exam_table[
        (exam_table["Offered to"].str.contains(major, case=False))
        & (
            exam_table[exam_table.columns[exam_table.columns.str.contains("level", case=False)]]
            .astype(str)
            .apply(lambda x: x.str.contains(str(level)))
            .any(axis=1)
        )
    ]

    events: list[CalendarEventRequest] = []
    for index, row in major_level_rows.iterrows():
        level_column = next(col for col in major_level_rows.columns if "level" in col.lower())

        level_string: str = row[level_column]
        if len(level_string) > 1:
            # index of first digit that matches level
            level_index = level_string.find(str(level))

            # find the index of the next digit, or the end of the string
            next_digit_index = level_index + 1
            while next_digit_index < len(level_string) and not level_string[next_digit_index].isdigit():
                next_digit_index += 1

            substring_in_between = level_string[level_index + 1 : next_digit_index]
            if major.lower() not in substring_in_between.lower():
                continue

        date_time = f"{row['Date']}"
        date_time_date = dt.datetime.strptime(date_time, "%A %d/%m/%Y")
        date_time_start = row["Time"].split(" to ")[0]
        date_time_end = row["Time"].split(" to ")[1]

        # if there is a space between hours and minutes, remove it

        date_time_start = date_time_start.replace(" ", "")
        date_time_end = date_time_end.replace(" ", "")

        dt_obj_start = dt.datetime.strptime(date_time_start, "%H:%M")
        dt_obj_start = date_time_date.replace(hour=dt_obj_start.hour, minute=dt_obj_start.minute)
        dt_obj_end = dt.datetime.strptime(date_time_end, "%H:%M")
        dt_obj_end = date_time_date.replace(hour=dt_obj_end.hour, minute=dt_obj_end.minute)
        print(dt_obj_start > dt_obj_end)
        print(dt_obj_start, dt_obj_end)
        if dt_obj_start > dt_obj_end:
            dt_obj_end = dt_obj_end.replace(hour=dt_obj_end.hour + 12)

        dt_obj_end = date_time_date.replace(hour=dt_obj_end.hour, minute=dt_obj_end.minute)

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
    print_success("============================= Events =============================")
    for event in events:
        print(f"{event.summary} - {event.start.dateTime} - {event.end.dateTime}")
    print_success("===============================================================")

    return events
