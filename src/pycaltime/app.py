"""Flask App."""

from datetime import datetime, timezone
from typing import Any

from flask import Flask, send_from_directory
from flask.typing import ResponseReturnValue
from flask_bootstrap import Bootstrap5
from flask_dance.contrib.google import google
from werkzeug.middleware.proxy_fix import ProxyFix

from pycaltime import __version__
from pycaltime.auth import google_blueprint
from pycaltime.config import config
from pycaltime.dashboard.home import dashboard_blueprint
from pycaltime.storage import initialize_database


# Flask app factory
def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """App factory.

    Args:
        test_config (dict[str, Any] | None, optional): config. Defaults to None.

    Returns:
        Flask: application
    """
    # initialise flask
    app = Flask(__name__)
    app.config.from_mapping(test_config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.secret_key = config.FLASK_SECRET_KEY

    # initialise bookstrap
    app.config["BOOTSTRAP_BOOTSWATCH_THEME"] = "cerulean"
    bootstrap = Bootstrap5()
    bootstrap.init_app(app)

    # register blueprints
    app.register_blueprint(google_blueprint, url_prefix="/login")
    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")

    # initialise database
    initialize_database()

    @app.route("/")
    def home() -> ResponseReturnValue:
        return send_from_directory("static", "index.html")

    @app.context_processor
    def inject_globals() -> dict[str, str]:
        print(">>> inject <<<")
        return {
            "current_year": datetime.now(timezone.utc).year,
            "version": __version__,
            "authenticated": google.authorized or google.token["expires_in"] < 0,
        }

    print("App Created:")
    print(app.url_map)
    return app


# @app.route("/")
# def home() -> ResponseReturnValue:
#     """Home page."""
#     if not google.authorized or google.token["expires_in"] < 0:
#         return redirect(url_for("google.login"))

#     calendar_timezone = get_calendar_timezone()
#     current_week = first_day_of_the_week(
#         datetime.now(tz=ZoneInfo(calendar_timezone)).date()
#     )

#     user_id = session.get("user_id", "")
#     if not user_id:
#         user_id = get_user_info().id
#         session["user_id"] = get_user_info().id

#     ##############################################
#     # for user in UserData.scan():
#     #     user.delete()
#     ##############################################

#     user_data_query = list(UserData.query(user_id))
#     if user_data_query:
#         print("user data found")
#         user_data = user_data_query.pop()
#     else:
#         print("user data NOT found - creating UserData")
#         user_info = get_user_info()
#         user_data = UserData(
#             id=user_info.id,
#             email=user_info.email,
#             given_name=user_info.given_name,
#             family_name=user_info.family_name,
#             last_updated=datetime.now(tz=ZoneInfo(calendar_timezone)),
#             jobs=[
#                 JobData(
#                     hashtag="#hct",
#                     name="Horsham Churches Together",
#                     short_name="HCT",
#                     contracted_hours=15,
#                     annual_holiday_hours=15 * 5,
#                     pro_rata_bank_holiday=True,
#                     employment_start=datetime(
#                         2024, 2, 12, tzinfo=ZoneInfo(calendar_timezone)
#                     ),
#                     employment_end=datetime(
#                         9999, 12, 31, tzinfo=ZoneInfo(calendar_timezone)
#                     ),
#                     timesheets={},
#                 ),
#                 JobData(
#                     hashtag="#life",
#                     name="LIFE Community Baptist Church",
#                     short_name="LIFE",
#                     contracted_hours=22.5,
#                     annual_holiday_hours=22.5 * 5,
#                     pro_rata_bank_holiday=False,
#                     employment_start=datetime(
#                         2024, 2, 12, tzinfo=ZoneInfo(calendar_timezone)
#                     ),
#                     employment_end=datetime(
#                         9999, 12, 31, tzinfo=ZoneInfo(calendar_timezone)
#                     ),
#                     timesheets={},
#                 ),
#             ],
#         )
#         update_timesheets(
#             date(2024, 1, 1),
#             current_week + timedelta(weeks=user_data.view_future_weeks + 1),
#             user_data,
#         )
#         user_data.save()

#     print(f"USER: {user_data.id} ({user_data.email})")

#     # print("Database Scan")
#     # for x in UserData.scan():
#     #     pprint(x)

#     # update with recent calendar data
#     update_timesheets(
#         current_week - timedelta(weeks=user_data.view_past_weeks),
#         current_week + timedelta(weeks=user_data.view_future_weeks + 1),
#         user_data,
#     )
#     user_data.last_updated = datetime.now(tz=ZoneInfo(calendar_timezone))
#     user_data.save()

#     # cacluate flexi time
#     for job in user_data.jobs:
#         flexi = 0
#         if job.short_name == "HCT":  ### temporary fix!!!
#             flexi += 980
#         for week, timesheet in job.timesheets.items():
#             if job.employment_start.date() <= week < job.employment_end.date():
#                 timesheet.balance = timesheet.total() - int(job.contracted_hours * 60)
#                 flexi += timesheet.balance
#                 timesheet.flexi = flexi
#             else:
#                 timesheet.flexi = 0
#                 timesheet.balance = 0

#     # render the table
#     weeks_to_display = [
#         (current_week + timedelta(weeks=x))
#         for x in range(-user_data.view_past_weeks, user_data.view_future_weeks + 1)
#     ]
#     return render_template(
#         "table.html",
#         user_data=user_data,
#         weeks=weeks_to_display,
#         this_week=current_week,
#     )

if __name__ == "__main__":
    create_app().run()
