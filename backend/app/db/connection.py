import psycopg2
from contextlib import contextmanager
from app.config import config
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Yields a psycopg2 connection object.
    """
    conn = None
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
