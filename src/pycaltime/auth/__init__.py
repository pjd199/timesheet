"""Authentication blueprint."""

from flask_dance.contrib.google import make_google_blueprint

from pycaltime.config import config

google_blueprint = make_google_blueprint(
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
    redirect_to="dashboard.home",
)
