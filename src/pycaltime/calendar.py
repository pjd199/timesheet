from dataclasses import dataclass
from datetime import datetime, timedelta, date
from re import findall
from pycaltime.storage import Timesheet, UserData

from itertools import groupby
from pycaltime.google import iterate_events, CalendarEvent


def first_day_of_the_week(t: date) -> date:
    return t - timedelta(days=t.weekday())

def iterate_weeks(start: date, finish: date):
    result = start
    while result < finish:
        yield result
        result += timedelta(weeks=1)


def summerize_weeks(
    start: date,
    finish: date,
    user_data: UserData,
):
    job_hashtags = {job.hashtag for job in user_data.jobs}
    job_for_hashtag = {job.hashtag: job for job in user_data.jobs}

    # for start_of_the_week, events in group_events_by_week(start, end, calendar_id):
    for week, group in groupby(
        iterate_events(start, finish),
        key=lambda x: first_day_of_the_week(x.start.date()),
    ):

        events = list(group)
        for job in user_data.jobs:
            job.timesheets[week] = Timesheet()

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
                    buffer_event.title += "".join(job_hashtags & event.hashtags())
                if event.finish in buffer_events_start:
                    buffer_event = buffer_events_start.pop(event.finish)
                    buffer_events_finish.pop(buffer_event.start, None)
                    buffer_event.title += "".join(job_hashtags & event.hashtags())

        # process events
        for event in events:
            # extract event information
            for x in job_hashtags & event.hashtags():
                if "#holiday" in event.hashtags():
                    job_for_hashtag[x].timesheets[week].holiday += event.duration()
                elif "#bank" in event.hashtags():
                    job_for_hashtag[x].timesheets[week].bank += event.duration()
                elif "#sick" in event.hashtags():
                    job_for_hashtag[x].timesheets[week].sick += event.duration()
                else:
                    job_for_hashtag[x].timesheets[week].work += event.duration() // len(
                        job_hashtags & event.hashtags()
                    )
