import unittest

from app.services.issues import classify_issue_baseline, compare_issue_distributions


class IssueTests(unittest.TestCase):
    def test_multilabel_classification_and_exact_evidence(self) -> None:
        text = "매칭이 너무 느립니다. 서버 렉도 심각해요."
        result = classify_issue_baseline("r1", text)
        self.assertIn("matchmaking", result.issue_types)
        self.assertIn("server_connection", result.issue_types)
        self.assertEqual(result.expression_intensity, "high")
        self.assertTrue(all(span in text for span in result.evidence_spans))

    def test_other_fallback(self) -> None:
        result = classify_issue_baseline("r2", "재미있어요")
        self.assertEqual(result.issue_types, ["other"])

    def test_distribution_delta_uses_review_ratio(self) -> None:
        before = [classify_issue_baseline("b1", "매칭 문제")]
        after = [
            classify_issue_baseline("a1", "매칭 문제"),
            classify_issue_baseline("a2", "매칭이 느림"),
        ]
        delta = next(
            item
            for item in compare_issue_distributions(before, after)
            if item.issue_type == "matchmaking"
        )
        self.assertEqual(delta.before_ratio, 1)
        self.assertEqual(delta.after_ratio, 1)


if __name__ == "__main__":
    unittest.main()
