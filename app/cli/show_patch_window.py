from datetime import timedelta

from app.db import get_connection
from app.repositories.news_repo import get_news_by_gid


DEFAULT_PATCH_GID = "1836506165545135"
DEFAULT_WINDOW_DAYS = 7


def main() -> None:
    patch_gid = DEFAULT_PATCH_GID
    window_days = DEFAULT_WINDOW_DAYS

    with get_connection() as conn:
        patch_news = get_news_by_gid(conn=conn, gid=patch_gid)

    if patch_news is None:
        raise ValueError(f"Patch news not found. patch_gid={patch_gid}")

    patch_date = patch_news["date"]
    patch_day = patch_date.date()

    before_start = patch_day - timedelta(days=window_days)
    before_end = patch_day - timedelta(days=1)

    after_start = patch_day
    after_end = patch_day + timedelta(days=window_days)

    until_date = before_start

    print("patch window")
    print("-" * 80)
    print(f"gid          : {patch_news['gid']}")
    print(f"title        : {patch_news['title']}")
    print(f"news_type    : {patch_news['news_type']}")
    print(f"patch_date   : {patch_date}")
    print(f"window_days  : {window_days}")
    print("-" * 80)
    print(f"before_start : {before_start}")
    print(f"before_end   : {before_end}")
    print(f"after_start  : {after_start}")
    print(f"after_end    : {after_end}")
    print(f"until_date   : {until_date}")


if __name__ == "__main__":
    main()
