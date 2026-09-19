import os

def _get_database_uri():
    uri = os.environ.get("DATABASE_URL", "sqlite:///bus_pass.db")
    # Render (and some other hosts) supply "postgres://", but SQLAlchemy 2.x
    # requires "postgresql://" - normalize it here.
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    return uri


class Config:
    # Uses Render's Postgres in production, falls back to local SQLite for
    # testing on your own machine without any extra setup.
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Used to sign JWT tokens - change this in production, keep it secret
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-secret-key")
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-flask-secret")