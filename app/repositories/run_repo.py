from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb


def start_collection_run(
    conn: Connection,
    *,
    source_type: str,
    appid: str,
    request_params: dict[str, Any],
) -> UUID:
    query = """
        INSERT INTO collection_runs (source_type, appid, request_params)
        VALUES (%s, %s, %s)
        RETURNING run_id;
    """
    with conn.cursor() as cur:
        cur.execute(query, (source_type, appid, Jsonb(request_params)))
        row = cur.fetchone()
    if row is None:
        raise RuntimeError("collection run was not created")
    return row[0]


def finish_collection_run(
    conn: Connection,
    *,
    run_id: UUID,
    status: str,
    row_count: int,
    error_message: str | None = None,
) -> None:
    query = """
        UPDATE collection_runs
        SET finished_at = %s, status = %s, row_count = %s, error_message = %s
        WHERE run_id = %s;
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (datetime.now(timezone.utc), status, row_count, error_message, run_id),
        )
