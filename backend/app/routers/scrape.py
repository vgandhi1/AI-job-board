"""Scraping endpoints.

POST /scrape          - synchronous scrape + ingest
POST /scrape/async    - kicks off scrape + ingest in a background task

Both endpoints share the same scraping/ingestion code paths
(`scraper_service` + `ingestion_service`) so there is exactly one writer.
"""
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.schemas import ScrapeRequest, ScrapeResultResponse
from app.services.ingestion_service import ingest_scraped_jobs
from app.services.scraper_service import get_scraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("", response_model=ScrapeResultResponse)
async def scrape_jobs(request: ScrapeRequest, db: AsyncSession = Depends(get_db)):
    """Scrape `request.source` and persist results synchronously."""
    try:
        scraper = get_scraper(request.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        scraped = await scraper.scrape(
            query=request.query,
            location=request.location,
            max_results=request.max_results,
        )
    except Exception as e:
        # Do not surface raw exception messages (may include page HTML, URLs,
        # or other sensitive scrape detail) to the API client.
        logger.error("Scrape failed for source=%s: %s", request.source, type(e).__name__)
        raise HTTPException(status_code=502, detail="Scrape source unavailable")

    if not scraped:
        return ScrapeResultResponse(
            message="No jobs found",
            source=request.source,
            scraped=0,
            saved=0,
            skipped=0,
            embedded=0,
        )

    result = await ingest_scraped_jobs(
        db,
        scraped,
        generate_embeddings=request.generate_embeddings,
    )
    return ScrapeResultResponse(
        message=f"Successfully scraped {result.scraped} jobs from {request.source}",
        source=request.source,
        scraped=result.scraped,
        saved=result.saved,
        skipped=result.skipped,
        embedded=result.embedded,
    )


@router.post("/async")
async def scrape_jobs_async(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Schedule the scrape+ingest to run in the background.

    Returns immediately with a `processing` status. Results are visible via
    `GET /jobs` once the background task completes.
    """
    # Validate source up-front so the caller gets a clear 400 instead of a
    # silent background failure.
    try:
        get_scraper(request.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def _run() -> None:
        try:
            scraper = get_scraper(request.source)
            scraped = await scraper.scrape(
                query=request.query,
                location=request.location,
                max_results=request.max_results,
            )
            async with AsyncSessionLocal() as session:
                await ingest_scraped_jobs(
                    session,
                    scraped,
                    generate_embeddings=request.generate_embeddings,
                )
        except Exception as e:
            logger.error(
                "Background scrape failed for source=%s: %s",
                request.source, type(e).__name__,
            )

    def _schedule() -> None:
        # BackgroundTasks runs callables in a thread; bridge to the running
        # event loop with asyncio.run for this isolated coroutine.
        asyncio.run(_run())

    background_tasks.add_task(_schedule)
    return {
        "message": f"Scraping started in background for {request.source}",
        "status": "processing",
    }
