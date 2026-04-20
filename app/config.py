import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_UPLOADS_DIR = BASE_DIR / "app" / "uploads"


def _get_path_from_env(env_name, default_path):
    return Path(os.getenv(env_name, str(default_path))).expanduser().resolve()


INSTANCE_DIR = _get_path_from_env("PROJECTTRACKER_INSTANCE_DIR", DEFAULT_INSTANCE_DIR)
UPLOADS_DIR = _get_path_from_env("PROJECTTRACKER_UPLOADS_DIR", DEFAULT_UPLOADS_DIR)


def _sqlite_uri(path):
    return f"sqlite:///{path}"


class Config:
    SECRET_KEY = os.getenv("PROJECTTRACKER_SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "PROJECTTRACKER_MAIN_DB_URI",
        _sqlite_uri(INSTANCE_DIR / "main.db"),
    )
    SQLALCHEMY_BINDS = {
        "service": os.getenv(
            "PROJECTTRACKER_SERVICE_DB_URI",
            _sqlite_uri(INSTANCE_DIR / "service.db"),
        ),
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(UPLOADS_DIR)


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_BINDS = {
        "service": "sqlite://",
    }
