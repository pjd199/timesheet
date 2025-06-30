"""Dashboard home."""

from flask import redirect, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import get_user_info
from pycaltime.storage import UserData


@dashboard_blueprint.route("settings")
def settings() -> ResponseReturnValue:
    """Dashboard settings."""
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    user_info = get_user_info()
    user_data = list(UserData.query(user_info.id)).pop()
    return render_template("settings.html", user_info=user_info, user_data=user_data)
