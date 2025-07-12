"""Dashboard blueprint package."""

from flask import Blueprint

dashboard_blueprint = Blueprint("dashboard", __name__, template_folder="templates")

# import views to bind routes to blueprint
from . import about, home, mileage, settings, timesheet  # noqa: E402, F401
