from pydantic import BaseModel, Field


class EventAttendee(BaseModel):
    email: str
    displayName: str | None = None


class EventDateTime(BaseModel):
    dateTime: str
    timeZone: str


class CalendarEventRequest(BaseModel):
    summary: str
    location: str | None = None
    description: str | None = None
    start: EventDateTime
    end: EventDateTime
    attendees: list[EventAttendee] | None = Field(default_factory=list)


class CalendarEventResponse(CalendarEventRequest):
    class Creator(BaseModel):
        email: str

    class Organizer(BaseModel):
        email: str
        displayName: str

    class Reminders(BaseModel):
        useDefault: bool

    kind: str
    etag: str
    id: str
    status: str
    htmlLink: str
    created: str
    updated: str
    reminders: Reminders
    creator: Creator
    organizer: Organizer


class CalendarsRequest(BaseModel):
    summary: str
    description: str | None = None
    location: str | None = None
    timeZone: str


class CalendarsResponse(CalendarsRequest):
    kind: str
    etag: str
    id: str
    conferenceProperties: dict[str, list[str]] | None = None


class AddEventsResponse(BaseModel):
    code: int
    message: str
    event: CalendarEventRequest | None = None
