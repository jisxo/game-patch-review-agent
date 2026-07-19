from app.db import get_connection


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT appid, name, store_url FROM games;")
            rows = cur.fetchall()

    print("games table rows:")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
