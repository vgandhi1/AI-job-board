from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List
from app.database import get_db
from app.models import Job
from app.schemas import SemanticSearchRequest, JobMatchResponse, JobFitAnalysisRequest, JobFitAnalysisResponse, JobResponse
from app.services.vector_service import generate_embedding
from app.services.fit_analysis_service import analyze_job_fit

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=List[JobMatchResponse])
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search using vector embeddings.
    
    Falls back to keyword search if vector search fails.
    """
    try:
        # Generate embedding for the query
        query_embedding = await generate_embedding(request.query)
        
        # Perform cosine similarity search
        # Using 1 - cosine_distance for similarity score (0 to 1 range)
        similarity_query = select(
            Job,
            (1 - (Job.embedding.cosine_distance(query_embedding))).label("match_score")
        ).where(
            Job.embedding.isnot(None)
        ).order_by(
            Job.embedding.cosine_distance(query_embedding)
        ).limit(request.limit)
        
        result = await db.execute(similarity_query)
        rows = result.all()
        
        if not rows:
            # Fallback to keyword search if no vector results
            return await _keyword_search_fallback(request.query, request.limit, db)
        
        # Format results
        jobs_with_scores = []
        for job, score in rows:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_currency": job.salary_currency,
                "posted_at": job.posted_at,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "match_score": float(score)
            }
            jobs_with_scores.append(JobMatchResponse(**job_dict))
        
        return jobs_with_scores
        
    except Exception as e:
        # Fallback to keyword search on error
        return await _keyword_search_fallback(request.query, request.limit, db)


async def _keyword_search_fallback(query: str, limit: int, db: AsyncSession) -> List[JobMatchResponse]:
    """Fallback keyword search when vector search fails"""
    search_terms = query.lower().split()
    
    # Build keyword search query - match any term in any field
    conditions = []
    for term in search_terms:
        conditions.append(
            or_(
                Job.title.ilike(f"%{term}%"),
                Job.description.ilike(f"%{term}%"),
                Job.company.ilike(f"%{term}%")
            )
        )
    
    keyword_query = select(Job).where(
        or_(*conditions) if conditions else True
    ).limit(limit)
    
    result = await db.execute(keyword_query)
    jobs = result.scalars().all()
    
    # Return with a default match score of 0.5 for keyword matches
    return [
        JobMatchResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            description=job.description,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            posted_at=job.posted_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
            match_score=0.5  # Default score for keyword matches
        )
        for job in jobs
    ]


@router.post("/analyze-fit", response_model=JobFitAnalysisResponse)
async def analyze_job_fit_endpoint(
    request: JobFitAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze job fit for a specific job based on user query.
    Runs on-demand to save latency and API costs.
    """
    # Fetch the job
    result = await db.execute(select(Job).where(Job.id == request.job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Perform fit analysis
    fit_analysis = await analyze_job_fit(request.user_query, job.description)
    
    return JobFitAnalysisResponse(
        job=JobResponse.model_validate(job),
        fit_analysis=fit_analysis
    )
