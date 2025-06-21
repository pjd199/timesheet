"""User Home Blueprint."""

from flask import Blueprint, redirect, url_for
from flask.typing import ResponseReturnValue

user_home_blueprint = Blueprint(
    "user_home_blueprint", __name__, template_folder="templates"
)


@user_home_blueprint.route("home")
def home() -> ResponseReturnValue:
    """User home."""
    return redirect(url_for("timesheet_blueprint.show"))
