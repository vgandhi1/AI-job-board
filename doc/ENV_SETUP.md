# Environment Variables Setup

## Single .env File (Root)

**We use a single `.env` file at the project root** that is shared by both backend and frontend.

### Location

Create `.env` at project root:

```bash
# ============================================
# AI Job Board - Environment Configuration
# ============================================
# This single .env file is used by both backend and frontend

# Database Configuration (Backend)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobboard

# OpenAI API Configuration (Backend)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override default models (Backend)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_ANALYSIS_MODEL=gpt-4o-mini

# App Configuration (Backend)
DEBUG=false
APP_NAME=AI Job Board API

# Frontend Configuration
# Backend API URL (used by Next.js frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Quick Setup

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

Or use the `setup.sh` script which will create the `.env` file automatically.

## How It Works

- **Backend**: Reads `.env` from project root (configured in `backend/app/config.py`)
- **Frontend**: Next.js automatically reads `.env` from project root for `NEXT_PUBLIC_*` variables
- **Docker**: Uses root `.env` file via docker-compose

## Benefits of Single .env File

✅ Single source of truth  
✅ Easier to manage  
✅ No duplication  
✅ Works with docker-compose  
✅ Standard practice for monorepos
