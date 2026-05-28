"""Ingestion subsystem.

Bridges scraped postings (`ScrapedJob` from `scraper_service`) into the
unified `jobs` table using async SQLAlchemy, and optionally generates an
OpenAI embedding so the job is immediately searchable.

This is the only writer that touches the DB on the scraper path; routers and
scripts call into here so dedupe/embedding behavior stays consistent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job
from app.schemas import ScrapedJob
from app.services.vector_service import generate_embedding, prepare_job_text

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    scraped: int
    saved: int
    skipped: int
    embedded: int


async def ingest_scraped_jobs(
    db: AsyncSession,
    scraped_jobs: Iterable[ScrapedJob],
    *,
    generate_embeddings: bool = True,
) -> IngestionResult:
    """Upsert scraped jobs into the DB.

    Dedupe key: `url`. If a job with the same URL already exists, it is
    skipped (no update). Pass `generate_embeddings=False` to defer embedding
    work to the `backfill_embeddings` script.
    """
    scraped_list: List[ScrapedJob] = list(scraped_jobs)
    saved = 0
    skipped = 0
    embedded = 0

    for scraped in scraped_list:
        url_str = str(scraped.url)

        # Dedupe by URL (unique index in DB also enforces this, but checking
        # first avoids noisy IntegrityError -> rollback cycles).
        existing = await db.execute(select(Job).where(Job.url == url_str))
        if existing.scalar_one_or_none() is not None:
            skipped += 1
            continue

        job = Job(
            title=scraped.title,
            company=scraped.company,
            city=scraped.city,
            location=scraped.city,  # best-effort: scraped city == location
            url=url_str,
            description=scraped.description,
            source=scraped.source,
        )

        if generate_embeddings and scraped.description:
            try:
                text = prepare_job_text(scraped.title, scraped.description, scraped.company)
                job.embedding = await generate_embedding(text)
                embedded += 1
            except Exception as e:
                # Embedding failure should not block ingestion - the job is
                # still saved and can be backfilled later.
                logger.warning(
                    "Embedding failed for job '%s' at '%s': %s",
                    scraped.title, scraped.company, type(e).__name__,
                )

        db.add(job)
        saved += 1

    await db.commit()
    logger.info(
        "Ingestion: scraped=%d, saved=%d, skipped=%d, embedded=%d",
        len(scraped_list), saved, skipped, embedded,
    )
    return IngestionResult(
        scraped=len(scraped_list),
        saved=saved,
        skipped=skipped,
        embedded=embedded,
    )
