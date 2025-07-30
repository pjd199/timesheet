"""Dashboard home."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import redirect, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.calendar import update_timesheets
from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import get_calendar_timezone, get_user_info
from pycaltime.storage import UserData
from pycaltime.utils import first_day_of_the_week


@dashboard_blueprint.route("home")
def home() -> ResponseReturnValue:
    """Dashboard home."""
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    user_info = get_user_info()
    user_data = list(UserData.query(user_info.id)).pop()
    timezone = get_calendar_timezone()
    current_week = first_day_of_the_week(datetime.now(tz=ZoneInfo(timezone)).date())

    # update with recent calendar data
    update_timesheets(
        current_week - timedelta(weeks=user_data.view_past_weeks),
        current_week + timedelta(weeks=user_data.view_future_weeks + 1),
        user_data,
    )
    user_data.save()

    return render_template(
        "home.html",
        given_name=user_info.given_name,
        user_data=user_data,
        current_week=current_week,
    )
