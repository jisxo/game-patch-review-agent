from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from app.models import ReviewIssue


def upsert_review(
    conn: Connection,
    *,
    appid: str,
    review: dict[str, Any],
    collected_run_id: UUID | None,
) -> bool:
    author = review.get("author") or {}
    query = """
        INSERT INTO steam_reviews (
            recommendationid, appid, review, voted_up, language,
            timestamp_created, timestamp_updated, playtime_forever,
            playtime_at_review, weighted_vote_score, votes_up,
            comment_count, collected_run_id
        ) VALUES (
            %(recommendationid)s, %(appid)s, %(review)s, %(voted_up)s,
            %(language)s, to_timestamp(%(timestamp_created)s),
            to_timestamp(%(timestamp_updated)s), %(playtime_forever)s,
            %(playtime_at_review)s, %(weighted_vote_score)s,
            %(votes_up)s, %(comment_count)s, %(collected_run_id)s
        )
        ON CONFLICT (recommendationid) DO UPDATE SET
            review = EXCLUDED.review,
            voted_up = EXCLUDED.voted_up,
            language = EXCLUDED.language,
            timestamp_updated = EXCLUDED.timestamp_updated,
            playtime_forever = EXCLUDED.playtime_forever,
            playtime_at_review = EXCLUDED.playtime_at_review,
            weighted_vote_score = EXCLUDED.weighted_vote_score,
            votes_up = EXCLUDED.votes_up,
            comment_count = EXCLUDED.comment_count,
            collected_run_id = EXCLUDED.collected_run_id,
            collected_at = NOW()
        RETURNING (xmax = 0) AS inserted;
    """
    params = {
        "recommendationid": review["recommendationid"],
        "appid": appid,
        "review": review.get("review") or "",
        "voted_up": bool(review.get("voted_up")),
        "language": review.get("language") or "unknown",
        "timestamp_created": review["timestamp_created"],
        "timestamp_updated": review.get("timestamp_updated") or review["timestamp_created"],
        "playtime_forever": author.get("playtime_forever"),
        "playtime_at_review": author.get("playtime_at_review"),
        "weighted_vote_score": review.get("weighted_vote_score"),
        "votes_up": review.get("votes_up"),
        "comment_count": review.get("comment_count"),
        "collected_run_id": collected_run_id,
    }
    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
    return bool(row and row[0])


def list_reviews_by_period(
    conn: Connection,
    *,
    appid: str,
    start_at: datetime,
    end_at: datetime,
) -> list[dict[str, Any]]:
    query = """
        SELECT recommendationid, review, voted_up, language,
               timestamp_created, timestamp_updated, playtime_forever,
               playtime_at_review
        FROM steam_reviews
        WHERE appid = %s
          AND timestamp_created >= %s
          AND timestamp_created < %s
        ORDER BY timestamp_created;
    """
    with conn.cursor() as cur:
        cur.execute(query, (appid, start_at, end_at))
        rows = cur.fetchall()
    return [
        {
            "review_id": row[0],
            "review": row[1],
            "voted_up": row[2],
            "language": row[3],
            "timestamp_created": row[4],
            "timestamp_updated": row[5],
            "playtime_forever": row[6],
            "playtime_at_review": row[7],
        }
        for row in rows
    ]


def count_reviews_by_period(
    conn: Connection,
    *,
    appid: str,
    start_at: datetime,
    end_at: datetime,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM steam_reviews
            WHERE appid = %s AND timestamp_created >= %s AND timestamp_created < %s;
            """,
            (appid, start_at, end_at),
        )
        row = cur.fetchone()
    return int(row[0]) if row else 0


def upsert_issue_prediction(
    conn: Connection,
    *,
    prediction: ReviewIssue,
    method: str,
    model: str,
    prompt_version: str,
) -> None:
    query = """
        INSERT INTO review_issue_predictions (
            review_id, method, model, prompt_version, issue_types,
            summary, evidence_spans, expression_intensity, confidence, raw_output
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (review_id, method, prompt_version, model) DO UPDATE SET
            issue_types = EXCLUDED.issue_types,
            summary = EXCLUDED.summary,
            evidence_spans = EXCLUDED.evidence_spans,
            expression_intensity = EXCLUDED.expression_intensity,
            confidence = EXCLUDED.confidence,
            raw_output = EXCLUDED.raw_output,
            created_at = NOW();
    """
    value = prediction.model_dump()
    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                prediction.review_id,
                method,
                model,
                prompt_version,
                Jsonb(prediction.issue_types),
                prediction.summary,
                Jsonb(prediction.evidence_spans),
                prediction.expression_intensity,
                prediction.confidence,
                Jsonb(value),
            ),
        )
