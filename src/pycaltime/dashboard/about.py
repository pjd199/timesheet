"""Dashboard about."""

from os import environ
from sys import version_info

from flask import redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_dance.contrib.google import google

from pycaltime import __version__
from pycaltime.dashboard import dashboard_blueprint


@dashboard_blueprint.route("about")
def about() -> ResponseReturnValue:
    """Dashboard about."""
    if not google.authorized or google.token["expires_in"] < 0:
        return redirect(url_for("google.login"))

    return render_template(
        "about.html",
        python_version=f"{version_info.major}.{version_info.minor}",
        build_version=__version__,
        aws_lambda="AWS_LAMBDA_FUNCTION_NAME" in environ,
        hostname=request.host,
    )
