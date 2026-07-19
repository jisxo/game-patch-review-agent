from __future__ import annotations

from collections.abc import Iterable


def multilabel_metrics(
    expected: Iterable[set[str]], predicted: Iterable[set[str]]
) -> dict[str, float]:
    gold = list(expected)
    guesses = list(predicted)
    if len(gold) != len(guesses):
        raise ValueError("expected and predicted lengths differ")
    labels = sorted(set().union(*gold, *guesses)) if gold or guesses else []
    if not labels:
        return {"macro_precision": 1.0, "macro_recall": 1.0, "macro_f1": 1.0}
    precision_values: list[float] = []
    recall_values: list[float] = []
    f1_values: list[float] = []
    for label in labels:
        tp = sum(
            label in truth and label in guess for truth, guess in zip(gold, guesses, strict=True)
        )
        fp = sum(
            label not in truth and label in guess
            for truth, guess in zip(gold, guesses, strict=True)
        )
        fn = sum(
            label in truth and label not in guess
            for truth, guess in zip(gold, guesses, strict=True)
        )
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)
    return {
        "macro_precision": sum(precision_values) / len(labels),
        "macro_recall": sum(recall_values) / len(labels),
        "macro_f1": sum(f1_values) / len(labels),
    }


def recall_at_k(expected_ids: set[str], ranked_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 1.0 if not ranked_ids[:k] else 0.0
    return len(expected_ids.intersection(ranked_ids[:k])) / len(expected_ids)


def reciprocal_rank(expected_ids: set[str], ranked_ids: list[str]) -> float:
    for rank, item_id in enumerate(ranked_ids, start=1):
        if item_id in expected_ids:
            return 1 / rank
    return 0.0


def citation_precision(claim_evidence_ids: list[list[str]], valid_ids: set[str]) -> float:
    citations = [citation for group in claim_evidence_ids for citation in group]
    if not citations:
        return 0.0
    return sum(citation in valid_ids for citation in citations) / len(citations)
