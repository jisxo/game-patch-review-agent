from datetime import datetime, timezone
from collections.abc import Iterator
from time import sleep
from typing import Any
from urllib.parse import unquote

import requests

from app.config import settings


STEAM_REVIEW_URL_TEMPLATE = "https://store.steampowered.com/appreviews/{appid}"


def fetch_steam_reviews(
    appid: str,
    language: str = "koreana",
    review_filter: str = "recent",
    review_type: str = "all",
    purchase_type: str = "all",
    num_per_page: int = 20,
    cursor: str = "*",
    include_offtopic: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    url = STEAM_REVIEW_URL_TEMPLATE.format(appid=appid)

    params = {
        "json": 1,
        "language": language,
        "filter": review_filter,
        "review_type": review_type,
        "purchase_type": purchase_type,
        "num_per_page": num_per_page,
        "cursor": cursor,
        "filter_offtopic_activity": 0 if include_offtopic else 1,
    }

    response = requests.get(
        url,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()

    data = response.json()

    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError(
            f"Unexpected Steam Review API response: reviews is missing or invalid. "
            f"data_keys={list(data.keys())}"
        )

    next_cursor = data.get("cursor")
    if not isinstance(next_cursor, str):
        raise ValueError(
            f"Unexpected Steam Review API response: cursor is missing or invalid. "
            f"data_keys={list(data.keys())}"
        )

    return reviews, next_cursor


def iter_review_pages(
    *,
    appid: str,
    language: str = "koreana",
    review_type: str = "all",
    purchase_type: str = "all",
    num_per_page: int = 100,
    include_offtopic: bool = False,
    max_pages: int | None = None,
) -> Iterator[tuple[int, list[dict[str, Any]], str]]:
    """Yield Steam review pages and stop safely on empty or repeated cursors."""
    cursor = "*"
    seen_cursors: set[str] = set()
    page = 1

    while max_pages is None or page <= max_pages:
        last_error: Exception | None = None
        for attempt in range(settings.max_retry_count):
            try:
                reviews, next_cursor = fetch_steam_reviews(
                    appid=appid,
                    language=language,
                    review_filter="recent",
                    review_type=review_type,
                    purchase_type=purchase_type,
                    num_per_page=num_per_page,
                    cursor=cursor,
                    include_offtopic=include_offtopic,
                )
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 < settings.max_retry_count:
                    sleep(settings.request_sleep_seconds * (attempt + 1))
        else:
            raise RuntimeError(
                f"Steam Review API failed: appid={appid}, page={page}, cursor={cursor}"
            ) from last_error

        normalized_next = unquote(next_cursor)
        yield page, reviews, next_cursor
        if not reviews:
            return
        if normalized_next in seen_cursors or normalized_next == unquote(cursor):
            raise RuntimeError(
                f"Steam Review API returned a repeated cursor: appid={appid}, page={page}"
            )
        seen_cursors.add(normalized_next)
        cursor = next_cursor
        page += 1
        if settings.request_sleep_seconds > 0:
            sleep(settings.request_sleep_seconds)


def unix_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


def main() -> None:
    reviews, next_cursor = fetch_steam_reviews(
        appid=settings.default_appid,
        language=settings.default_language,
        num_per_page=5,
        cursor="*",
    )

    print(f"review count: {len(reviews)}")
    print(f"next cursor : {next_cursor}")

    for review in reviews:
        recommendationid = review.get("recommendationid")
        voted_up = review.get("voted_up")
        language = review.get("language")
        timestamp_created = review.get("timestamp_created")
        created_at = (
            unix_to_datetime(timestamp_created) if isinstance(timestamp_created, int) else None
        )
        playtime_forever = review.get("author", {}).get("playtime_forever")
        playtime_at_review = review.get("author", {}).get("playtime_at_review")
        review_text = review.get("review") or ""

        print("-" * 80)
        print(f"recommendationid  : {recommendationid}")
        print(f"voted_up          : {voted_up}")
        print(f"language          : {language}")
        print(f"created_at        : {created_at}")
        print(f"playtime_forever  : {playtime_forever}")
        print(f"playtime_at_review: {playtime_at_review}")
        print(f"review preview    : {review_text[:200]}")


if __name__ == "__main__":
    main()
