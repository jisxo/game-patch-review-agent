from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from psycopg import Connection

from app.config import settings
from app.models import PatchCoverage
from app.repositories.analysis_repo import upsert_patch_window_report
from app.repositories.news_repo import (
    get_news_by_gid,
    list_overlapping_patches,
    list_patch_candidates,
)
from app.repositories.review_repo import (
    count_reviews_by_period,
    list_reviews_by_period,
    upsert_issue_prediction,
)
from app.services.issues import classify_issue_baseline, compare_issue_distributions
from app.services.llm_issues import extract_issue_with_llm
from app.services.statistics import calculate_window_stats


def window_bounds(reference_at: Any, window_days: int) -> tuple[Any, Any, Any, Any]:
    before_start = reference_at - timedelta(days=window_days)
    before_end = reference_at
    after_start = reference_at
    after_end = reference_at + timedelta(days=window_days)
    return before_start, before_end, after_start, after_end


def calculate_patch_coverage(
    conn: Connection,
    *,
    appid: str,
    window_days: int,
    min_reviews: int,
) -> list[PatchCoverage]:
    results: list[PatchCoverage] = []
    for candidate in list_patch_candidates(conn, appid):
        before_start, before_end, after_start, after_end = window_bounds(
            candidate["date"], window_days
        )
        before_count = count_reviews_by_period(
            conn, appid=appid, start_at=before_start, end_at=before_end
        )
        after_count = count_reviews_by_period(
            conn, appid=appid, start_at=after_start, end_at=after_end
        )
        overlapping = list_overlapping_patches(
            conn,
            appid=appid,
            start_at=before_start,
            end_at=after_end,
            exclude_gid=candidate["gid"],
        )
        eligible = before_count >= min_reviews and after_count >= min_reviews
        reason = None
        if not eligible:
            reason = (
                f"minimum not met: before={before_count}, after={after_count}, min={min_reviews}"
            )
        results.append(
            PatchCoverage(
                patch_gid=candidate["gid"],
                title=candidate["title"],
                reference_at=candidate["date"],
                window_days=window_days,
                before_count=before_count,
                after_count=after_count,
                overlapping_patches=overlapping,
                eligible=eligible,
                exclusion_reason=reason,
            )
        )
    return results


def analyze_patch_window(
    conn: Connection,
    *,
    patch_gid: str,
    window_days: int | None = None,
    min_reviews: int | None = None,
    issue_method: str = "baseline",
) -> tuple[UUID, dict[str, Any]]:
    patch = get_news_by_gid(conn, patch_gid)
    if patch is None:
        raise ValueError(f"patch not found: gid={patch_gid}")
    days = window_days or settings.default_window_days
    minimum = min_reviews or settings.min_reviews_per_window
    before_start, before_end, after_start, after_end = window_bounds(patch["date"], days)
    before_reviews = list_reviews_by_period(
        conn, appid=patch["appid"], start_at=before_start, end_at=before_end
    )
    after_reviews = list_reviews_by_period(
        conn, appid=patch["appid"], start_at=after_start, end_at=after_end
    )
    before_stats = calculate_window_stats(before_reviews)
    after_stats = calculate_window_stats(after_reviews)
    if issue_method not in {"baseline", "llm"}:
        raise ValueError(f"unsupported issue method: {issue_method}")
    classifier = extract_issue_with_llm if issue_method == "llm" else classify_issue_baseline
    before_issues = [classifier(row["review_id"], row["review"]) for row in before_reviews]
    after_issues = [classifier(row["review_id"], row["review"]) for row in after_reviews]
    prediction_model = settings.llm_model if issue_method == "llm" else "keyword-baseline"
    prediction_version = (
        "review-issue-v1" if issue_method == "llm" else settings.keyword_rules_version
    )
    for prediction in before_issues + after_issues:
        upsert_issue_prediction(
            conn,
            prediction=prediction,
            method=issue_method,
            model=prediction_model,
            prompt_version=prediction_version,
        )
    deltas = compare_issue_distributions(before_issues, after_issues)
    overlaps = list_overlapping_patches(
        conn,
        appid=patch["appid"],
        start_at=before_start,
        end_at=after_end,
        exclude_gid=patch_gid,
    )
    warnings: list[str] = []
    if before_stats.count < minimum or after_stats.count < minimum:
        warnings.append("minimum review count not met")
    if overlaps:
        warnings.append(f"overlapping patches: {', '.join(overlaps)}")
    report_id = upsert_patch_window_report(
        conn,
        appid=patch["appid"],
        patch_gid=patch_gid,
        reference_at=patch["date"],
        window_days=days,
        before_start=before_start,
        before_end=before_end,
        after_start=after_start,
        after_end=after_end,
        before=before_stats,
        after=after_stats,
        min_reviews=minimum,
        warnings=warnings,
        keyword_rules_version=settings.keyword_rules_version,
        issue_deltas=deltas,
    )
    return report_id, {
        "patch": patch,
        "before": before_stats.model_dump(),
        "after": after_stats.model_dump(),
        "issue_deltas": [item.model_dump() for item in deltas],
        "warnings": warnings,
        "eligible": before_stats.count >= minimum and after_stats.count >= minimum,
        "issue_method": issue_method,
        "before_start": before_start,
        "after_end": after_end,
    }
