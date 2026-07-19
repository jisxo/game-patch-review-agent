from app.config import settings
from app.db import get_connection
from app.repositories.news_repo import list_patch_candidates


def main() -> None:
    appid = settings.default_appid

    with get_connection() as conn:
        candidates = list_patch_candidates(conn=conn, appid=appid)

    print(f"patch candidates count: {len(candidates)}")

    for candidate in candidates:
        print("-" * 80)
        print(f"gid       : {candidate['gid']}")
        print(f"title     : {candidate['title']}")
        print(f"date      : {candidate['date']}")
        print(f"news_type : {candidate['news_type']}")


if __name__ == "__main__":
    main()
