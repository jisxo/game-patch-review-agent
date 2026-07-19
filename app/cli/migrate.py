from pathlib import Path

from app.db import get_connection


def main() -> None:
    migration_dir = Path(__file__).resolve().parents[2] / "migrations"
    with get_connection() as conn:
        for path in sorted(migration_dir.glob("*.sql")):
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding="utf-8"))
            print(f"applied: {path.name}")
        conn.commit()


if __name__ == "__main__":
    main()
