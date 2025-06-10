from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from os import environ
from zoneinfo import ZoneInfo
from pprint import pprint
from re import findall, match
from typing import Any
from collections import deque
from itertools import pairwise, groupby, permutations

import googleapiclient.discovery
from flask import Flask, redirect, url_for, render_template
from flask_dance.contrib.google import google, make_google_blueprint
from google.oauth2 import credentials
from werkzeug.middleware.proxy_fix import ProxyFix


environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "0"  # noqa: S105


# Load secrets
FLASK_SECRET_KEY = environ.get("FLASK_SECRET_KEY")
GOOGLE_CLIENT_ID = environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = environ.get("GOOGLE_CLIENT_SECRET")


@dataclass
class WeeklySummary:
    start_date: datetime
    tag: str
    work: int = 0
    holiday: int = 0
    bank: int = 0
    sick: int = 0

    def total(self):
        return self.work + self.holiday + self.bank + self.sick


@dataclass
class ProjectInfo:
    tag: str
    name: str
    short_name: str


@dataclass
class CalendarEvent:
    title: str
    description: str
    location: str
    start: datetime
    finish: datetime

    def duration(self):
        return (self.finish - self.start) // timedelta(minutes=1)

    def hashtags(self):
        return frozenset(findall(r"#\w+", f"{self.title} {self.description}"))


# Initialize Flask
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = FLASK_SECRET_KEY
blueprint = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
)
app.register_blueprint(blueprint, url_prefix="/login")


def get_calendar_list():
    """
    Retrieves a list of calendars for the authenticated user.
    Requires the https://www.googleapis.com/auth/calendar.readonly scope.
    """
    if not google.authorized:
        return None, "Not authorized to access Google Calendar."

    try:
        # Get the credentials from the google object
        creds = credentials.Credentials(
            google.access_token,
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )

        # Build the Calendar API service.
        service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)

        # Call the Calendar API to list calendars.
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get("items", []), None
    except Exception as e:
        return None, f"Error retrieving calendar list: {e}"


def get_calendar_timezone(calendar_id: str, default: str):
    """
    Retrieves a list of calendars for the authenticated user.
    Requires the https://www.googleapis.com/auth/calendar.readonly scope.
    """
    # Get the credentials from the google object
    creds = credentials.Credentials(
        google.access_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    # Build the Calendar API service.
    service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)

    # Call the Calendar API to list calendars.
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get("items", []):
        if calendar.get("primary", False):
            return calendar.get("timeZone", default)
    return default


def first_day_of_the_week(timestamp: datetime) -> datetime:
    days_to_monday = timestamp.weekday()
    monday = timestamp - timedelta(days=days_to_monday)
    return datetime(monday.year, monday.month, monday.day, tzinfo=timestamp.tzinfo)


def first_day_of_the_week_grouper(event: CalendarEvent) -> datetime:
    return first_day_of_the_week(event.start)


def iterate_events(
    start: datetime, finish: datetime, calendar_id: str
) -> Iterator[CalendarEvent]:
    # Get the credentials from the google object
    creds = credentials.Credentials(
        google.access_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )

    service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)

    # Get the current time
    print(f"Iterating events from {start.isoformat()} to {finish.isoformat()}")

    next_page_token = None
    # Call the Calendar API to get events
    while True:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start.isoformat(),
                timeMax=finish.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                pageToken=next_page_token,
                maxResults=500,
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


def summerize_weeks(
    start: datetime,
    finish: datetime,
    projects: list[str],
    calendar_id: str,
):
    # create the results structure
    start_of_the_week = first_day_of_the_week(start)
    num_weeks = ((finish - start_of_the_week).days // 7) + 1

    results = {
        start_of_the_week
        + timedelta(weeks=i): {
            project: WeeklySummary(start_of_the_week + timedelta(weeks=i), project)
            for project in projects
        }
        for i in range(num_weeks)
    }

    # for start_of_the_week, events in group_events_by_week(start, end, calendar_id):
    for start_of_the_week, group in groupby(
        iterate_events(start, finish, calendar_id), key=first_day_of_the_week_grouper
    ):

        events = list(group)

        # process buffer events
        buffer_events = [
            event
            for event in events
            if ("travel" in event.title or "decompress" in event.title)
            and "reclaim" in event.description
        ]
        buffer_events_start = {x.start: x for x in buffer_events}
        buffer_events_finish = {x.finish: x for x in buffer_events}
        for event in events:
            if event.location or (
                "teams.microsoft.com" in event.description
                or "zoom.us" in event.description
            ):
                if event.start in buffer_events_finish:
                    buffer_event = buffer_events_finish.pop(event.start)
                    buffer_events_start.pop(buffer_event.finish, None)
                    buffer_event.title += "".join(projects & event.hashtags())
                if event.finish in buffer_events_start:
                    buffer_event = buffer_events_start.pop(event.finish)
                    buffer_events_finish.pop(buffer_event.start, None)
                    buffer_event.title += "".join(projects & event.hashtags())

        # process events
        for event in events:
            # extract event information
            for project in projects & event.hashtags():
                #print(f"{event.title} - {''.join(event.hashtags())} - {event.duration()}")
                if "#holiday" in event.hashtags():
                    results[start_of_the_week][project].holiday += event.duration()
                elif "#bank" in event.hashtags():
                    results[start_of_the_week][project].bank += event.duration()
                elif "#sick" in event.hashtags():
                    results[start_of_the_week][project].sick += event.duration()
                else:
                    results[start_of_the_week][project].work += event.duration() // len(
                        projects & event.hashtags()
                    )
    return results


@app.route("/")
def index():
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text

    data = resp.json()

    calendar_id = "primary"
    calendar_timezone = get_calendar_timezone(calendar_id, default="Europe/London")

    #
    # use timezone seetings from calendar
    #
    projects = {"#hct", "#life"}
    project_info = {
        "#hct": ProjectInfo("#hct", "Horsham Church Together", "HCT"),
        "#life": ProjectInfo("#life", "Life Community Baptist Church", "LIFE"),
    }

    start = datetime(2025, 4, 28, tzinfo=ZoneInfo(calendar_timezone))
    results = summerize_weeks(
        start,
        start + timedelta(weeks=1),
        projects,
        calendar_id,
    )

    # create the table
    data = [
        {"date": start_of_the_week}
        | {project: results[start_of_the_week][project].total() for project in projects}
        for start_of_the_week in results
    ]
    return render_template(
        "table.html", projects=sorted(projects), project_info=project_info, data=data
    )

if __name__ == "__main__":
    app.run()
