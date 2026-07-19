from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://game:game@localhost:5432/game_reaction"

    default_appid: str = "1049590"
    default_language: str = "koreana"

    request_timeout_seconds: int = 10
    request_sleep_seconds: int = 1
    max_retry_count: int = 3

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    default_window_days: int = 7
    min_reviews_per_window: int = 30
    keyword_rules_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
