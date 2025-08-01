"""Timesheet blueprint."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import redirect, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.calendar import first_day_of_the_week, update_timesheets
from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import get_calendar_timezone, get_user_info
from pycaltime.storage import UserData
from pycaltime.utils import date_range


@dashboard_blueprint.route("/timesheet")
def timesheet() -> ResponseReturnValue:
    """Timesheet.

    Returns:
        ResponseReturnValue: _description_
    """
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    user_id = get_user_info().id
    timezone = get_calendar_timezone()
    current_week = first_day_of_the_week(datetime.now(tz=ZoneInfo(timezone)).date())
    user_data = list(UserData.query(user_id)).pop()

    # update with recent calendar data
    update_timesheets(
        current_week - timedelta(weeks=user_data.view_past_weeks),
        current_week + timedelta(weeks=user_data.view_future_weeks + 1),
        user_data,
    )
    user_data.save()

    # create the table headers
    titles = [("date", "Date")]
    for job in user_data.jobs:
        titles.append((f"{job.hashtag}-hours", job.short_name))
        titles.append((f"{job.hashtag}-diff", "+/-"))
        titles.append((f"{job.hashtag}-flexi", "flexi"))
    titles.append(("total", "Total"))

    # create the table data
    data = []
    weeks = date_range(
        current_week - timedelta(weeks=user_data.view_past_weeks),
        current_week + timedelta(weeks=user_data.view_future_weeks + 1),
        timedelta(weeks=1),
    )
    for week in weeks:
        row = {"date": week.strftime("%d-%m-%Y")}
        weekly_total = 0
        for job in user_data.jobs:
            total = job.timesheets[week].total() / 60
            weekly_total += total
            diff = total - job.contracted_hours
            flexi = job.timesheets[week].flexi / 60
            row[f"{job.hashtag}-hours"] = f"{total:.2f}"
            row[f"{job.hashtag}-diff"] = f"{diff:+.2f}"
            row[f"{job.hashtag}-flexi"] = f"{flexi:.2f}"
        row["total"] = f"{weekly_total:.2f}"
        data.append(row)

    return render_template(
        "timesheet.html",
        data=data,
        titles=titles,
        primary_key="date",
        highlight=current_week.strftime("%d-%m-%Y"),
    )
