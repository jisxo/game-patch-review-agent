from __future__ import annotations

import json
from typing import Any

import requests

from app.config import settings


class LLMConfigurationError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required for LLM or dense retrieval")
        self.base_url = settings.openai_base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json={
                "model": settings.embedding_model,
                "input": texts,
                "dimensions": settings.embedding_dimensions,
            },
            timeout=max(settings.request_timeout_seconds, 30),
        )
        response.raise_for_status()
        data = response.json().get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ValueError("invalid embeddings response")
        return [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]

    def json_completion(
        self,
        *,
        system: str,
        user: str,
        schema_name: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        payload = {
            "model": model or settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=max(settings.request_timeout_seconds, 60),
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        return json.loads(content), {
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
        }
