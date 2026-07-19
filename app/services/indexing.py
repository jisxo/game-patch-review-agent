from __future__ import annotations

from psycopg import Connection

from app.config import settings
from app.repositories.chunk_repo import upsert_chunks
from app.repositories.news_repo import list_news_for_indexing
from app.services.llm_client import OpenAICompatibleClient
from app.services.text_processing import chunk_document


CHUNKING_VERSION = "section-v1"


def index_news_documents(
    conn: Connection,
    *,
    appid: str,
    with_embeddings: bool = False,
) -> dict[str, int]:
    documents = list_news_for_indexing(conn, appid)
    indexed_documents = 0
    indexed_chunks = 0
    client = OpenAICompatibleClient() if with_embeddings else None

    for document in documents:
        chunks = chunk_document(title=document["title"], content=document["contents"])
        if not chunks:
            continue
        embeddings = client.embed([chunk.content for chunk in chunks]) if client else None
        indexed_chunks += upsert_chunks(
            conn,
            appid=appid,
            gid=document["gid"],
            chunks=chunks,
            chunking_version=CHUNKING_VERSION,
            embeddings=embeddings,
            embedding_model=settings.embedding_model if embeddings else None,
        )
        indexed_documents += 1
    return {"documents": indexed_documents, "chunks": indexed_chunks}
