CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS games (
    appid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    store_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collection_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    appid TEXT NOT NULL REFERENCES games(appid),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    request_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    row_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS steam_news (
    gid TEXT PRIMARY KEY,
    appid TEXT NOT NULL REFERENCES games(appid),
    title TEXT NOT NULL,
    url TEXT,
    contents TEXT,
    date TIMESTAMPTZ NOT NULL,
    feedname TEXT,
    feedlabel TEXT,
    author TEXT,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    news_type TEXT NOT NULL DEFAULT 'unknown',
    is_patch_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    collected_run_id UUID REFERENCES collection_runs(run_id) ON DELETE SET NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS steam_reviews (
    recommendationid TEXT PRIMARY KEY,
    appid TEXT NOT NULL REFERENCES games(appid),
    review TEXT NOT NULL,
    voted_up BOOLEAN NOT NULL,
    language TEXT NOT NULL,
    timestamp_created TIMESTAMPTZ NOT NULL,
    timestamp_updated TIMESTAMPTZ,
    playtime_forever INTEGER,
    playtime_at_review INTEGER,
    weighted_vote_score NUMERIC,
    votes_up INTEGER,
    comment_count INTEGER,
    collected_run_id UUID REFERENCES collection_runs(run_id) ON DELETE SET NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_steam_news_appid_date
    ON steam_news (appid, date DESC);
CREATE INDEX IF NOT EXISTS idx_steam_reviews_appid_created
    ON steam_reviews (appid, timestamp_created DESC);

INSERT INTO games (appid, name, store_url)
VALUES (
    '1049590',
    'Eternal Return',
    'https://store.steampowered.com/app/1049590/Eternal_Return/'
)
ON CONFLICT (appid) DO UPDATE
SET
    name = EXCLUDED.name,
    store_url = EXCLUDED.store_url;
