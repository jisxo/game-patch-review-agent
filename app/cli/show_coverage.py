import argparse
import json

from app.config import settings
from app.db import get_connection
from app.services.analysis import calculate_patch_coverage


def main() -> None:
    parser = argparse.ArgumentParser(description="Show review coverage for patch candidates")
    parser.add_argument("--appid", default=settings.default_appid)
    parser.add_argument("--window-days", type=int, default=settings.default_window_days)
    parser.add_argument("--min-reviews", type=int, default=settings.min_reviews_per_window)
    args = parser.parse_args()
    with get_connection() as conn:
        result = calculate_patch_coverage(
            conn,
            appid=args.appid,
            window_days=args.window_days,
            min_reviews=args.min_reviews,
        )
    print(
        json.dumps(
            [item.model_dump() for item in result], ensure_ascii=False, indent=2, default=str
        )
    )


if __name__ == "__main__":
    main()
