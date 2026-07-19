import argparse
import json

from app.db import get_connection
from app.services.pipeline import run_patch_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a grounded patch-window report")
    parser.add_argument("patch_gid")
    parser.add_argument("--method", choices=("bm25", "dense", "hybrid"), default="bm25")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--issue-method", choices=("baseline", "llm"), default="baseline")
    parser.add_argument(
        "--generation-method", choices=("deterministic", "llm"), default="deterministic"
    )
    args = parser.parse_args()
    with get_connection() as conn:
        result = run_patch_report(
            conn,
            patch_gid=args.patch_gid,
            search_method=args.method,
            top_k=args.top_k,
            issue_method=args.issue_method,
            generation_method=args.generation_method,
        )
        conn.commit()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
