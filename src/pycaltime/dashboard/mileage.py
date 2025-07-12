"""Milage view."""

from datetime import UTC, date, datetime

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


@dashboard_blueprint.route("/mileage")
def mileage() -> ResponseReturnValue:
    """Mileage.

    Returns:
        ResponseReturnValue: the rendered page
    """
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    user_id = get_user_info().id
    user_data = list(UserData.query(user_id)).pop()
    hashtags = {job.hashtag for job in user_data.jobs if job.hashtag}

    start = (
        date.fromisoformat(request.args["start"])
        if "start" in request.args
        else datetime.now(UTC).date().replace(day=1)
    )

    # get events
    location_events = [
        event
        for event in iterate_events(start, start.replace(month=start.month + 1))
        if event.location and event.hashtags() & hashtags
    ]

    # create the table headers
    titles = [
        ("event", "Event"),
        ("date", "Date"),
        ("location", "Location"),
        ("distance", "Trip"),
    ]

    # create the table data
    data = []
    origin = "217 St Leonards Road, Horsham, RH13 6BE"
    distances = get_distances(origin, location_events)

    for event, distance in zip(location_events, distances):
        if distance > 0:
            row = {
                "event": event.title,
                "date": event.start.strftime("%d-%m-%Y"),
                "location": event.location,
                "distance": f"{round(distance * 0.000621 * 2)}",
            }
            data.append(row)

    return render_template(
        "mileage.html",
        month=start.strftime("%B"),
        data=data,
        titles=titles,
        primary_key="date",
    )
