"""Milage view."""

from datetime import UTC, date, datetime
from itertools import groupby
from re import match

from flask import redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.bank_holidays import bank_holidays
from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import (
    get_user_info,
    iterate_events,
)
from pycaltime.storage import UserData


@dashboard_blueprint.route("/holiday")
def holiday() -> ResponseReturnValue:
    """Holiday view.

    Returns:
        ResponseReturnValue: the rendered page
    """
    # check user is logged in
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    # handle the year parameter
    if "year" in request.args and match(r"\d{4}", request.args["year"]):
        year = int(request.args["year"])
    else:
        year = datetime.now(UTC).date().year

    # load user data
    user_id = get_user_info().id
    user_data = list(UserData.query(user_id)).pop()
    job_hashtags = {job.hashtag for job in user_data.jobs}
    holiday_events = (
        event
        for event in iterate_events(date(year, 1, 1), date(year + 1, 1, 1))
        if {"#holiday", "#bank"} & event.hashtags()
    )

    # create the table headers
    titles = (
        [("date", "Date")]
        + [
            (f"{job.hashtag}-#holiday", f"{job.short_name} hols")
            for job in user_data.jobs
        ]
        + [(f"{job.hashtag}-#bank", f"{job.short_name} bank") for job in user_data.jobs]
        + [("total", "Total")]
    )

    # create the table data
    data = []
    col_totals = {f"{job.hashtag}-#holiday": 0.0 for job in user_data.jobs} | {
        f"{job.hashtag}-#bank": 0.0 for job in user_data.jobs
    }
    for day, group in groupby(
        holiday_events,
        key=lambda x: x.start.date(),
    ):
        row = (
            {"date": f"{day}", "total": 0.0}
            | {f"{job.hashtag}-#holiday": 0.0 for job in user_data.jobs}
            | {f"{job.hashtag}-#bank": 0.0 for job in user_data.jobs}
        )
        for event in group:
            for job_hashtag in job_hashtags & event.hashtags():
                for type_tag in {"#holiday", "#bank"} & event.hashtags():
                    row[f"{job_hashtag}-{type_tag}"] += event.duration() / 60
                    col_totals[f"{job_hashtag}-{type_tag}"] += event.duration() / 60
                    row["total"] += event.duration() / 60
        data.append(row)

    data.append({"date": "Total", "total": sum(col_totals.values())} | col_totals)

    bank_holidays_this_year = len(bank_holidays(year))

    # Calculate the remaining allowance
    data.append(
        {"date": "Used"}
        | {
            f"{job.hashtag}-#holiday": str(col_totals[f"{job.hashtag}-#holiday"])
            + f" / {job.contracted_hours * 5.6:.01f}"
            for job in user_data.jobs
        }
        | {
            f"{job.hashtag}-#bank": str(col_totals[f"{job.hashtag}-#bank"])
            + f" / {
                ((job.contracted_hours / 37.5)
                 if job.pro_rata_bank_holiday else 1) * (bank_holidays_this_year * 7.5)
            }"
            for job in user_data.jobs
        }
    )

    # annual_holiday_hours = NumberAttribute()
    # pro_rata_bank_holiday = BooleanAttribute()

    # render the temple
    return render_template(
        "holiday.html",
        title=f"{year} Holiday",
        data=data,
        titles=titles,
        primary_key="date",
        highlight="Total",
        prev=url_for(
            request.endpoint,
            year=f"{year-1}",
        ),
        next=url_for(
            request.endpoint,
            year=f"{year+1}",
        ),
    )
