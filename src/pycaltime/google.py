"""Google API Interface."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from re import findall
from typing import Any
from zoneinfo import ZoneInfo

import googleapiclient.discovery
from flask_dance.contrib.google import google
from google.oauth2 import credentials

from pycaltime.config import config
from pycaltime.utils import include_from_dict


@include_from_dict
@dataclass
class UserInfo:
    """UserInfo from Google API."""

    id: str
    name: str
    given_name: str
    family_name: str
    email: str
    verified_email: bool


@dataclass
class CalendarEvent:
    """Calendar Event."""

    title: str
    description: str
    location: str
    start: datetime
    finish: datetime

    def duration(self) -> int:
        """Event duration, in minutes.

        Returns:
            int: minutes
        """
        return (self.finish - self.start) // timedelta(minutes=1)

    def hashtags(self) -> frozenset[str]:
        """Retrieve hashtags from the event.

        Returns:
            frozenset[str]: hashtags
        """
        return frozenset(findall(r"#\w+", f"{self.title} {self.description}"))


def api_service() -> None:
    """API service."""
    creds = credentials.Credentials(
        google.access_token,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    # Build the Calendar API service.
    return googleapiclient.discovery.build("calendar", "v3", credentials=creds)


def get_user_info() -> UserInfo:
    """User Information."""
    resp = google.get("/oauth2/v2/userinfo")
    data = resp.json()
    print(f"Loading userinfo {data}")
    return UserInfo.from_dict(data)


def get_calendar_list() -> list[Any]:
    """Retrieves a list of calendars for the authenticated user.

    Returns:
        list[Any]: calendar list
    """
    calendar_list = api_service().calendarList().list().execute()
    return calendar_list.get("items", [])


def get_calendar_timezone(calendar_id: str = "primary") -> str:
    """Get the timezone of the primary calendar."""
    calendar_list = api_service().calendarList().list().execute()
    return next(
        calendar.get("timeZone")
        for calendar in calendar_list.get("items", [])
        if calendar.get(calendar_id, False)
    )


def iterate_events(
    start: date, finish: date, calendar_id: str = "primary"
) -> Iterator[CalendarEvent]:
    """Iterator calendar events from the API.

    Args:
        start (date): start date
        finish (date): end date
        calendar_id (str, optional): calendar id. Defaults to "primary".

    Yields:
        CalendarEvent: the events
    """
    calendar_timezone = get_calendar_timezone()
    next_page_token = None
    # Call the Calendar API to get events
    while True:
        events_result = (
            api_service()
            .events()
            .list(
                calendarId=calendar_id,
                timeMin=datetime.combine(
                    start, time(), tzinfo=ZoneInfo(calendar_timezone)
                ).isoformat(),
                timeMax=datetime.combine(
                    finish, time(), tzinfo=ZoneInfo(calendar_timezone)
                ).isoformat(),
                singleEvents=True,
                orderBy="startTime",
                pageToken=next_page_token,
            )
            .execute()
        )

        yield from (
            CalendarEvent(
                title=x.get("summary", "").lower(),
                description=x.get("description", "").lower(),
                location=x.get("location", "").lower(),
                start=datetime.fromisoformat(x.get("start").get("dateTime")),
                finish=datetime.fromisoformat(x.get("end").get("dateTime")),
            )
            for x in events_result.get("items", [])
            if x.get("start").get("dateTime") is not None  # ignore all day events
        )

        # handle paging
        next_page_token = events_result.get("nextPageToken")
        if not next_page_token:
            break  # Exit loop if there are no more pages
