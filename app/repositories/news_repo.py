from datetime import datetime
from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb


def upsert_steam_news(
    conn: Connection,
    news_item: dict[str, Any],
    appid: str,
    news_type: str,
    is_patch_candidate: bool,
    collected_run_id: str | None = None,
) -> None:
    query = """
        INSERT INTO steam_news (
            gid,
            appid,
            title,
            url,
            contents,
            date,
            feedname,
            feedlabel,
            author,
            tags,
            news_type,
            is_patch_candidate,
            collected_run_id
        )
        VALUES (
            %(gid)s,
            %(appid)s,
            %(title)s,
            %(url)s,
            %(contents)s,
            to_timestamp(%(date)s),
            %(feedname)s,
            %(feedlabel)s,
            %(author)s,
            %(tags)s,
            %(news_type)s,
            %(is_patch_candidate)s,
            %(collected_run_id)s
        )
        ON CONFLICT (gid) DO UPDATE SET
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            contents = EXCLUDED.contents,
            date = EXCLUDED.date,
            feedname = EXCLUDED.feedname,
            feedlabel = EXCLUDED.feedlabel,
            author = EXCLUDED.author,
            tags = EXCLUDED.tags,
            news_type = EXCLUDED.news_type,
            is_patch_candidate = EXCLUDED.is_patch_candidate,
            collected_run_id = EXCLUDED.collected_run_id,
            collected_at = NOW();
    """

    params = {
        "gid": news_item.get("gid"),
        "appid": appid,
        "title": news_item.get("title") or "",
        "url": news_item.get("url"),
        "contents": news_item.get("contents"),
        "date": news_item.get("date"),
        "feedname": news_item.get("feedname"),
        "feedlabel": news_item.get("feedlabel"),
        "author": news_item.get("author"),
        "tags": Jsonb(news_item.get("tags", [])),
        "news_type": news_type,
        "is_patch_candidate": is_patch_candidate,
        "collected_run_id": collected_run_id,
    }

    with conn.cursor() as cur:
        cur.execute(query, params)


def list_patch_candidates(conn: Connection, appid: str) -> list[dict[str, Any]]:
    query = """
        SELECT
            gid,
            title,
            date,
            news_type,
            is_patch_candidate
        FROM steam_news
        WHERE appid = %(appid)s
          AND is_patch_candidate = true
        ORDER BY date DESC;
    """

    params = {
        "appid": appid,
    }

    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    candidates = []
    for row in rows:
        candidate = {
            "gid": row[0],
            "title": row[1],
            "date": row[2],
            "news_type": row[3],
            "is_patch_candidate": row[4],
        }
        candidates.append(candidate)

    return candidates


def get_news_by_gid(conn: Connection, gid: str) -> dict[str, Any] | None:
    query = """
        SELECT
            gid,
            appid,
            title,
            url,
            contents,
            date,
            news_type,
            is_patch_candidate
        FROM steam_news
        WHERE gid = %(gid)s;
    """

    params = {
        "gid": gid,
    }

    with conn.cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()

    if row is None:
        return None

    news = {
        "gid": row[0],
        "appid": row[1],
        "title": row[2],
        "url": row[3],
        "contents": row[4],
        "date": row[5],
        "news_type": row[6],
        "is_patch_candidate": row[7],
    }

    return news


def list_news_for_indexing(conn: Connection, appid: str) -> list[dict[str, Any]]:
    query = """
        SELECT gid, title, contents, date, news_type, url
        FROM steam_news
        WHERE appid = %s
          AND contents IS NOT NULL
          AND BTRIM(contents) <> ''
        ORDER BY date DESC;
    """
    with conn.cursor() as cur:
        cur.execute(query, (appid,))
        rows = cur.fetchall()
    return [
        {
            "gid": row[0],
            "title": row[1],
            "contents": row[2],
            "date": row[3],
            "news_type": row[4],
            "url": row[5],
        }
        for row in rows
    ]


def list_overlapping_patches(
    conn: Connection,
    *,
    appid: str,
    start_at: datetime,
    end_at: datetime,
    exclude_gid: str,
) -> list[str]:
    query = """
        SELECT gid FROM steam_news
        WHERE appid = %s
          AND is_patch_candidate = TRUE
          AND date >= %s AND date < %s
          AND gid <> %s
        ORDER BY date;
    """
    with conn.cursor() as cur:
        cur.execute(query, (appid, start_at, end_at, exclude_gid))
        return [row[0] for row in cur.fetchall()]
