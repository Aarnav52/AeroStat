import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _build_database_url():
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    db_user = os.getenv("user")
    db_password = os.getenv("password")
    db_host = os.getenv("host")
    db_port = os.getenv("port")
    db_name = os.getenv("database")

    if (db_user is None or db_password is None or db_host is None
            or db_port is None or db_name is None):
        return None

    escaped_password = quote_plus(db_password)
    return f"postgresql://{db_user}:{escaped_password}@{db_host}:{db_port}/{db_name}"


class Config:
    DATABASE_URL = _build_database_url()
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

config = Config()
