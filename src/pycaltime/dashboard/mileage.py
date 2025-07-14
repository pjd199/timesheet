"""Milage view."""

from datetime import UTC, date, datetime
from re import match

from flask import redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import (
    get_distances,
    get_user_info,
    iterate_events,
)
from pycaltime.storage import UserData
from pycaltime.utils import (
    first_day_of_the_month,
    first_day_of_the_next_month,
    first_day_of_the_previous_month,
)


@dashboard_blueprint.route("/mileage")
def mileage() -> ResponseReturnValue:
    """Mileage. view.

    Returns:
        ResponseReturnValue: the rendered page
    """
    # check user is logged in
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    # load user data
    user_id = get_user_info().id
    user_data = list(UserData.query(user_id)).pop()

    # handle the month parameter
    if "month" in request.args and match(r"\d{4}-\d{2}-\d{2}", request.args["month"]):
        month = first_day_of_the_month(date.fromisoformat(request.args["month"]))
    else:
        month = first_day_of_the_month(datetime.now(UTC).date())

    # handle the filter parameter
    if (
        "filter" in request.args
        and request.args["filter"].isdigit()
        and 0 < int(request.args["filter"]) <= len(user_data.jobs)
    ):
        job_filter = int(request.args["filter"])
        hashtags = {user_data.jobs[job_filter - 1].hashtag}
    else:
        job_filter = 0
        hashtags = {job.hashtag for job in user_data.jobs if job.hashtag}

    # get the events for the month, and calculate distances
    location_events = [
        event
        for event in iterate_events(month, first_day_of_the_next_month(month))
        if event.location and event.hashtags() & hashtags
    ]
    origin = "217 St Leonards Road, Horsham, RH13 6BE"
    distances = get_distances(origin, location_events)

    # create the table headers
    titles = [
        ("event", "Event"),
        ("date", "Date"),
        ("location", "Location"),
        ("distance", "Trip"),
    ]

    # create the table data
    data = []
    for event, distance in zip(location_events, distances):
        if distance > 0:
            row = {
                "event": event.title,
                "date": event.start.strftime("%d-%m-%Y"),
                "location": event.location,
                "distance": f"{round(distance * 0.000621 * 2)}",
            }
            data.append(row)

    # render the temple
    return render_template(
        "mileage.html",
        month=month.strftime("%Y-%m-%d"),
        title=month.strftime("%B %Y"),
        data=data,
        titles=titles,
        primary_key="date",
        prev=url_for(
            request.endpoint,
            month=first_day_of_the_previous_month(month).isoformat(),
            filter=job_filter,
        ),
        next=url_for(
            request.endpoint,
            month=first_day_of_the_next_month(month).isoformat(),
            filter=job_filter,
        ),
        job_filter=["All Jobs", *(x.short_name for x in user_data.jobs)],
    )
