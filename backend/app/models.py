"""Unified SQLAlchemy models.

The Job model combines two strands:
  - AI-job-board: semantic-search/AI fields (description, embedding, salary, etc.)
  - job-board:    ingestion/source-tracking fields (url, source, city, scraped_at)

Description is nullable because scraped postings may not include a body until
they are enriched downstream.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.config import settings
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # --- Core posting metadata (always present) ---
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # --- Location ---
    # `location` is the free-form location string (e.g. "San Francisco, CA").
    # `city` is the normalized first segment, used for filter/aggregation.
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True, index=True)

    # --- Compensation (optional, may not be on scraped postings) ---
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")

    # --- Ingestion / provenance ---
    # `source` records where the row came from: "linkedin", "indeed", "wellfound",
    # "manual", "sample", etc. Sample/manual rows are allowed to have NULL url.
    url = Column(String(500), nullable=True, unique=True, index=True)
    source = Column(String(100), nullable=True, index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    # --- Timestamps ---
    posted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # --- AI / Semantic search ---
    # Dim is driven by settings.embedding_dimension so OpenAI and Ollama
    # (with different embedding models) can both be supported. Defaults to
    # 1536 (OpenAI text-embedding-3-small). If you change EMBEDDING_DIMENSION
    # in .env, run scripts/reset_embedding_dimension.py to resize the column.
    # Nullable so a job can be ingested first and embedded later.
    embedding = Column(Vector(settings.embedding_dimension), nullable=True)

    __table_args__ = (
        Index("idx_title_company_city", "title", "company", "city"),
    )

    def __repr__(self) -> str:
        return (
            f"<Job(id={self.id}, title='{self.title}', "
            f"company='{self.company}', source='{self.source}')>"
        )
