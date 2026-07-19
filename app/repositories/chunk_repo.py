from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg import Connection

from app.services.text_processing import TextChunk


def upsert_chunks(
    conn: Connection,
    *,
    appid: str,
    gid: str,
    chunks: list[TextChunk],
    chunking_version: str,
    embeddings: list[list[float]] | None = None,
    embedding_model: str | None = None,
) -> int:
    if embeddings is not None and len(embeddings) != len(chunks):
        raise ValueError("embedding count must match chunk count")
    query = """
        INSERT INTO document_chunks (
            gid, appid, chunk_index, section_path, content, content_hash,
            embedding, chunking_version, embedding_model
        ) VALUES (
            %(gid)s, %(appid)s, %(chunk_index)s, %(section_path)s,
            %(content)s, %(content_hash)s, %(embedding)s::vector,
            %(chunking_version)s, %(embedding_model)s
        )
        ON CONFLICT (gid, chunk_index, chunking_version) DO UPDATE SET
            section_path = EXCLUDED.section_path,
            content = EXCLUDED.content,
            content_hash = EXCLUDED.content_hash,
            embedding = EXCLUDED.embedding,
            embedding_model = EXCLUDED.embedding_model,
            created_at = NOW();
    """
    with conn.cursor() as cur:
        for index, chunk in enumerate(chunks):
            embedding = embeddings[index] if embeddings is not None else None
            cur.execute(
                query,
                {
                    "gid": gid,
                    "appid": appid,
                    "chunk_index": chunk.chunk_index,
                    "section_path": chunk.section_path,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "embedding": _vector_literal(embedding),
                    "chunking_version": chunking_version,
                    "embedding_model": embedding_model,
                },
            )
    return len(chunks)


def _vector_literal(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(str(value) for value in vector) + "]"


def list_chunks(
    conn: Connection,
    *,
    appid: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT c.chunk_id::text, c.gid, n.title, c.section_path, c.content
        FROM document_chunks c
        JOIN steam_news n ON n.gid = c.gid
        WHERE c.appid = %(appid)s
          AND (%(published_after)s::timestamptz IS NULL
               OR n.date >= %(published_after)s::timestamptz)
          AND (%(published_before)s::timestamptz IS NULL
               OR n.date < %(published_before)s::timestamptz)
        ORDER BY n.date DESC, c.chunk_index;
    """
    with conn.cursor() as cur:
        cur.execute(
            query,
            {
                "appid": appid,
                "published_after": published_after,
                "published_before": published_before,
            },
        )
        rows = cur.fetchall()
    return [
        {
            "chunk_id": row[0],
            "gid": row[1],
            "title": row[2],
            "section_path": row[3],
            "content": row[4],
        }
        for row in rows
    ]


def dense_search(
    conn: Connection,
    *,
    appid: str,
    query_embedding: list[float],
    top_k: int,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT c.chunk_id::text, c.gid, n.title, c.section_path, c.content,
               1 - (c.embedding <=> %(vector)s::vector) AS score
        FROM document_chunks c
        JOIN steam_news n ON n.gid = c.gid
        WHERE c.appid = %(appid)s AND c.embedding IS NOT NULL
          AND (%(published_after)s::timestamptz IS NULL
               OR n.date >= %(published_after)s::timestamptz)
          AND (%(published_before)s::timestamptz IS NULL
               OR n.date < %(published_before)s::timestamptz)
        ORDER BY c.embedding <=> %(vector)s::vector
        LIMIT %(top_k)s;
    """
    vector = _vector_literal(query_embedding)
    with conn.cursor() as cur:
        cur.execute(
            query,
            {
                "vector": vector,
                "appid": appid,
                "top_k": top_k,
                "published_after": published_after,
                "published_before": published_before,
            },
        )
        rows = cur.fetchall()
    return [
        {
            "chunk_id": row[0],
            "gid": row[1],
            "title": row[2],
            "section_path": row[3],
            "content": row[4],
            "score": float(row[5]),
        }
        for row in rows
    ]
