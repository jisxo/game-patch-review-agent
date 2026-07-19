from __future__ import annotations

from time import perf_counter
from typing import Any

from psycopg import Connection

from app.config import settings
from app.repositories.analysis_repo import (
    finish_analysis_run,
    save_retrieval_run,
    start_analysis_run,
)
from app.services.analysis import analyze_patch_window
from app.services.reporting import (
    build_grounded_report,
    build_grounded_report_with_llm,
    retrieval_query_from_analysis,
)
from app.services.search import search_chunks


def run_patch_report(
    conn: Connection,
    *,
    patch_gid: str,
    search_method: str = "bm25",
    top_k: int = 5,
    window_days: int | None = None,
    min_reviews: int | None = None,
    issue_method: str = "baseline",
    generation_method: str = "deterministic",
) -> dict[str, Any]:
    started_at = perf_counter()
    report_id, analysis = analyze_patch_window(
        conn,
        patch_gid=patch_gid,
        window_days=window_days,
        min_reviews=min_reviews,
        issue_method=issue_method,
    )
    request_params = {
        "patch_gid": patch_gid,
        "search_method": search_method,
        "top_k": top_k,
        "window_days": window_days,
        "min_reviews": min_reviews,
        "issue_method": issue_method,
        "generation_method": generation_method,
    }
    analysis_run_id = start_analysis_run(
        conn,
        report_id=report_id,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        prompt_version="grounded-report-v1",
        index_version="section-v1",
        request_params=request_params,
    )
    query = retrieval_query_from_analysis(analysis)
    retrieval_started_at = perf_counter()
    results = search_chunks(
        conn,
        appid=analysis["patch"]["appid"],
        query=query,
        method=search_method,
        top_k=top_k,
        published_after=analysis["before_start"],
        published_before=analysis["after_end"],
    )
    retrieval_ms = int((perf_counter() - retrieval_started_at) * 1000)
    serialized_results = [item.model_dump() for item in results]
    save_retrieval_run(
        conn,
        analysis_run_id=analysis_run_id,
        query_text=query,
        method=search_method,
        top_k=top_k,
        results=serialized_results,
        latency_ms=retrieval_ms,
    )
    if generation_method == "llm":
        report, usage = build_grounded_report_with_llm(
            report_id=str(report_id), analysis=analysis, retrieval_results=results
        )
    elif generation_method == "deterministic":
        report = build_grounded_report(
            report_id=str(report_id), analysis=analysis, retrieval_results=results
        )
        usage = {"input_tokens": 0, "output_tokens": 0}
    else:
        raise ValueError(f"unsupported generation method: {generation_method}")
    response = {
        "report_id": str(report_id),
        "analysis_run_id": str(analysis_run_id),
        "query": query,
        "search_method": search_method,
        "issue_method": issue_method,
        "generation_method": generation_method,
        "usage": usage,
        "analysis": analysis,
        "retrieval_results": serialized_results,
        "report": report.model_dump(),
    }
    finish_analysis_run(
        conn,
        analysis_run_id=analysis_run_id,
        status="completed",
        latency_ms=int((perf_counter() - started_at) * 1000),
        report=response,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )
    return response
