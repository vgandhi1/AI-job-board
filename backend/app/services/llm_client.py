"""Provider-aware LLM client factory.

This is the single place that decides whether to talk to OpenAI or to a local
Ollama server. Both providers are reached via the same `openai.AsyncOpenAI`
SDK - we just swap `base_url`. That works because Ollama exposes an
OpenAI-compatible API at `/v1/*` (chat completions + embeddings).

All other services should call `get_llm_client()` / `get_embedding_model()` /
`get_analysis_model()` instead of constructing clients themselves. This:

  - Defers credential validation until the first API call (so the app can
    boot even when one provider is unconfigured).
  - Keeps provider switching to a single env var (`LLM_PROVIDER`).
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings


_PLACEHOLDER_OPENAI_KEY = "your_openai_api_key_here"


def get_llm_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client wired up for the configured provider.

    Raises ValueError if the configured provider is missing required
    credentials. Called lazily by callers so import-time side effects don't
    crash the app on boot.
    """
    if settings.llm_provider == "ollama":
        # Ollama doesn't actually validate the API key, but the SDK refuses
        # to construct with an empty string, so we pass a placeholder.
        if not settings.ollama_base_url:
            raise ValueError(
                "OLLAMA_BASE_URL is not set. "
                "Set it in .env when LLM_PROVIDER=ollama."
            )
        return AsyncOpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key=settings.ollama_api_key or "ollama",
        )

    # openai
    if (
        not settings.openai_api_key
        or settings.openai_api_key == _PLACEHOLDER_OPENAI_KEY
    ):
        raise ValueError(
            "OPENAI_API_KEY is not set. Set it in .env, or switch to a local "
            "model with LLM_PROVIDER=ollama."
        )
    return AsyncOpenAI(api_key=settings.openai_api_key)


def get_embedding_model() -> str:
    """Embedding model name for the configured provider."""
    return (
        settings.ollama_embedding_model
        if settings.llm_provider == "ollama"
        else settings.openai_embedding_model
    )


def get_analysis_model() -> str:
    """Chat/analysis model name for the configured provider."""
    return (
        settings.ollama_analysis_model
        if settings.llm_provider == "ollama"
        else settings.openai_analysis_model
    )


def provider_label() -> str:
    """Human-readable provider name (for logs and `/health` style endpoints)."""
    return settings.llm_provider
