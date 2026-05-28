"""Add pgvector extension and embedding column

Revision ID: 001_add_pgvector
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_add_pgvector'
down_revision = '000_initial_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding column to jobs table
    op.add_column('jobs', sa.Column('embedding', Vector(1536), nullable=True))
    
    # Create HNSW index for efficient similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS jobs_embedding_idx 
        ON jobs 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    # Drop index
    op.execute('DROP INDEX IF EXISTS jobs_embedding_idx')
    
    # Drop column
    op.drop_column('jobs', 'embedding')
    
    # Note: We don't drop the extension as it might be used by other tables
