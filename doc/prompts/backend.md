## TASK: IMPLEMENT SEMANTIC SEARCH ARCHITECTURE
I need to upgrade the existing FastAPI backend to support vector-based semantic retrieval.

1. **Database Schema Update**:
   - Generate an Alembic migration to enable the `pgvector` extension.
   - Add an `embedding` column (vector(1536)) to the `Job` table.
   - Create an HNSW index on the `embedding` column to optimize query performance.

2. **Embedding Service**:
   - Create a dedicated service `app/services/vector_service.py`.
   - Implement a function `generate_embedding(text: str)` using OpenAI's `text-embedding-3-small` model.
   - Provide a utility script to backfill embeddings for existing records by concatenating `title`, `description`, and `company` fields.

3. **Search Endpoint Implementation**:
   - specific endpoint: `POST /search/semantic`.
   - Input Schema: `{ query: str, limit: int = 10 }`.
   - Workflow:
     a. Generate vector for the user query.
     b. Perform a cosine similarity search against the database.
     c. Return a list of jobs including a `match_score` (0.0 to 1.0) indicating relevance.

Context: The `Job` model is already defined in `models.py`. Ensure the code follows SOLID principles.