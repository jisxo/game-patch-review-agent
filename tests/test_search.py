import unittest

from app.models import SearchResult
from app.services.search import bm25_search, reciprocal_rank_fusion, tokenize


CHUNKS = [
    {
        "chunk_id": "1",
        "gid": "g1",
        "title": "Patch matchmaking",
        "section_path": "System",
        "content": "Matchmaking queue logic was changed.",
    },
    {
        "chunk_id": "2",
        "gid": "g2",
        "title": "Character patch",
        "section_path": "Balance",
        "content": "Character attack damage was reduced.",
    },
]


class SearchTests(unittest.TestCase):
    def test_tokenize_korean_and_english(self) -> None:
        self.assertEqual(tokenize("매칭 Queue 변경"), ["매칭", "queue", "변경"])

    def test_bm25_returns_relevant_document(self) -> None:
        results = bm25_search(CHUNKS, "matchmaking queue", top_k=1)
        self.assertEqual(results[0].chunk_id, "1")
        self.assertGreater(results[0].score, 0)

    def test_rrf_combines_rankings(self) -> None:
        first = [SearchResult(**CHUNKS[0], score=1, method="bm25")]
        second = [SearchResult(**CHUNKS[0], score=0.9, method="dense")]
        results = reciprocal_rank_fusion([first, second], top_k=1)
        self.assertEqual(results[0].chunk_id, "1")
        self.assertEqual(results[0].method, "hybrid")


if __name__ == "__main__":
    unittest.main()
