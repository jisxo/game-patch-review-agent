import os

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.db import get_connection
from app.repositories.chunk_repo import dense_search, upsert_chunks
from app.services.text_processing import TextChunk


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="set RUN_INTEGRATION=1 with the PostgreSQL container running",
)


def test_core_api_flow() -> None:
    client = TestClient(app)
    checks = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/patches"),
        ("GET", "/coverage?window_days=7&min_reviews=30"),
        ("GET", "/search?query=server%20connection&method=bm25&top_k=3"),
    ]
    for method, path in checks:
        response = client.request(method, path)
        assert response.status_code == 200, response.text


def test_pgvector_dense_search() -> None:
    vector = [1.0] + [0.0] * 1535
    chunk = TextChunk(
        chunk_index=0,
        section_path="Integration Test",
        content="matchmaking integration test document",
        content_hash="integration-test-hash",
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO steam_news (
                    gid, appid, title, contents, date, news_type, is_patch_candidate
                ) VALUES (
                    'integration-test-news', '1049590', 'Integration Test',
                    'temporary', NOW(), 'unknown', FALSE
                ) ON CONFLICT (gid) DO NOTHING;
                """
            )
        upsert_chunks(
            conn,
            appid="1049590",
            gid="integration-test-news",
            chunks=[chunk],
            chunking_version="integration-test",
            embeddings=[vector],
            embedding_model="integration-test",
        )
        results = dense_search(conn, appid="1049590", query_embedding=vector, top_k=1)
        assert results[0]["gid"] == "integration-test-news"
        assert results[0]["score"] == pytest.approx(1.0)
        conn.rollback()
