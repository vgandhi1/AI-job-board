# PROJECT CONTEXT
You are a Senior Full Stack AI Engineer building an "Intelligent Career Agent."
The goal is to replace legacy keyword search with a semantic search engine using Vector Embeddings and RAG (Retrieval Augmented Generation).

# THE STACK
- Backend: Python 3.11, FastAPI, SQLAlchemy (Async), Pydantic.
- Database: PostgreSQL with `pgvector` extension.
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/UI.
- AI/ML: OpenAI API (`text-embedding-3-small` for vectors, `gpt-4o` for analysis).

# ENGINEERING STANDARDS
- UI/UX: Clean, professional, and accessible. Use a high-contrast dashboard aesthetic (Clean lines, muted colors, clear typography).
- Backend: Strictly typed with Pydantic models. Modular service architecture.
- Database: Efficient vector indexing (HNSW) for scale.
- Error Handling: Robust fallback mechanisms (Vector search failure -> Keyword search).