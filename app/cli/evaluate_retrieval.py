import argparse
import json
from pathlib import Path

from app.config import settings
from app.db import get_connection
from app.evaluation.metrics import recall_at_k, reciprocal_rank
from app.services.search import search_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval from JSONL gold labels")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--appid", default=settings.default_appid)
    parser.add_argument("--method", choices=("bm25", "dense", "hybrid"), default="bm25")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    with get_connection() as conn, args.dataset.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            results = search_chunks(
                conn,
                appid=args.appid,
                query=row["query"],
                method=args.method,
                top_k=args.top_k,
            )
            ranked = [item.chunk_id for item in results]
            expected = set(row["expected_chunk_ids"])
            recalls.append(recall_at_k(expected, ranked, args.top_k))
            reciprocal_ranks.append(reciprocal_rank(expected, ranked))
    output = {
        "method": args.method,
        "top_k": args.top_k,
        "examples": len(recalls),
        "recall_at_k": sum(recalls) / len(recalls) if recalls else 0,
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
