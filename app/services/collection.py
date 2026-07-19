from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from psycopg import Connection

from app.collectors.steam_news import (
    classify_news_item,
    fetch_steam_news,
)
from app.collectors.steam_reviews import iter_review_pages, unix_to_datetime
from app.repositories.news_repo import upsert_steam_news
from app.repositories.review_repo import upsert_review
from app.repositories.run_repo import finish_collection_run, start_collection_run


def collect_news(conn: Connection, *, appid: str, count: int = 100) -> dict[str, Any]:
    params = {"count": count, "maxlength": 0}
    run_id = start_collection_run(
        conn, source_type="steam_news", appid=appid, request_params=params
    )
    conn.commit()
    saved = 0
    try:
        for item in fetch_steam_news(appid, count=count):
            title = item.get("title") or ""
            news_type, _, _ = classify_news_item(title)
            upsert_steam_news(
                conn,
                news_item=item,
                appid=appid,
                news_type=news_type,
                is_patch_candidate=news_type in {"patch_note", "hotfix"},
                collected_run_id=str(run_id),
            )
            saved += 1
        finish_collection_run(conn, run_id=run_id, status="success", row_count=saved)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        finish_collection_run(
            conn,
            run_id=run_id,
            status="failed",
            row_count=saved,
            error_message=str(exc)[:1000],
        )
        conn.commit()
        raise
    return {"run_id": str(run_id), "saved": saved}


def collect_reviews(
    conn: Connection,
    *,
    appid: str,
    language: str,
    max_pages: int | None,
    include_offtopic: bool,
    stop_before: datetime | None = None,
) -> dict[str, Any]:
    params = {
        "language": language,
        "filter": "recent",
        "purchase_type": "all",
        "max_pages": max_pages,
        "include_offtopic": include_offtopic,
        "stop_before": stop_before.isoformat() if stop_before else None,
    }
    run_id = start_collection_run(
        conn, source_type="steam_reviews", appid=appid, request_params=params
    )
    conn.commit()
    saved = 0
    inserted = 0
    duplicates = 0
    pages = 0
    newest: datetime | None = None
    oldest: datetime | None = None
    stop_reason = "empty_page"
    try:
        for page, reviews, _ in iter_review_pages(
            appid=appid,
            language=language,
            include_offtopic=include_offtopic,
            max_pages=max_pages,
        ):
            pages = page
            if not reviews:
                break
            page_dates: list[datetime] = []
            for review in reviews:
                timestamp = review.get("timestamp_created")
                if not isinstance(timestamp, int):
                    raise ValueError(
                        f"invalid timestamp_created: appid={appid}, page={page}, "
                        f"review_id={review.get('recommendationid')}"
                    )
                created_at = unix_to_datetime(timestamp)
                page_dates.append(created_at)
                newest = created_at if newest is None else max(newest, created_at)
                oldest = created_at if oldest is None else min(oldest, created_at)
                was_inserted = upsert_review(
                    conn,
                    appid=appid,
                    review=review,
                    collected_run_id=run_id,
                )
                inserted += int(was_inserted)
                duplicates += int(not was_inserted)
                saved += 1
            if stop_before and page_dates and min(page_dates) < stop_before:
                stop_reason = "stop_before_reached"
                break
        else:
            stop_reason = "max_pages_reached"
        finish_collection_run(conn, run_id=run_id, status="success", row_count=saved)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        finish_collection_run(
            conn,
            run_id=run_id,
            status="failed",
            row_count=saved,
            error_message=str(exc)[:1000],
        )
        conn.commit()
        raise
    return {
        "run_id": str(run_id),
        "pages": pages,
        "processed": saved,
        "inserted": inserted,
        "duplicates": duplicates,
        "newest": newest.isoformat() if newest else None,
        "oldest": oldest.isoformat() if oldest else None,
        "stop_reason": stop_reason,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
