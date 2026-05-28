"""Jobs CRUD + stats endpoints (async).

Ported from the legacy job-board sync router to the AI-job-board async stack.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job
from app.schemas import JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _page_from_offset(skip: int, limit: int) -> int:
    return skip // limit + 1 if limit > 0 else 1


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    source: Optional[str] = Query(None, description="Filter by source"),
    city: Optional[str] = Query(None, description="Filter by city"),
    company: Optional[str] = Query(None, description="Filter by company"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated job list with optional filters."""
    filters = []
    if source:
        filters.append(Job.source.ilike(f"%{source}%"))
    if city:
        filters.append(Job.city.ilike(f"%{city}%"))
    if company:
        filters.append(Job.company.ilike(f"%{company}%"))

    total_stmt = select(func.count(Job.id))
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = (await db.execute(total_stmt)).scalar_one()

    list_stmt = select(Job)
    if filters:
        list_stmt = list_stmt.where(*filters)
    list_stmt = list_stmt.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    rows = (await db.execute(list_stmt)).scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in rows],
        total=total,
        page=_page_from_offset(skip, limit),
        page_size=limit,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.get("/city/{city}", response_model=JobListResponse)
async def list_jobs_by_city(
    city: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filt = Job.city.ilike(f"%{city}%")
    total = (await db.execute(select(func.count(Job.id)).where(filt))).scalar_one()
    rows = (
        await db.execute(
            select(Job).where(filt).order_by(Job.created_at.desc()).offset(skip).limit(limit)
        )
    ).scalars().all()
    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in rows],
        total=total,
        page=_page_from_offset(skip, limit),
        page_size=limit,
    )


@router.get("/company/{company}", response_model=JobListResponse)
async def list_jobs_by_company(
    company: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filt = Job.company.ilike(f"%{company}%")
    total = (await db.execute(select(func.count(Job.id)).where(filt))).scalar_one()
    rows = (
        await db.execute(
            select(Job).where(filt).order_by(Job.created_at.desc()).offset(skip).limit(limit)
        )
    ).scalars().all()
    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in rows],
        total=total,
        page=_page_from_offset(skip, limit),
        page_size=limit,
    )


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    # NOTE: This endpoint currently has no authentication. Per the workspace
    # auth rule, a destructive endpoint like DELETE should require an
    # authenticated caller with appropriate permissions. Wire FastAPI
    # dependency-injected auth here before exposing this to untrusted clients.
    job = (await db.execute(select(Job).where(Job.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()
    return {"message": f"Job {job_id} deleted successfully"}
