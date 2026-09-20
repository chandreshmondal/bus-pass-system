import os
from datetime import timedelta

def _get_database_uri():
    uri = os.environ.get("DATABASE_URL", "sqlite:///bus_pass.db")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


class Config:
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-secret-key")
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-flask-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)