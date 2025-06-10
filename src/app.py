from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, asdict
from datetime import date, timedelta, datetime
from itertools import groupby, pairwise, permutations
from os import environ
from pprint import pprint, pformat
from re import findall, match
from typing import Any
from zoneinfo import ZoneInfo
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from uuid import uuid4

import googleapiclient.discovery
from google.oauth2 import credentials


from flask import Flask, redirect, render_template, url_for, session
from flask_dance.contrib.google import google, make_google_blueprint

from werkzeug.middleware.proxy_fix import ProxyFix

from pycaltime.google import get_user_info, get_calendar_timezone, get_calendar_list
from pycaltime.calendar import summerize_weeks, first_day_of_the_week

from pycaltime.storage import UserData, JobData, Timesheet, TimesheetDict

environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "0"  # noqa: S105


from pycaltime.config import FLASK_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

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


@app.route("/")
def home():
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    weeks_history = 69
    weeks_future = 4
    calendar_timezone = get_calendar_timezone()
    current_week = first_day_of_the_week(
        datetime.now(tz=ZoneInfo(calendar_timezone)).date()
    )

    user_id = session.get("user_id", "")
    if not user_id:
        user_id = get_user_info().id
        session["user_id"] = get_user_info().id

    ##############################################
    # for user in UserData.scan():
    #     user.delete()
    ##############################################

    user_data_query = list(UserData.query(user_id))
    if user_data_query:
        print("user data found")
        user_data = user_data_query.pop()
    else:
        print("user data NOT found - creating UserData")
        user_info = get_user_info()
        user_data = UserData(
            id=user_info.id,
            email=user_info.email,
            given_name=user_info.given_name,
            family_name=user_info.family_name,
            jobs=[
                JobData(
                    hashtag="#hct",
                    name="Horsham Churches Together",
                    short_name="HCT",
                    contracted_hours=15,
                    annual_holiday_hours=15 * 5,
                    pro_rata_bank_holiday=True,
                    employment_start=datetime(
                        2024, 2, 12, tzinfo=ZoneInfo(calendar_timezone)
                    ),
                    employment_end=datetime(
                        9999, 12, 31, tzinfo=ZoneInfo(calendar_timezone)
                    ),
                    timesheets={},
                ),
                JobData(
                    hashtag="#life",
                    name="LIFE Community Baptist Church",
                    short_name="LIFE",
                    contracted_hours=22.5,
                    annual_holiday_hours=22.5 * 5,
                    pro_rata_bank_holiday=False,
                    employment_start=datetime(
                        2024, 2, 12, tzinfo=ZoneInfo(calendar_timezone)
                    ),
                    employment_end=datetime(
                        9999, 12, 31, tzinfo=ZoneInfo(calendar_timezone)
                    ),
                    timesheets={},
                ),
            ],
        )
        summerize_weeks(
            date(2024, 1, 1),
            current_week + timedelta(weeks=weeks_future),
            user_data,
        )

        # for job in user_data.jobs:
        #     if job.hashtag in results:
        #         q = results[job.hashtag]
        #         for week, timesheet in results[job.hashtag].items():
        #             job.timesheets[week] = timesheet
        user_data.save()

    print(f"USER: {user_data.id} ({user_data.email})")

    # print("Database Scan")
    # for x in UserData.scan():
    #     pprint(x)




###########################################################
    # summerize_weeks(
    #     current_week - timedelta(weeks=weeks_history),
    #     current_week + timedelta(weeks=weeks_future),
    #     user_data,
    # )
    # user_data.save()

    # cacluate flexi time
    for job in user_data.jobs:
        flexi = 0
        if job.short_name == "HCT":
            flexi +=  980
        for week, timesheet in job.timesheets.items():
            if job.employment_start.date() <= week < job.employment_end.date():
                timesheet.balance = timesheet.total() - int(job.contracted_hours * 60)
                flexi += timesheet.balance
                timesheet.flexi = flexi
            else:
                timesheet.flexi = 0
                timesheet.balance = 0

    # for job in user_data.jobs:
    #     for week, timesheet in iter(job.timesheets.items()):
    #         print(
    #             f"{job.short_name} {week} -> {timesheet.total()//60} - {timesheet.balance//60} - {timesheet.flexi//60} {timesheet}"
    #         )

    # render the table
    weeks_to_display = [
        (current_week + timedelta(weeks=x)) for x in range(-weeks_history, weeks_future)
    ]
    return render_template(
        "table.html",
        user_data=user_data,
        weeks=weeks_to_display,
        this_week=current_week,
    )


if __name__ == "__main__":
    app.run()
