from __future__ import annotations

import re

from app.models import IssueDelta, ReviewIssue


ISSUE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "matchmaking": ("매칭", "매치메이킹", "큐", "대기열", "팀매칭"),
    "server_connection": ("서버", "접속", "로그인", "연결", "핑", "렉"),
    "performance": ("프레임", "fps", "최적화", "버벅", "끊김", "성능"),
    "bug": ("버그", "오류", "에러", "튕김", "크래시", "작동안"),
    "balance": ("밸런스", "너프", "버프", "사기", "OP", "오버파워"),
    "character": ("캐릭터", "실험체", "스킬", "궁극기"),
    "monetization": ("과금", "현질", "가격", "스킨", "패스", "BM"),
    "ux": ("UI", "UX", "인터페이스", "메뉴", "조작", "편의성"),
}

HIGH_INTENSITY = ("최악", "절대", "망겜", "환불", "삭제", "못해", "심각")
MEDIUM_INTENSITY = ("불편", "짜증", "문제", "별로", "안됨", "느림")


def classify_issue_baseline(review_id: str, text: str) -> ReviewIssue:
    normalized = text.casefold()
    issue_types = [
        issue_type
        for issue_type, keywords in ISSUE_KEYWORDS.items()
        if any(keyword.casefold() in normalized for keyword in keywords)
    ]
    if not issue_types:
        issue_types = ["other"]

    intensity = "low"
    if any(keyword.casefold() in normalized for keyword in HIGH_INTENSITY):
        intensity = "high"
    elif any(keyword.casefold() in normalized for keyword in MEDIUM_INTENSITY):
        intensity = "medium"

    sentences = [item.strip() for item in re.split(r"(?<=[.!?。])\s+|\n+", text) if item.strip()]
    evidence = [
        sentence
        for sentence in sentences
        if any(
            keyword.casefold() in sentence.casefold()
            for issue_type in issue_types
            for keyword in ISSUE_KEYWORDS.get(issue_type, ())
        )
    ][:3]
    if not evidence and text.strip():
        evidence = [text.strip()[:300]]

    return ReviewIssue(
        review_id=review_id,
        issue_types=issue_types,
        summary=text.strip()[:200],
        evidence_spans=evidence,
        expression_intensity=intensity,
        confidence=0.7 if issue_types != ["other"] else 0.3,
    )


def issue_distribution(predictions: list[ReviewIssue]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for prediction in predictions:
        for issue_type in prediction.issue_types:
            counts[issue_type] = counts.get(issue_type, 0) + 1
    return counts


def compare_issue_distributions(
    before: list[ReviewIssue], after: list[ReviewIssue]
) -> list[IssueDelta]:
    before_counts = issue_distribution(before)
    after_counts = issue_distribution(after)
    issue_types = sorted(set(before_counts) | set(after_counts))
    return [
        IssueDelta(
            issue_type=issue_type,
            before_count=before_counts.get(issue_type, 0),
            after_count=after_counts.get(issue_type, 0),
            before_ratio=before_counts.get(issue_type, 0) / len(before) if before else 0,
            after_ratio=after_counts.get(issue_type, 0) / len(after) if after else 0,
            percentage_point_change=(
                (after_counts.get(issue_type, 0) / len(after) if after else 0)
                - (before_counts.get(issue_type, 0) / len(before) if before else 0)
            )
            * 100,
        )
        for issue_type in issue_types
    ]
