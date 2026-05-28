"""
Script to add sample jobs for testing.
Run this after setting up the database.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import Job
from app.services.vector_service import generate_embedding, prepare_job_text


SAMPLE_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "Tech Innovations Inc.",
        "description": "We are looking for a Senior Python Developer with 5+ years of experience in backend development. Experience with FastAPI, PostgreSQL, and cloud platforms (AWS/GCP) is required. You will work on building scalable APIs and microservices. Knowledge of machine learning frameworks is a plus.",
        "location": "San Francisco, CA",
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "USD",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Solutions Corp",
        "description": "Join our ML team to build cutting-edge AI products. Requirements include: 3+ years of ML experience, proficiency in Python, TensorFlow/PyTorch, and experience with NLP models. You'll work on RAG systems, vector embeddings, and LLM integration.",
        "location": "Remote",
        "salary_min": 140000,
        "salary_max": 200000,
        "salary_currency": "USD",
    },
    {
        "title": "Full Stack Developer (React/Node.js)",
        "company": "WebDev Solutions",
        "description": "We need a Full Stack Developer proficient in React, Next.js, Node.js, and TypeScript. Experience with Tailwind CSS and modern UI frameworks required. You'll build responsive web applications and work with REST APIs.",
        "location": "New York, NY",
        "salary_min": 100000,
        "salary_max": 150000,
        "salary_currency": "USD",
    },
    {
        "title": "Data Engineer",
        "company": "DataFlow Systems",
        "description": "Looking for a Data Engineer to design and maintain data pipelines. Skills needed: Python, SQL, Apache Spark, Airflow, and experience with data warehouses. You'll work with large-scale data processing and ETL pipelines.",
        "location": "Seattle, WA",
        "salary_min": 110000,
        "salary_max": 160000,
        "salary_currency": "USD",
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudTech Services",
        "description": "DevOps Engineer needed for CI/CD pipeline management and infrastructure automation. Experience with Docker, Kubernetes, Terraform, and cloud platforms (AWS/Azure) required. You'll ensure high availability and scalability of our systems.",
        "location": "Austin, TX",
        "salary_min": 115000,
        "salary_max": 170000,
        "salary_currency": "USD",
    },
    {
        "title": "Backend Engineer (Python/FastAPI)",
        "company": "API Masters",
        "description": "Backend Engineer position focusing on API development with FastAPI and Python. Experience with async programming, PostgreSQL, and Redis is essential. You'll build high-performance APIs and integrate with third-party services.",
        "location": "Boston, MA",
        "salary_min": 105000,
        "salary_max": 155000,
        "salary_currency": "USD",
    },
    {
        "title": "AI/ML Research Scientist",
        "company": "Research Labs",
        "description": "Research Scientist position for advancing AI capabilities. PhD or Master's in Computer Science with focus on ML/NLP. Experience with transformer models, vector databases, and semantic search systems. You'll publish research and build innovative AI solutions.",
        "location": "Palo Alto, CA",
        "salary_min": 150000,
        "salary_max": 220000,
        "salary_currency": "USD",
    },
    {
        "title": "Software Engineer - Python",
        "company": "StartupXYZ",
        "description": "Early-stage startup looking for a Python Software Engineer. You'll work on various projects including web development, data processing, and automation. Fast learner and adaptable to changing requirements. Experience with Django or Flask preferred.",
        "location": "Remote",
        "salary_min": 90000,
        "salary_max": 130000,
        "salary_currency": "USD",
    },
]


async def add_sample_jobs():
    """Add sample jobs to the database"""
    async with AsyncSessionLocal() as session:
        # Check if jobs already exist
        from sqlalchemy import select
        result = await session.execute(select(Job))
        existing_jobs = result.scalars().all()
        
        if existing_jobs:
            print(f"Found {len(existing_jobs)} existing jobs. Skipping sample data insertion.")
            return
        
        print(f"Adding {len(SAMPLE_JOBS)} sample jobs...")
        
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i, job_data in enumerate(SAMPLE_JOBS):
            # Create job
            job = Job(
                **job_data,
                posted_at=base_date + timedelta(days=i * 3),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            # Generate embedding
            try:
                job_text = prepare_job_text(job.title, job.description, job.company)
                embedding = await generate_embedding(job_text)
                job.embedding = embedding
                print(f"  ✓ Added: {job.title} at {job.company}")
            except Exception as e:
                print(f"  ✗ Error generating embedding for {job.title}: {str(e)}")
                # Still add the job without embedding
                pass
            
            session.add(job)
        
        await session.commit()
        print(f"\n✓ Successfully added {len(SAMPLE_JOBS)} sample jobs!")


if __name__ == "__main__":
    print("Adding sample jobs to database...")
    asyncio.run(add_sample_jobs())
