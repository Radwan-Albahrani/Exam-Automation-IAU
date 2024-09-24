from commons import (
    authorize_and_return_service,
    get_exams_table,
    get_major_and_level,
    print_error,
    print_success,
)
from schema import CalendarEventRequest
from services.add_exams_to_calendar import add_exams_to_calendar
from services.get_exam_events import get_exam_events
from services.get_specific_calendar import get_specific_calendar


def main():

    file_path = input("Enter the path of the exams pdf file: ")
    exam_table = get_exams_table(file_path=file_path)

    major, level = get_major_and_level()

    events: list[CalendarEventRequest] = get_exam_events(
        major=major,
        level=level,
        exam_table=exam_table,
    )

    confirm = input("Do you want to add these events to the calendar? (y/n): ")
    if confirm.lower() != "y":
        print_error("Aborted")
        return

    calendar_name = input("Enter the name of the calendar to add the events to: ")
    service = authorize_and_return_service()
    if service is None:
        print_error("Failed to authorize")
        return

    selected_calendar = get_specific_calendar(
        service=service,
        calendar_name=calendar_name,
    )

    if selected_calendar is None:
        print_error("Failed to find the exams calendar")
        return

    response = add_exams_to_calendar(
        service=service,
        exams=events,
        calendarId=selected_calendar.id,
    )

    if response.code == 200:
        print_success("Events added successfully")
    else:
        print_error(f"Failed to add events: {response.message}")


if __name__ == "__main__":
    main()
