from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from app.models import IssueDelta, WindowStats


def upsert_patch_window_report(
    conn: Connection,
    *,
    appid: str,
    patch_gid: str,
    reference_at: Any,
    window_days: int,
    before_start: Any,
    before_end: Any,
    after_start: Any,
    after_end: Any,
    before: WindowStats,
    after: WindowStats,
    min_reviews: int,
    warnings: list[str],
    keyword_rules_version: str,
    issue_deltas: list[IssueDelta],
) -> UUID:
    eligible = before.count >= min_reviews and after.count >= min_reviews
    pp_change = (
        (after.positive_ratio - before.positive_ratio) * 100
        if before.positive_ratio is not None and after.positive_ratio is not None
        else None
    )
    query = """
        INSERT INTO patch_window_reports (
            appid, patch_gid, analysis_reference_at, window_days,
            before_start, before_end, after_start, after_end,
            before_count, after_count, before_positive, after_positive,
            before_positive_ratio, after_positive_ratio, percentage_point_change,
            min_reviews_per_window, eligible, warnings, keyword_rules_version,
            keyword_results
        ) VALUES (
            %(appid)s, %(patch_gid)s, %(reference_at)s, %(window_days)s,
            %(before_start)s, %(before_end)s, %(after_start)s, %(after_end)s,
            %(before_count)s, %(after_count)s, %(before_positive)s, %(after_positive)s,
            %(before_ratio)s, %(after_ratio)s, %(pp_change)s,
            %(min_reviews)s, %(eligible)s, %(warnings)s, %(rules_version)s,
            %(keyword_results)s
        )
        ON CONFLICT (patch_gid, window_days, min_reviews_per_window, keyword_rules_version)
        DO UPDATE SET
            before_count = EXCLUDED.before_count,
            after_count = EXCLUDED.after_count,
            before_positive = EXCLUDED.before_positive,
            after_positive = EXCLUDED.after_positive,
            before_positive_ratio = EXCLUDED.before_positive_ratio,
            after_positive_ratio = EXCLUDED.after_positive_ratio,
            percentage_point_change = EXCLUDED.percentage_point_change,
            eligible = EXCLUDED.eligible,
            warnings = EXCLUDED.warnings,
            keyword_results = EXCLUDED.keyword_results,
            created_at = NOW()
        RETURNING report_id;
    """
    params = {
        "appid": appid,
        "patch_gid": patch_gid,
        "reference_at": reference_at,
        "window_days": window_days,
        "before_start": before_start,
        "before_end": before_end,
        "after_start": after_start,
        "after_end": after_end,
        "before_count": before.count,
        "after_count": after.count,
        "before_positive": before.positive_count,
        "after_positive": after.positive_count,
        "before_ratio": before.positive_ratio,
        "after_ratio": after.positive_ratio,
        "pp_change": pp_change,
        "min_reviews": min_reviews,
        "eligible": eligible,
        "warnings": Jsonb(warnings),
        "rules_version": keyword_rules_version,
        "keyword_results": Jsonb([item.model_dump() for item in issue_deltas]),
    }
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    if row is None:
        raise RuntimeError("patch window report was not saved")
    return row[0]


def get_patch_window_report(conn: Connection, report_id: UUID) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM patch_window_reports WHERE report_id = %s", (report_id,))
        row = cur.fetchone()
        if row is None:
            return None
        columns = [description.name for description in cur.description]
    return dict(zip(columns, row, strict=True))


def start_analysis_run(
    conn: Connection,
    *,
    report_id: UUID,
    llm_model: str,
    embedding_model: str,
    prompt_version: str,
    index_version: str,
    request_params: dict[str, Any],
) -> UUID:
    query = """
        INSERT INTO analysis_runs (
            report_id, status, llm_model, embedding_model,
            prompt_version, index_version, request_params
        ) VALUES (%s, 'created', %s, %s, %s, %s, %s)
        RETURNING analysis_run_id;
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                report_id,
                llm_model,
                embedding_model,
                prompt_version,
                index_version,
                Jsonb(request_params),
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise RuntimeError("analysis run was not created")
    return row[0]


def finish_analysis_run(
    conn: Connection,
    *,
    analysis_run_id: UUID,
    status: str,
    latency_ms: int,
    report: dict[str, Any] | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error_message: str | None = None,
) -> None:
    query = """
        UPDATE analysis_runs SET
            status = %s,
            report = %s,
            latency_ms = %s,
            input_tokens = %s,
            output_tokens = %s,
            error_message = %s,
            finished_at = %s
        WHERE analysis_run_id = %s;
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                status,
                Jsonb(json.loads(json.dumps(report, default=str))) if report is not None else None,
                latency_ms,
                input_tokens,
                output_tokens,
                error_message,
                datetime.now(timezone.utc),
                analysis_run_id,
            ),
        )


def save_retrieval_run(
    conn: Connection,
    *,
    analysis_run_id: UUID,
    query_text: str,
    method: str,
    top_k: int,
    results: list[dict[str, Any]],
    latency_ms: int,
) -> None:
    query = """
        INSERT INTO retrieval_runs (
            analysis_run_id, query, method, top_k, results, latency_ms
        ) VALUES (%s, %s, %s, %s, %s, %s);
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            (analysis_run_id, query_text, method, top_k, Jsonb(results), latency_ms),
        )
