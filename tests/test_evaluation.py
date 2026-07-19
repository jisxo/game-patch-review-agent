import unittest

from app.evaluation.metrics import (
    citation_precision,
    multilabel_metrics,
    recall_at_k,
    reciprocal_rank,
)


class EvaluationTests(unittest.TestCase):
    def test_multilabel_perfect(self) -> None:
        metrics = multilabel_metrics([{"bug"}, {"balance"}], [{"bug"}, {"balance"}])
        self.assertEqual(metrics["macro_f1"], 1)

    def test_retrieval_metrics(self) -> None:
        self.assertEqual(recall_at_k({"b"}, ["a", "b"], 2), 1)
        self.assertEqual(reciprocal_rank({"b"}, ["a", "b"]), 0.5)

    def test_citation_precision(self) -> None:
        self.assertEqual(citation_precision([["a", "x"], ["b"]], {"a", "b"}), 2 / 3)


if __name__ == "__main__":
    unittest.main()
