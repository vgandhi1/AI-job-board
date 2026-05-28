"""Resize the `jobs.embedding` pgvector column to match `EMBEDDING_DIMENSION`.

When you switch LLM providers (e.g. OpenAI -> Ollama) the embedding model
changes, and so does the vector length:

    OpenAI text-embedding-3-small : 1536
    OpenAI text-embedding-3-large : 3072
    Ollama nomic-embed-text       :  768
    Ollama mxbai-embed-large      : 1024

The pgvector type stores the dimension as part of the column definition, so
switching providers requires:

  1. Drop the HNSW index on `embedding`.
  2. NULL out existing embeddings (they're useless at the new dim).
  3. Alter the column to the new vector length.
  4. Recreate the HNSW index.
  5. Re-embed via `scripts/backfill_embeddings.py`.

This script does steps 1-4. Step 5 is run separately so you can choose to
defer (e.g. during off-hours).

DANGER: this drops every embedding in the DB. Job rows are kept; the model
file `app/models.py` reads the new dimension from `settings.embedding_dimension`,
so the ORM and DB stay in sync after this runs.

Usage:
    cd backend
    # 1. Edit .env -> set LLM_PROVIDER, embedding model, EMBEDDING_DIMENSION
    # 2. Run this script
    uv run python scripts/reset_embedding_dimension.py
    # or:  python scripts/reset_embedding_dimension.py
    # 3. (optional) Re-embed:
    uv run python scripts/backfill_embeddings.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `python scripts/...` invocation from the backend/ directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import engine  # noqa: E402


# Built into the pgvector docs; the index name we create in migration 001.
_INDEX_NAME = "jobs_embedding_idx"


async def reset() -> None:
    dim = int(settings.embedding_dimension)
    if dim < 1 or dim > 16000:
        # pgvector supports up to 16000 dims.
        raise SystemExit(f"Refusing to resize: invalid EMBEDDING_DIMENSION={dim}.")

    print(f"Provider          : {settings.llm_provider}")
    print(f"Target dimension  : {dim}")
    print(f"This will DROP existing embeddings.")
    confirm = input("Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    async with engine.begin() as conn:
        print("[1/4] Dropping HNSW index (if present)...")
        await conn.execute(text(f"DROP INDEX IF EXISTS {_INDEX_NAME}"))

        print("[2/4] Clearing existing embeddings...")
        await conn.execute(text("UPDATE jobs SET embedding = NULL"))

        print(f"[3/4] Altering embedding column to vector({dim})...")
        # Two-step alter: drop & re-add. ALTER COLUMN ... TYPE vector(N)
        # works on empty columns but is fussy across pgvector versions, so
        # we just recreate the column - safer and well-supported.
        await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS embedding"))
        await conn.execute(text(f"ALTER TABLE jobs ADD COLUMN embedding vector({dim})"))

        print(f"[4/4] Recreating HNSW index ({_INDEX_NAME})...")
        await conn.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS {_INDEX_NAME}
                ON jobs
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
                """
            )
        )

    print("Done.")
    print("Next step: run `python scripts/backfill_embeddings.py` to repopulate.")


if __name__ == "__main__":
    asyncio.run(reset())
