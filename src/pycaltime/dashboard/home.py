"""Dashboard home."""

from flask import redirect, render_template, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime.dashboard import dashboard_blueprint
from pycaltime.google import get_user_info
from pycaltime.storage import UserData


@dashboard_blueprint.route("home")
def home() -> ResponseReturnValue:
    """Dashboard home."""
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    user_info = get_user_info()
    list(UserData.query(user_info.id)).pop()
    return render_template("home.html", given_name=user_info.given_name)
