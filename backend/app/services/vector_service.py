"""Embedding generation service.

Provider-agnostic: routes to OpenAI or Ollama based on `LLM_PROVIDER`.
The client is constructed lazily so the app can boot without either
provider configured (errors surface only when an embedding is requested).
"""
from typing import List

from app.config import settings
from app.services.llm_client import get_embedding_model, get_llm_client


async def generate_embedding(text: str) -> List[float]:
    """Embed `text` using the currently configured provider/model.

    The returned vector's length is determined by the model:
      - OpenAI text-embedding-3-small : 1536
      - Ollama nomic-embed-text       : 768
      - Ollama mxbai-embed-large      : 1024
    `settings.embedding_dimension` MUST match - see config docstring.
    """
    client = get_llm_client()
    try:
        response = await client.embeddings.create(
            model=get_embedding_model(),
            input=text,
        )
    except Exception as e:
        # Surface a generic message to callers; do not leak full exception
        # text or request payload (may contain candidate query / job body).
        raise ValueError(
            f"Failed to generate embedding via provider={settings.llm_provider}: "
            f"{type(e).__name__}"
        ) from e

    return response.data[0].embedding


def prepare_job_text(job_title: str, job_description: str, company: str) -> str:
    """Concatenate the fields used as the embedding source.

    Kept stable across providers so backfill works regardless of which
    embedding model is active at the time.
    """
    return f"{job_title}\n{company}\n{job_description}"
