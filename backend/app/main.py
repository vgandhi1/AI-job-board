"""Unified FastAPI application entry point.

Hosts both AI-powered search (semantic + fit analysis) and the ingestion API
(scraper + jobs CRUD + stats) under a single app, sharing one DB schema.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import jobs, scrape, search, stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered job board with semantic search, fit analysis, and a "
        "Playwright-based scraping/ingestion pipeline."
    ),
    version="2.0.0",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# In production, prefer an Nginx reverse proxy so frontend and backend share
# an origin and CORS is unnecessary. In dev, allow localhost origins.
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
if settings.debug:
    # Wildcard is fine in DEBUG only; never enable in production.
    cors_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(search.router)
app.include_router(jobs.router)
app.include_router(scrape.router)
app.include_router(stats.router)


# ---------------------------------------------------------------------------
# Meta endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "message": "AI Job Board API",
        "version": "2.0.0",
        "endpoints": {
            "semantic_search": "POST /search/semantic",
            "analyze_fit": "POST /search/analyze-fit",
            "list_jobs": "GET /jobs",
            "job_by_id": "GET /jobs/{job_id}",
            "jobs_by_city": "GET /jobs/city/{city}",
            "jobs_by_company": "GET /jobs/company/{company}",
            "scrape": "POST /scrape",
            "scrape_async": "POST /scrape/async",
            "stats": "GET /stats",
            "health": "GET /health",
            "api_status": "GET /api/v1/status",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/status")
async def api_status():
    return {"status": "healthy", "service": "ai-job-board-api", "version": "2.0.0"}
