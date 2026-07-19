import argparse
import json
from datetime import datetime

from app.config import settings
from app.db import get_connection
from app.services.collection import collect_news, collect_reviews


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("datetime must include timezone, for example +00:00")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Steam news or reviews")
    subparsers = parser.add_subparsers(dest="source", required=True)

    news = subparsers.add_parser("news")
    news.add_argument("--appid", default=settings.default_appid)
    news.add_argument("--count", type=int, default=100)

    reviews = subparsers.add_parser("reviews")
    reviews.add_argument("--appid", default=settings.default_appid)
    reviews.add_argument("--language", default=settings.default_language)
    reviews.add_argument("--max-pages", type=int)
    reviews.add_argument("--include-offtopic", action="store_true")
    reviews.add_argument("--stop-before", type=parse_datetime)

    args = parser.parse_args()
    with get_connection() as conn:
        if args.source == "news":
            result = collect_news(conn, appid=args.appid, count=args.count)
        else:
            result = collect_reviews(
                conn,
                appid=args.appid,
                language=args.language,
                max_pages=args.max_pages,
                include_offtopic=args.include_offtopic,
                stop_before=args.stop_before,
            )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
