import argparse
import json
from pathlib import Path

from app.evaluation.metrics import multilabel_metrics
from app.services.issues import classify_issue_baseline
from app.services.llm_issues import extract_issue_with_llm


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate issue extraction from JSONL labels")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--method", choices=("baseline", "llm"), default="baseline")
    args = parser.parse_args()
    classifier = extract_issue_with_llm if args.method == "llm" else classify_issue_baseline
    expected: list[set[str]] = []
    predicted: list[set[str]] = []
    failures = 0
    with args.dataset.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                result = classifier(row["review_id"], row["review"])
            except Exception as exc:
                failures += 1
                print(f"failure line={line_number}: {exc}")
                continue
            expected.append(set(row["issue_types"]))
            predicted.append(set(result.issue_types))
    metrics = multilabel_metrics(expected, predicted)
    metrics.update({"examples": len(expected), "failures": failures, "method": args.method})
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
