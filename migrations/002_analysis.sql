CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE steam_news
    ADD COLUMN IF NOT EXISTS news_type TEXT NOT NULL DEFAULT 'unknown';

CREATE TABLE IF NOT EXISTS patch_window_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appid TEXT NOT NULL REFERENCES games(appid),
    patch_gid TEXT NOT NULL REFERENCES steam_news(gid),
    analysis_reference_at TIMESTAMPTZ NOT NULL,
    reference_time_source TEXT NOT NULL DEFAULT 'steam_news_date',
    window_days INTEGER NOT NULL,
    before_start TIMESTAMPTZ NOT NULL,
    before_end TIMESTAMPTZ NOT NULL,
    after_start TIMESTAMPTZ NOT NULL,
    after_end TIMESTAMPTZ NOT NULL,
    before_count INTEGER NOT NULL,
    after_count INTEGER NOT NULL,
    before_positive INTEGER NOT NULL,
    after_positive INTEGER NOT NULL,
    before_positive_ratio DOUBLE PRECISION,
    after_positive_ratio DOUBLE PRECISION,
    percentage_point_change DOUBLE PRECISION,
    min_reviews_per_window INTEGER NOT NULL,
    eligible BOOLEAN NOT NULL,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    keyword_rules_version TEXT NOT NULL,
    keyword_results JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (patch_gid, window_days, min_reviews_per_window, keyword_rules_version)
);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gid TEXT NOT NULL REFERENCES steam_news(gid) ON DELETE CASCADE,
    appid TEXT NOT NULL REFERENCES games(appid),
    chunk_index INTEGER NOT NULL,
    section_path TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(1536),
    chunking_version TEXT NOT NULL,
    embedding_model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (gid, chunk_index, chunking_version)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_appid
    ON document_chunks (appid);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS review_issue_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id TEXT NOT NULL REFERENCES steam_reviews(recommendationid) ON DELETE CASCADE,
    method TEXT NOT NULL,
    model TEXT,
    prompt_version TEXT NOT NULL,
    issue_types JSONB NOT NULL,
    summary TEXT NOT NULL,
    evidence_spans JSONB NOT NULL,
    expression_intensity TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    raw_output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (review_id, method, prompt_version, model)
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    analysis_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES patch_window_reports(report_id),
    status TEXT NOT NULL DEFAULT 'created',
    llm_model TEXT,
    embedding_model TEXT,
    prompt_version TEXT NOT NULL,
    index_version TEXT NOT NULL,
    request_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    report JSONB,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd DOUBLE PRECISION,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS retrieval_runs (
    retrieval_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID REFERENCES analysis_runs(analysis_run_id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    method TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    results JSONB NOT NULL,
    latency_ms INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eval_examples (
    example_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    input JSONB NOT NULL,
    expected JSONB NOT NULL,
    dataset_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eval_results (
    eval_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    example_id TEXT NOT NULL REFERENCES eval_examples(example_id),
    run_version TEXT NOT NULL,
    prediction JSONB NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
