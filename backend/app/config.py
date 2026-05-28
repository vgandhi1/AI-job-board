"""Application configuration.

Reads from a single project-root `.env` file. Two LLM providers are
supported:

  - "openai"  (default): hosted OpenAI APIs. Requires OPENAI_API_KEY.
  - "ollama":            local Ollama server. Reached via its OpenAI-compatible
                         `/v1` endpoint so we can keep using the openai SDK.
                         No API key required (Ollama ignores it).

`embedding_dimension` MUST match the embedding model in use. Mismatch will
break the pgvector column. See `scripts/reset_embedding_dimension.py` for the
safe way to switch.
"""
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project-root .env (parent of backend/).
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobboard"

    # --- LLM provider switch ---
    # "openai" or "ollama". Keep OpenAI as default so existing setups don't break.
    llm_provider: Literal["openai", "ollama"] = "openai"

    # --- OpenAI (used when llm_provider == "openai") ---
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_analysis_model: str = "gpt-4o-mini"

    # --- Ollama (used when llm_provider == "ollama") ---
    # Default points at the WSL2 gateway, which is how WSL reaches the Windows
    # host where Ollama runs. In docker-compose we override this to
    # http://host.docker.internal:11434 via env.
    # Operator-controlled value, never sourced from user input.
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_embedding_model: str = "nomic-embed-text"   # 768 dims
    ollama_analysis_model: str = "llama3.1"
    # Ollama doesn't require an API key, but the openai SDK requires a non-empty
    # string. Override only if you've put Ollama behind an auth proxy.
    ollama_api_key: str = "ollama"

    # --- Embedding dimension ---
    # MUST match the embedding model. Defaults to OpenAI text-embedding-3-small.
    # Common values:
    #   OpenAI text-embedding-3-small : 1536
    #   OpenAI text-embedding-3-large : 3072
    #   Ollama nomic-embed-text       : 768
    #   Ollama mxbai-embed-large      : 1024
    #   Ollama bge-large              : 1024
    #   Ollama all-minilm             : 384
    # If you change this, run scripts/reset_embedding_dimension.py.
    embedding_dimension: int = 1536

    # --- App ---
    app_name: str = "AI Job Board API"
    debug: bool = False

    @field_validator("ollama_base_url")
    @classmethod
    def _validate_ollama_url(cls, v: str) -> str:
        # Operator-controlled URL; we still reject obviously wrong values to
        # surface misconfiguration early (per the workspace SSRF prevention
        # rule's "Restrict Allowed Protocols and Ports" guideline).
        if not v:
            return v
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(
                "OLLAMA_BASE_URL must start with http:// or https:// "
                f"(got: {v!r})"
            )
        return v.rstrip("/")


settings = Settings()
