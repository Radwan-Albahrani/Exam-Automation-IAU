from commons import (
    authorize_and_return_service,
    get_exams_table,
    get_major_and_level,
    print_error,
    print_success,
)
from schema import CalendarEventRequest
from services.add_exams_to_calendar import add_exams_to_calendar
from services.add_exams_to_ics_calendar import add_exams_to_ics_calendar
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

    try:
        service = authorize_and_return_service()
        if service is None:
            print_error("Failed to authorize. Service not found")
            ics_instead = input("Do you want to generate an ICS file instead? (y/n): ")
            if ics_instead.lower() == "y":
                return add_exams_to_ics_calendar(exams=events)
            else:
                print("Aborted")
                return
    except Exception as e:
        print(f"Failed to Authorize: {e}")
        ics_instead = input("Do you want to generate an ICS file instead? (y/n): ")
        if ics_instead.lower() == "y":
            return add_exams_to_ics_calendar(exams=events)
        else:
            print("Aborted")
            return

    return google_calendar_flow(
        events=events,
        service=service,
    )


def google_calendar_flow(events, service):
    selected_calendar = get_specific_calendar(
        service=service,
    )

    if selected_calendar is None:
        print_error("Failed to find the exams calendar")
        print("Would you like to generate an ICS file instead?")
        ics_instead = input("Do you want to generate an ICS file instead? (y/n): ")
        if ics_instead.lower() == "y":
            return add_exams_to_ics_calendar(exams=events)
        else:
            print("Aborted")
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
