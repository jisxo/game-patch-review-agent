import unittest

from app.models import SearchResult
from app.services.reporting import build_grounded_report, retrieval_query_from_analysis


class ReportingTests(unittest.TestCase):
    def test_report_abstains_without_public_evidence(self) -> None:
        analysis = {
            "before": {"positive_ratio": 0.5},
            "after": {"positive_ratio": 0.4},
            "issue_deltas": [],
            "warnings": [],
        }
        report = build_grounded_report(report_id="r1", analysis=analysis, retrieval_results=[])
        self.assertEqual(report.status, "insufficient_evidence")
        self.assertTrue(report.observed_changes)

    def test_report_cites_chunk(self) -> None:
        analysis = {
            "before": {"positive_ratio": 0.5},
            "after": {"positive_ratio": 0.6},
            "issue_deltas": [],
            "warnings": [],
        }
        result = SearchResult(
            chunk_id="c1",
            gid="g1",
            title="Patch",
            section_path="Matchmaking",
            content="queue changed",
            score=1,
            method="bm25",
        )
        report = build_grounded_report(
            report_id="r1", analysis=analysis, retrieval_results=[result]
        )
        self.assertEqual(report.status, "grounded")
        self.assertEqual(report.related_public_evidence[0].evidence_ids, ["chunk:c1"])

    def test_query_uses_increasing_issues(self) -> None:
        query = retrieval_query_from_analysis(
            {"issue_deltas": [{"issue_type": "server_connection", "percentage_point_change": 3}]}
        )
        self.assertIn("server connection", query)


if __name__ == "__main__":
    unittest.main()
