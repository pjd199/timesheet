"""Timesheet blueprint."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, redirect, render_template, session, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.calendar import first_day_of_the_week, update_timesheets
from pycaltime.google import get_calendar_timezone
from pycaltime.storage import UserData

show_timesheet = Blueprint("show_timesheet", __name__, template_folder="templates")


@show_timesheet.route("/show")
def show() -> ResponseReturnValue:
    """Show timesheet.

    Returns:
        ResponseReturnValue: _description_
    """
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    calendar_timezone = get_calendar_timezone()
    current_week = first_day_of_the_week(
        datetime.now(tz=ZoneInfo(calendar_timezone)).date()
    )

    user_id = session.get("user_id")
    user_data = list(UserData.query(user_id)).pop()

    # update with recent calendar data
    update_timesheets(
        current_week - timedelta(weeks=user_data.view_past_weeks),
        current_week + timedelta(weeks=user_data.view_future_weeks + 1),
        user_data,
    )
    user_data.last_updated = datetime.now(tz=ZoneInfo(calendar_timezone))
    user_data.save()

    # cacluate flexi time
    for job in user_data.jobs:
        flexi = 0
        if job.short_name == "HCT":  ### temporary fix!!!
            flexi += 980
        for week, timesheet in job.timesheets.items():
            if job.employment_start.date() <= week < job.employment_end.date():
                timesheet.balance = timesheet.total() - int(job.contracted_hours * 60)
                flexi += timesheet.balance
                timesheet.flexi = flexi
            else:
                timesheet.flexi = 0
                timesheet.balance = 0

    # render the table
    weeks_to_display = [
        (current_week + timedelta(weeks=x))
        for x in range(-user_data.view_past_weeks, user_data.view_future_weeks + 1)
    ]
    return render_template(
        "show.html",
        user_data=user_data,
        weeks=weeks_to_display,
        this_week=current_week,
    )
