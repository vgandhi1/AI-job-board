"""
Utility script to backfill embeddings for existing job records.
Run this after setting up the database and OpenAI API key.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models import Job
from app.services.vector_service import generate_embedding, prepare_job_text


async def backfill_embeddings(batch_size: int = 10):
    """
    Backfill embeddings for all jobs that don't have embeddings yet.
    
    Args:
        batch_size: Number of jobs to process in each batch
    """
    async with AsyncSessionLocal() as session:
        # Get all jobs without embeddings
        result = await session.execute(
            select(Job).where(Job.embedding.is_(None))
        )
        jobs = result.scalars().all()
        
        total_jobs = len(jobs)
        print(f"Found {total_jobs} jobs without embeddings")
        
        if total_jobs == 0:
            print("All jobs already have embeddings!")
            return
        
        processed = 0
        for i in range(0, total_jobs, batch_size):
            batch = jobs[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1} ({len(batch)} jobs)...")
            
            for job in batch:
                try:
                    # Prepare text for embedding
                    job_text = prepare_job_text(job.title, job.description, job.company)
                    
                    # Generate embedding
                    embedding = await generate_embedding(job_text)
                    
                    # Update job with embedding
                    job.embedding = embedding
                    processed += 1
                    
                    if processed % 10 == 0:
                        print(f"  Processed {processed}/{total_jobs} jobs...")
                        
                except Exception as e:
                    print(f"  Error processing job {job.id}: {str(e)}")
                    continue
            
            # Commit batch
            await session.commit()
            print(f"  Committed batch {i // batch_size + 1}")
        
        print(f"\nCompleted! Processed {processed} jobs.")


if __name__ == "__main__":
    print("Starting embedding backfill...")
    asyncio.run(backfill_embeddings())
