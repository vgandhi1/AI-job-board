"""Aggregate stats for the job board (async)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Return totals plus breakdowns by source and top cities."""
    total = (await db.execute(select(func.count(Job.id)))).scalar_one()

    by_source_rows = (
        await db.execute(
            select(Job.source, func.count(Job.id)).group_by(Job.source)
        )
    ).all()

    top_cities_rows = (
        await db.execute(
            select(Job.city, func.count(Job.id))
            .where(Job.city.isnot(None))
            .group_by(Job.city)
            .order_by(func.count(Job.id).desc())
            .limit(10)
        )
    ).all()

    return {
        "total_jobs": total,
        "by_source": {source or "unknown": count for source, count in by_source_rows},
        "top_cities": {city: count for city, count in top_cities_rows},
    }
