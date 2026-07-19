import unittest
from unittest.mock import patch

from app.models import SearchResult
from app.services.llm_issues import extract_issue_with_llm
from app.services.reporting import build_grounded_report_with_llm


class FakeClient:
    response: dict = {}

    def json_completion(self, **_: object) -> tuple[dict, dict[str, int]]:
        return self.response, {"input_tokens": 10, "output_tokens": 5}


class LLMGuardrailTests(unittest.TestCase):
    @patch("app.services.llm_issues.OpenAICompatibleClient", FakeClient)
    def test_issue_requires_exact_evidence_span(self) -> None:
        FakeClient.response = {
            "review_id": "r1",
            "issue_types": ["matchmaking"],
            "summary": "매칭 문제",
            "evidence_spans": ["원문에 없는 문장"],
            "expression_intensity": "medium",
            "confidence": 0.9,
        }
        with self.assertRaisesRegex(ValueError, "evidence span"):
            extract_issue_with_llm("r1", "매칭이 느립니다")

    @patch("app.services.reporting.OpenAICompatibleClient", FakeClient)
    def test_report_rejects_unknown_citation(self) -> None:
        FakeClient.response = {
            "observed_changes": [{"text": "추천 비율이 변했습니다.", "evidence_ids": ["stat:r1"]}],
            "related_public_evidence": [
                {"text": "관련 후보입니다.", "evidence_ids": ["chunk:invented"]}
            ],
            "needs_verification": ["내부 확인 필요"],
            "status": "grounded",
            "limitations": ["Steam 한국어 리뷰만 사용"],
        }
        analysis = {
            "before": {"positive_ratio": 0.5},
            "after": {"positive_ratio": 0.4},
            "issue_deltas": [],
            "warnings": [],
        }
        result = SearchResult(
            chunk_id="c1",
            gid="g1",
            title="Patch",
            section_path="System",
            content="matchmaking changed",
            score=1,
            method="bm25",
        )
        with self.assertRaisesRegex(ValueError, "invalid evidence IDs"):
            build_grounded_report_with_llm(
                report_id="r1", analysis=analysis, retrieval_results=[result]
            )


if __name__ == "__main__":
    unittest.main()
