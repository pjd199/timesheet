"""Dashboard home."""

from flask import redirect, url_for
from flask.typing import ResponseReturnValue

from pycaltime.dashboard import dashboard_blueprint


@dashboard_blueprint.route("home")
def home() -> ResponseReturnValue:
    """Dashboard home."""
    return redirect(url_for("dashboard.timesheet"))
