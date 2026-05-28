"""Unified Pydantic schemas.

Combines the search/AI schemas from AI-job-board with the scraper/ingestion
schemas from the legacy job-board project. A single `Job` resource now carries
both compensation/AI fields and ingestion/source fields.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Job: core resource
# ---------------------------------------------------------------------------


class JobBase(BaseModel):
    """Shared fields for any job representation."""

    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"

    # Provenance / ingestion. `url` is unique in the DB so we use it as the
    # natural dedupe key for scraped rows.
    url: Optional[HttpUrl] = None
    source: Optional[str] = Field(None, max_length=100)


class JobCreate(JobBase):
    """Schema for creating a job (manual entry or ingestion)."""

    pass


class ScrapedJob(BaseModel):
    """Minimal contract returned by scraper services.

    Kept narrow on purpose: scrapers should not invent salary or AI fields.
    """

    title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    url: HttpUrl
    description: Optional[str] = None
    source: str = Field(..., min_length=1, max_length=100)


class JobResponse(JobBase):
    id: int
    posted_at: datetime
    created_at: datetime
    updated_at: datetime
    scraped_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")


class JobMatchResponse(JobResponse):
    match_score: float = Field(
        ..., ge=0.0, le=1.0, description="Similarity score (1.0 = perfect match)"
    )


# ---------------------------------------------------------------------------
# Fit analysis
# ---------------------------------------------------------------------------


class JobFitAnalysis(BaseModel):
    analysis_summary: str
    pros: List[str]
    cons: List[str]


class JobFitAnalysisRequest(BaseModel):
    user_query: str
    job_id: int


class JobFitAnalysisResponse(BaseModel):
    job: JobResponse
    fit_analysis: JobFitAnalysis


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


class ScrapeRequest(BaseModel):
    source: str = Field(..., description="Source to scrape: 'linkedin', 'indeed', 'wellfound'")
    query: Optional[str] = Field(None, description="Search keywords")
    location: Optional[str] = Field(None, description="Location filter")
    max_results: int = Field(10, ge=1, le=100, description="Max postings to fetch")
    generate_embeddings: bool = Field(
        True,
        description=(
            "If True, generate vector embeddings for newly ingested jobs so they "
            "become searchable via /search/semantic immediately."
        ),
    )


class ScrapeResultResponse(BaseModel):
    message: str
    source: str
    scraped: int
    saved: int
    skipped: int
    embedded: int
