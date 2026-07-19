from datetime import datetime, timezone
from typing import Any

import requests

from app.config import settings
from app.db import get_connection
from app.repositories.news_repo import upsert_steam_news

STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"

NEWS_TYPE_KEYWORDS = {
    "patch_note": [
        "patch notes",
        "patchnotes",
        "패치노트",
        "패치 노트",
    ],
    "hotfix": [
        "hotfix",
        "핫픽스",
    ],
    "maintenance_notice": [
        "maintenance",
        "점검",
    ],
    "server_notice": [
        "server",
        "connection restored",
        "login",
        "서버",
        "접속",
    ],
    "dev_note": [
        "dev journal",
        "developer",
        "개발자",
        "개발 노트",
    ],
    "character_notice": [
        "new character",
        "character",
        "preview",
        "캐릭터",
        "신규 캐릭터",
    ],
    "event": [
        "event",
        "festival",
        "gift",
        "raffle",
        "winners",
        "이벤트",
        "선물",
        "당첨",
    ],
    "reward_notice": [
        "reward",
        "rewards",
        "distribution",
        "token",
        "보상",
    ],
    "sale_or_bundle": [
        "bundle",
        "sale",
        "off",
        "패키지",
        "할인",
    ],
}

NEWS_TYPE_PRIORITY = [
    "patch_note",
    "hotfix",
    "maintenance_notice",
    "server_notice",
    "dev_note",
    "character_notice",
    "reward_notice",
    "event",
    "sale_or_bundle",
]


def find_matched_keywords(title: str, keywords: list[str]) -> list[str]:
    lowered_title = title.lower()

    matched_keywords = [keyword for keyword in keywords if keyword.lower() in lowered_title]

    return matched_keywords


def classify_news_item(title: str) -> tuple[str, list[str], dict[str, list[str]]]:
    matched_keywords_by_type: dict[str, list[str]] = {}

    for news_type, keywords in NEWS_TYPE_KEYWORDS.items():
        matched_keywords = find_matched_keywords(title, keywords)

        if matched_keywords:
            matched_keywords_by_type[news_type] = matched_keywords

    matched_types = list(matched_keywords_by_type.keys())

    primary_news_type = "unknown"
    for news_type in NEWS_TYPE_PRIORITY:
        if news_type in matched_types:
            primary_news_type = news_type
            break

    return primary_news_type, matched_types, matched_keywords_by_type


def fetch_steam_news(appid: str, count: int = 50) -> list[dict[str, Any]]:
    params = {
        "appid": appid,
        "count": count,
        "maxlength": 0,
        "format": "json",
    }

    response = requests.get(
        STEAM_NEWS_URL,
        params=params,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()

    data = response.json()

    appnews = data.get("appnews")
    if not isinstance(appnews, dict):
        raise ValueError(
            f"Unexpected Steam News API response: appnews is missing or invalid. data={data}"
        )

    news_items = appnews.get("newsitems")
    if not isinstance(news_items, list):
        raise ValueError(
            f"Unexpected Steam News API response: newsitems is missing or invalid. appnews={appnews}"
        )

    return news_items


def unix_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


def main():
    appid = settings.default_appid

    news_items = fetch_steam_news(
        appid=appid,
        count=30,
    )

    saved_count = 0

    with get_connection() as conn:
        for item in news_items:
            gid = item.get("gid")
            title = item.get("title") or ""
            date = unix_to_datetime(item["date"]) if item.get("date") else None
            feedname = item.get("feedname")
            tags = item.get("tags", [])

            primary_news_type, matched_types, matched_keywords = classify_news_item(title)
            is_patch_candidate = primary_news_type in ["patch_note", "hotfix"]

            upsert_steam_news(
                conn=conn,
                news_item=item,
                appid=appid,
                news_type=primary_news_type,
                is_patch_candidate=is_patch_candidate,
            )

            saved_count += 1

            print("-" * 80)
            print(f"gid       : {gid}")
            print(f"title     : {title}")
            print(f"date      : {date}")
            print(f"feedname  : {feedname}")
            print(f"tags      : {tags}")
            print(f"type      : {primary_news_type}")
            print(f"types     : {matched_types}")
            print(f"patch?    : {is_patch_candidate}")
            print(f"matched   : {matched_keywords}")

        conn.commit()

    print("=" * 80)
    print(f"saved news count: {saved_count}")


if __name__ == "__main__":
    main()
