"""Google API Interface."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import batched
from re import findall
from typing import Any
from zoneinfo import ZoneInfo

import googleapiclient.discovery
import googlemaps
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
        return frozenset(
            findall(r"#\w+", f"{self.title.lower()} {self.description.lower()}")
        )

    def distance(self, origin: str) -> int:
        """Calculate distance from an origin address.

        Args:
            origin (str): the start location

        Returns:
            int: the distance, in meters
        """
        maps_client = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)
        matrix = maps_client.distance_matrix(
            origins=[origin],
            destinations=[self.location],
            arrival_time=self.start,
            mode="driving",
        )
        if not (
            matrix["status"] == "OK"
            and matrix["rows"][0]["elements"][0]["status"] == "OK"
        ):
            return 0
        return matrix["rows"][0]["elements"][0]["distance"]["value"]


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
                title=x.get("summary", ""),
                description=x.get("description", ""),
                location=x.get("location", ""),
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


def get_distances(origin: str, events: Iterable[CalendarEvent]) -> Iterable[int]:
    """Get distances to each event, starting from origin.

    Args:
        origin (str): _description_
        events (Iterable[CalendarEvent]): _description_

    Returns:
        Iterable[int]: _description_
    """
    maps_client = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)

    results = []
    for batch in batched(events, 25):
        matrix = maps_client.distance_matrix(
            origins=[origin],
            destinations=[event.location for event in batch],
            mode="driving",
        )
        if matrix["status"] != "OK":
            results.extend([0] * len(batch))

        results.extend(
            [
                x["distance"]["value"] if x["status"] == "OK" else 0
                for x in matrix["rows"][0]["elements"]
            ]
        )
    return results
