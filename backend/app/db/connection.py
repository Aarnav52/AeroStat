import time
import psycopg2
from contextlib import contextmanager
from app.config import config
import logging

logger = logging.getLogger(__name__)

# This project has repeatedly hit transient DNS/TLS resets against the
# Supabase pooler host (campus WiFi content-filtering, per prior session
# notes) - not a code bug, but enough of a known, occasional issue that a
# single blip shouldn't kill an entire unattended scheduled sweep. Retry
# just the initial connect (never retry mid-transaction).
_CONNECT_RETRIES = 3
_CONNECT_RETRY_DELAY_SECONDS = 3


def _connect_with_retry():
    last_error = None
    for attempt in range(1, _CONNECT_RETRIES + 1):
        try:
            return psycopg2.connect(config.DATABASE_URL)
        except psycopg2.OperationalError as e:
            last_error = e
            if attempt < _CONNECT_RETRIES:
                logger.warning(
                    f"DB connect attempt {attempt}/{_CONNECT_RETRIES} failed "
                    f"({e}); retrying in {_CONNECT_RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(_CONNECT_RETRY_DELAY_SECONDS)
    raise last_error


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Yields a psycopg2 connection object.
    """
    conn = None
    try:
        conn = _connect_with_retry()
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
