from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IssueType = Literal[
    "matchmaking",
    "server_connection",
    "performance",
    "bug",
    "balance",
    "character",
    "monetization",
    "ux",
    "other",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewIssue(StrictModel):
    review_id: str
    issue_types: list[IssueType]
    summary: str
    evidence_spans: list[str]
    expression_intensity: Literal["low", "medium", "high", "unknown"]
    confidence: float = Field(ge=0, le=1)


class WindowStats(StrictModel):
    count: int
    positive_count: int
    negative_count: int
    positive_ratio: float | None
    positive_ratio_ci_low: float | None
    positive_ratio_ci_high: float | None


class IssueDelta(StrictModel):
    issue_type: str
    before_count: int
    after_count: int
    before_ratio: float
    after_ratio: float
    percentage_point_change: float


class PatchCoverage(StrictModel):
    patch_gid: str
    title: str
    reference_at: datetime
    window_days: int
    before_count: int
    after_count: int
    overlapping_patches: list[str]
    eligible: bool
    exclusion_reason: str | None = None


class SearchResult(StrictModel):
    chunk_id: str
    gid: str
    title: str
    section_path: str
    content: str
    score: float
    method: str


class GroundedClaim(StrictModel):
    text: str
    evidence_ids: list[str]


class GroundedReport(StrictModel):
    observed_changes: list[GroundedClaim]
    related_public_evidence: list[GroundedClaim]
    needs_verification: list[str]
    status: Literal["grounded", "insufficient_evidence"]
    limitations: list[str]
