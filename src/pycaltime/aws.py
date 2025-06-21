"""AWS Lambda Handler."""

from apig_wsgi import make_lambda_handler

from pycaltime.app import create_app

# WSGI entry point for AWS Lambda functions
lambda_handler = make_lambda_handler(create_app())
