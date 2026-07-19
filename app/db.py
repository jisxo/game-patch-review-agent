from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg import Connection

from app.config import settings


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    conn = psycopg.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()
