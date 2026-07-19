from __future__ import annotations

from math import sqrt
from typing import Iterable, Mapping, Any

from app.models import WindowStats


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    if total == 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def calculate_window_stats(reviews: Iterable[Mapping[str, Any]]) -> WindowStats:
    rows = list(reviews)
    total = len(rows)
    positives = sum(1 for row in rows if bool(row.get("voted_up")))
    interval = wilson_interval(positives, total)
    return WindowStats(
        count=total,
        positive_count=positives,
        negative_count=total - positives,
        positive_ratio=positives / total if total else None,
        positive_ratio_ci_low=interval[0] if interval else None,
        positive_ratio_ci_high=interval[1] if interval else None,
    )
