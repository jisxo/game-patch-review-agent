from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from psycopg import Connection

from app.config import settings
from app.api.dashboard import DASHBOARD_HTML
from app.db import get_connection
from app.repositories.news_repo import list_patch_candidates
from app.services.analysis import calculate_patch_coverage
from app.services.indexing import index_news_documents
from app.services.llm_client import LLMConfigurationError
from app.services.pipeline import run_patch_report
from app.services.search import search_chunks


app = FastAPI(
    title="Game Update Reaction Analyzer",
    version="1.0.0",
    description="Evidence-linked analysis of Steam reviews around game updates.",
)


def database() -> Generator[Connection, None, None]:
    with get_connection() as conn:
        yield conn


Database = Annotated[Connection, Depends(database)]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/health")
def health(conn: Database) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    return {"status": "ok"}


@app.get("/patches")
def patches(conn: Database, appid: str = settings.default_appid) -> list[dict]:
    return list_patch_candidates(conn, appid)


@app.get("/coverage")
def coverage(
    conn: Database,
    appid: str = settings.default_appid,
    window_days: int = Query(settings.default_window_days, ge=1, le=90),
    min_reviews: int = Query(settings.min_reviews_per_window, ge=1),
) -> list[dict]:
    return [
        item.model_dump()
        for item in calculate_patch_coverage(
            conn,
            appid=appid,
            window_days=window_days,
            min_reviews=min_reviews,
        )
    ]


@app.post("/index")
def index_documents(
    conn: Database,
    appid: str = settings.default_appid,
    with_embeddings: bool = False,
) -> dict[str, int]:
    try:
        result = index_news_documents(conn, appid=appid, with_embeddings=with_embeddings)
        conn.commit()
        return result
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/search")
def search(
    conn: Database,
    query: str = Query(min_length=2, max_length=500),
    appid: str = settings.default_appid,
    method: Literal["bm25", "dense", "hybrid"] = "bm25",
    top_k: int = Query(5, ge=1, le=20),
) -> list[dict]:
    try:
        return [
            item.model_dump()
            for item in search_chunks(conn, appid=appid, query=query, method=method, top_k=top_k)
        ]
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/reports/{patch_gid}")
def report(
    patch_gid: str,
    conn: Database,
    method: Literal["bm25", "dense", "hybrid"] = "bm25",
    issue_method: Literal["baseline", "llm"] = "baseline",
    generation_method: Literal["deterministic", "llm"] = "deterministic",
    top_k: int = Query(5, ge=1, le=20),
) -> dict:
    try:
        result = run_patch_report(
            conn,
            patch_gid=patch_gid,
            search_method=method,
            top_k=top_k,
            issue_method=issue_method,
            generation_method=generation_method,
        )
        conn.commit()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
