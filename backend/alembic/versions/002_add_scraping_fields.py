"""Add scraping/ingestion fields to jobs table.

Adds `city`, `url`, `source`, and `scraped_at` columns so the unified jobs
table can also store rows from the LinkedIn/Indeed/Wellfound scrapers. Also
relaxes `description` to NULLABLE because scraped postings may not include a
body at ingestion time.

Revision ID: 002_add_scraping_fields
Revises: 001_add_pgvector
Create Date: 2024-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "002_add_scraping_fields"
down_revision = "001_add_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow description to be NULL (scraped jobs may not have one initially).
    op.alter_column("jobs", "description", existing_type=sa.Text(), nullable=True)

    # Add new ingestion/provenance columns.
    op.add_column("jobs", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("jobs", sa.Column("url", sa.String(length=500), nullable=True))
    op.add_column("jobs", sa.Column("source", sa.String(length=100), nullable=True))
    op.add_column(
        "jobs",
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )

    op.create_index(op.f("ix_jobs_city"), "jobs", ["city"], unique=False)
    op.create_index(op.f("ix_jobs_source"), "jobs", ["source"], unique=False)
    op.create_index(op.f("ix_jobs_url"), "jobs", ["url"], unique=True)
    op.create_index(
        "idx_title_company_city", "jobs", ["title", "company", "city"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_title_company_city", table_name="jobs")
    op.drop_index(op.f("ix_jobs_url"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_source"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_city"), table_name="jobs")

    op.drop_column("jobs", "scraped_at")
    op.drop_column("jobs", "source")
    op.drop_column("jobs", "url")
    op.drop_column("jobs", "city")

    op.alter_column("jobs", "description", existing_type=sa.Text(), nullable=False)
