"""System configuration."""

from functools import cached_property
from json import loads
from os import environ

import boto3

# Required for Flash Dance - https://flask-dance.readthedocs.io/en/v0.8.0/quickstarts/google.html
environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "0"  # noqa: S105


class Config:
    """Configuration settings."""

    def __init__(self) -> None:
        """Initialize."""
        self.FLASK_SECRET_KEY = self.aws_secrets["FLASK_SECRET_KEY"]
        self.GOOGLE_CLIENT_ID = self.aws_secrets["GOOGLE_CLIENT_ID"]
        self.GOOGLE_CLIENT_SECRET = self.aws_secrets["GOOGLE_CLIENT_SECRET"]
        self.GOOGLE_MAPS_API_KEY = self.aws_secrets["GOOGLE_MAPS_API_KEY"]
        self.AWS_REGION = self.aws_secrets["AWS_REGION"]

    # FLASK_SECRET_KEY - Must be unique per installation
    # python -c 'import secrets; print(secrets.token_hex())'
    # '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'"""
    FLASK_SECRET_KEY = None

    # GOOGLE_CLIENT_ID - from the Google console
    GOOGLE_CLIENT_ID = None

    # GOOGLE_CLIENT_SECRET - from the Google console
    GOOGLE_CLIENT_SECRET = None

    # GOOGLE_MAPS_API_KEY - from the Google console
    GOOGLE_MAPS_API_KEY = None

    # AWS_REGION
    AWS_REGION = None

    @cached_property
    def aws_secrets(self) -> dict[str, str]:
        """Load secrets from AWS Secrets Manager.

        Returns:
            dict[str, str]: dictionary of secrets
        """
        region = environ.get("AWS_REGION") if "AWS_REGION" in environ else "eu-west-2"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=region)
        get_secret_value_response = client.get_secret_value(SecretId="pycaltime")

        return loads(get_secret_value_response["SecretString"]) | {"AWS_REGION": region}


config = Config()
