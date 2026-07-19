import argparse

from app.config import settings
from app.db import get_connection
from app.services.indexing import index_news_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk and index collected Steam news")
    parser.add_argument("--appid", default=settings.default_appid)
    parser.add_argument("--with-embeddings", action="store_true")
    args = parser.parse_args()
    with get_connection() as conn:
        result = index_news_documents(conn, appid=args.appid, with_embeddings=args.with_embeddings)
        conn.commit()
    print(result)


if __name__ == "__main__":
    main()
