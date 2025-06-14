"""System configuration."""

from os import environ

# Required for Flash Dance - https://flask-dance.readthedocs.io/en/v0.8.0/quickstarts/google.html
environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "0"  # noqa: S105


class Config:
    """Configuration settings."""

    # FLASK_SECRET_KEY - Must be unique per installation
    # python -c 'import secrets; print(secrets.token_hex())'
    # '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'"""
    FLASK_SECRET_KEY = environ.get("FLASK_SECRET_KEY")

    # GOOGLE_CLIENT_ID - from the Google console
    GOOGLE_CLIENT_ID = environ.get("GOOGLE_CLIENT_ID")

    # GOOGLE_CLIENT_SECRET - from the Google console
    GOOGLE_CLIENT_SECRET = environ.get("GOOGLE_CLIENT_SECRET")

    # AWS_DEFAULT_REGION - from the AWS dynamo settings
    AWS_DEFAULT_REGION = environ.get("AWS_DEFAULT_REGION")


config = Config()
