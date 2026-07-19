from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

from psycopg import Connection

from app.models import SearchResult
from app.repositories.chunk_repo import dense_search, list_chunks
from app.services.llm_client import OpenAICompatibleClient


TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_PATTERN.findall(text)]


def bm25_search(
    chunks: list[dict[str, Any]], query: str, top_k: int = 5, k1: float = 1.5, b: float = 0.75
) -> list[SearchResult]:
    if not chunks:
        return []
    documents = [
        tokenize(f"{item['title']} {item['section_path']} {item['content']}") for item in chunks
    ]
    query_tokens = list(dict.fromkeys(tokenize(query)))
    average_length = sum(len(document) for document in documents) / len(documents) or 1
    document_frequency = {
        token: sum(1 for document in documents if token in document) for token in query_tokens
    }
    scored: list[tuple[float, dict[str, Any]]] = []
    for item, document in zip(chunks, documents, strict=True):
        frequencies = Counter(document)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies[token]
            if frequency == 0:
                continue
            df = document_frequency[token]
            idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * len(document) / average_length)
            score += idf * frequency * (k1 + 1) / denominator
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [SearchResult(**item, score=score, method="bm25") for score, item in scored[:top_k]]


def search_chunks(
    conn: Connection,
    *,
    appid: str,
    query: str,
    method: str = "bm25",
    top_k: int = 5,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> list[SearchResult]:
    if method == "bm25":
        return bm25_search(
            list_chunks(
                conn,
                appid=appid,
                published_after=published_after,
                published_before=published_before,
            ),
            query,
            top_k,
        )
    client = OpenAICompatibleClient()
    query_embedding = client.embed([query])[0]
    dense_rows = dense_search(
        conn,
        appid=appid,
        query_embedding=query_embedding,
        top_k=max(top_k, 10),
        published_after=published_after,
        published_before=published_before,
    )
    dense_results = [SearchResult(**row, method="dense") for row in dense_rows]
    if method == "dense":
        return dense_results[:top_k]
    if method != "hybrid":
        raise ValueError(f"unsupported search method: {method}")
    bm25_results = bm25_search(
        list_chunks(
            conn,
            appid=appid,
            published_after=published_after,
            published_before=published_before,
        ),
        query,
        max(top_k, 10),
    )
    return reciprocal_rank_fusion([bm25_results, dense_results], top_k=top_k)


def reciprocal_rank_fusion(
    result_sets: list[list[SearchResult]], *, top_k: int, constant: int = 60
) -> list[SearchResult]:
    scores: dict[str, float] = {}
    values: dict[str, SearchResult] = {}
    for results in result_sets:
        for rank, result in enumerate(results, start=1):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1 / (constant + rank)
            values[result.chunk_id] = result
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [
        values[chunk_id].model_copy(update={"score": scores[chunk_id], "method": "hybrid"})
        for chunk_id in ranked[:top_k]
    ]
