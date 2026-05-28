# AI Job Board

An AI-powered job board that combines two subsystems in a single FastAPI app:

1. **Search / AI** - semantic search over pgvector embeddings, plus on-demand
   job-fit analysis (pros / cons / summary). Pluggable LLM backend: use the
   hosted OpenAI APIs **or** a local Ollama server.
2. **Ingestion** - a Playwright-based scraper that pulls postings from
   LinkedIn, Indeed, and Wellfound into the same unified `jobs` table.

The frontend is a Next.js 14 app (Tailwind + Shadcn-style components).

---

## Tech stack

**Backend**
- Python 3.11, FastAPI
- SQLAlchemy 2.x (async) + asyncpg
- PostgreSQL with the `pgvector` extension
- Alembic for migrations
- LLM (configurable): OpenAI (`text-embedding-3-small`, `gpt-4o-mini`) **or**
  Ollama (`nomic-embed-text`, `llama3.1`, etc.) via Ollama's OpenAI-compatible API
- Playwright (Chromium) for scraping

**Frontend**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS, Shadcn-style UI primitives
- `lucide-react` icons

---

## Project layout

```
AI-job-board/
├── README.md                       # this file
├── docker-compose.yml              # postgres (pgvector) + backend + frontend
├── docker-compose.prod.yml         # prod variant (adds nginx)
├── .env / .env.example             # single shared env file
├── setup.sh                        # one-shot local dev bootstrap
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml              # uv-friendly project metadata
│   ├── requirements.txt
│   ├── run.py                      # local dev entrypoint
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 000_initial_jobs_table.py
│   │       ├── 001_add_pgvector_and_embeddings.py
│   │       └── 002_add_scraping_fields.py
    │   ├── scripts/
    │   │   ├── add_sample_jobs.py
    │   │   ├── backfill_embeddings.py
    │   │   ├── reset_embedding_dimension.py   # resize pgvector col on provider switch
    │   │   ├── db-start.sh             # docker compose up -d postgres
    │   │   ├── db-connect.sh           # psql shell
    │   │   ├── db-query.sh             # one-shot SQL
    │   │   └── install-playwright-deps.sh
│   └── app/
│       ├── main.py                 # FastAPI app, wires all routers
│       ├── config.py               # pydantic-settings, reads root .env
│       ├── database.py             # async engine + session factory
│       ├── models.py               # unified Job model (AI + scraping fields)
│       ├── schemas.py              # all Pydantic schemas
│       ├── routers/
│       │   ├── search.py           # POST /search/semantic, POST /search/analyze-fit
│       │   ├── jobs.py             # GET /jobs, /jobs/{id}, /jobs/city, /jobs/company, DELETE
│       │   ├── scrape.py           # POST /scrape, POST /scrape/async
│       │   └── stats.py            # GET /stats
│       └── services/
│           ├── llm_client.py            # provider-aware OpenAI/Ollama client
│           ├── vector_service.py        # embedding generation (provider-agnostic)
│           ├── fit_analysis_service.py  # job-fit analysis (provider-agnostic)
│           ├── scraper_service.py       # Playwright scrapers (LI/Indeed/Wellfound)
│           └── ingestion_service.py     # dedupe + save + embed
│
├── frontend/
│   ├── Dockerfile / Dockerfile.prod
│   ├── package.json, tsconfig.json, tailwind.config.ts, next.config.js
│   ├── app/                        # Next.js app router
│   ├── components/
│   │   ├── JobInsightCard.tsx
│   │   └── ui/                     # card, button, badge primitives
│   └── lib/                        # api client + utils
│
├── nginx/
│   └── nginx.conf                  # prod reverse proxy
│
└── doc/                            # all long-form docs live here
    ├── DEPLOYMENT.md
    ├── ENV_SETUP.md
    ├── DATABASE_SETUP.md
    ├── INTEGRATION_GUIDE.md
    └── prompts/                    # original product prompts
        ├── RAG-workflow.md
        ├── backend.md
        ├── frontend.md
        └── Fit-analysis.md
```

---

## Quick start

### 1. Docker Compose (recommended)

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY at minimum

docker compose up -d
docker compose exec backend alembic upgrade head

# (optional) seed sample data
docker compose exec backend python scripts/add_sample_jobs.py
```

Then visit:
- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API docs (Swagger): <http://localhost:8000/docs>

### 2. Manual local dev

```bash
./setup.sh        # installs backend + frontend deps + playwright
# edit .env

# Terminal 1 - database
docker compose up -d postgres

# Terminal 2 - backend
cd backend
alembic upgrade head
uv run uvicorn app.main:app --reload     # or: python run.py

# Terminal 3 - frontend
cd frontend
npm run dev
```

See [`doc/DATABASE_SETUP.md`](doc/DATABASE_SETUP.md) and
[`doc/ENV_SETUP.md`](doc/ENV_SETUP.md) for more options.

### 3. Production (Nginx reverse proxy)

For production, use the prod compose file which adds an Nginx service in
front of `frontend` and `backend` (single origin, no CORS, suitable for SSL
termination):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

See [`doc/DEPLOYMENT.md`](doc/DEPLOYMENT.md) for the full prod walkthrough
(SSL, secrets management, scaling notes).

---

## API surface

### Search / AI

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/search/semantic` | Vector search over `jobs.embedding`; falls back to keyword search on failure. |
| `POST` | `/search/analyze-fit` | GPT-4o-mini pros/cons/summary analysis for a given query + job_id. |

### Jobs CRUD

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/jobs` | Paginated list with `source` / `city` / `company` filters. |
| `GET` | `/jobs/{id}` | One job by id. |
| `GET` | `/jobs/city/{city}` | Filtered by city. |
| `GET` | `/jobs/company/{company}` | Filtered by company. |
| `DELETE` | `/jobs/{id}` | Delete (currently unauthenticated - see security note below). |

### Scraping / ingestion

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/scrape` | Synchronously scrape `source` (linkedin / indeed / wellfound), upsert by URL, optionally embed. |
| `POST` | `/scrape/async` | Same workflow, run as a background task. |

### Stats / meta

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/stats` | Totals, breakdown by source, top cities. |
| `GET` | `/health` | Healthcheck. |
| `GET` | `/api/v1/status` | Service identity + version. |
| `GET` | `/` | Endpoint index. |

### Example: scrape + ingest

```bash
curl -X POST http://localhost:8000/scrape \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "linkedin",
    "query": "python developer",
    "location": "San Francisco",
    "max_results": 10,
    "generate_embeddings": true
  }'
```

### Example: semantic search

```bash
curl -X POST http://localhost:8000/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query": "Senior Python developer with ML experience", "limit": 10}'
```

---

## AI provider (OpenAI vs Ollama)

The LLM backend is selected by the `LLM_PROVIDER` env var. Default is
`openai` so existing setups keep working. Switching to local Ollama lets
you run embeddings + fit analysis with no API spend and no data leaving
your machine.

### Config matrix

| Variable | `LLM_PROVIDER=openai` (default) | `LLM_PROVIDER=ollama` |
|---|---|---|
| `OPENAI_API_KEY` | **required** | unused |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` (1536d) | unused |
| `OPENAI_ANALYSIS_MODEL` | `gpt-4o-mini` | unused |
| `OLLAMA_BASE_URL` | unused | URL of the Ollama server (default `http://host.docker.internal:11434`) |
| `OLLAMA_EMBEDDING_MODEL` | unused | e.g. `nomic-embed-text` (768d), `mxbai-embed-large` (1024d) |
| `OLLAMA_ANALYSIS_MODEL` | unused | e.g. `llama3.1`, `qwen2.5`, `mistral` |
| `EMBEDDING_DIMENSION` | `1536` | **must match the chosen Ollama embedding model** |

Under the hood, both providers use the same `openai` Python SDK. For Ollama,
we just point `base_url` at Ollama's OpenAI-compatible `/v1` endpoint — no
extra dependencies.

### Setting up Ollama on Windows for use from WSL

Ollama runs on the Windows host; the backend runs in WSL2 (directly or in
Docker). The two need a network bridge.

**On Windows (one-time):**

1. Install Ollama for Windows: <https://ollama.com/download>
2. Make it listen on all interfaces, not just `127.0.0.1`. Open
   *Settings → System → About → Advanced system settings → Environment
   Variables* and add a **User** variable:

   ```
   OLLAMA_HOST = 0.0.0.0:11434
   ```

   Then restart the Ollama tray app (right-click → Quit, relaunch).

3. Pull the models you want:

   ```powershell
   ollama pull nomic-embed-text
   ollama pull llama3.1
   ```

4. Verify it answers from outside `localhost`:

   ```powershell
   curl http://localhost:11434/api/tags
   ```

**Windows Firewall:** if you're prompted, allow `ollama.exe` on Private
networks. If WSL still can't connect, add an inbound rule for TCP 11434
scoped to Private profile.

**On the WSL/AI-job-board side:**

Pick the right `OLLAMA_BASE_URL` based on how you run the backend:

- **`docker compose up`** (default) — keep the default:
  ```
  OLLAMA_BASE_URL=http://host.docker.internal:11434
  ```
  The compose file already declares `extra_hosts: host.docker.internal:host-gateway`
  so the container can route to the Windows host.

- **Backend running directly in WSL** (no Docker) — point at the Windows
  host's IP from WSL. On WSL2 the Windows host is the default gateway:

  ```bash
  WIN_IP=$(ip route show default | awk '{print $3}')
  echo "OLLAMA_BASE_URL=http://${WIN_IP}:11434"
  ```

  Paste that into `.env`. (Windows 11 24H2+ also supports WSL2 mirrored
  networking, where `localhost` crosses the boundary; if you enabled that,
  `http://localhost:11434` works too.)

### Switching from OpenAI to Ollama

Embedding dimensions differ between models, so the `pgvector` column has to
be resized. Procedure:

```bash
# 1. Edit .env
#    LLM_PROVIDER=ollama
#    OLLAMA_EMBEDDING_MODEL=nomic-embed-text
#    EMBEDDING_DIMENSION=768          # must match the model

# 2. Resize the embedding column (drops existing embeddings).
cd backend
uv run python scripts/reset_embedding_dimension.py

# 3. Re-embed all jobs using Ollama.
uv run python scripts/backfill_embeddings.py
```

Going back to OpenAI is the same flow with `EMBEDDING_DIMENSION=1536`.

### Quick health check

```bash
curl -X POST http://localhost:8000/search/semantic \
  -H 'Content-Type: application/json' \
  -d '{"query":"python developer", "limit": 3}'
```

If you see a 500 with "OPENAI_API_KEY is not set" or
"OLLAMA_BASE_URL is not set", the wrong provider is selected for your env.

---

## Data model

A single `jobs` table now carries both the AI/search fields and the
ingestion/provenance fields. See `backend/app/models.py` for the source of
truth.

| Column | Type | Source |
|---|---|---|
| `id` | `int` PK | both |
| `title`, `company` | `varchar` | both |
| `description` | `text`, nullable | AI (nullable so scrapers can ingest first) |
| `location`, `city` | `varchar` | location: AI / city: scraper |
| `salary_min/max/currency` | `int / int / varchar` | AI |
| `url` (unique) | `varchar` | scraper |
| `source` | `varchar` | scraper (linkedin / indeed / wellfound / manual / sample) |
| `scraped_at` | `timestamptz` | scraper |
| `posted_at`, `created_at`, `updated_at` | `timestamp` | both |
| `embedding` | `vector(1536)`, nullable | AI |

`embedding` is indexed with HNSW (cosine ops). `url` is a unique index used as
the dedupe key by the ingestion service.

---

## Migrations

```bash
cd backend
alembic upgrade head            # apply all
alembic revision -m "..."       # create a new revision
alembic downgrade -1            # roll back one step
```

Three migrations ship with the project:

1. `000_initial_jobs_table.py` - base schema
2. `001_add_pgvector_and_embeddings.py` - enables `pgvector`, adds `embedding`,
   creates HNSW index
3. `002_add_scraping_fields.py` - adds `city`, `url` (unique), `source`,
   `scraped_at`, and relaxes `description` to NULLABLE

> **Changing embedding dimension** (e.g. switching to an Ollama embedding
> model) is a separate operation - not an Alembic migration, because the
> target dimension depends on a runtime env var. Use
> `backend/scripts/reset_embedding_dimension.py` instead. See the
> [AI provider section](#ai-provider-openai-vs-ollama) for the full
> procedure.

---

## Security notes

- `DELETE /jobs/{id}` and `POST /scrape*` are currently unauthenticated. Wire
  FastAPI dependency-injected auth (session or token) before exposing these
  to untrusted callers, per the workspace authentication rules.
- Production deployments should put the app behind Nginx (see
  [`doc/DEPLOYMENT.md`](doc/DEPLOYMENT.md)) so CORS can be disabled and
  same-origin auth cookies (`Secure`, `HttpOnly`, `SameSite`) can be used.
- The scraper subsystem opens an outbound HTTP context (Playwright) only to
  the hardcoded LinkedIn / Indeed / Wellfound origins selected by `source`.
  Source strings are validated against an allow-list in `get_scraper()`.
- `db-query.sh` runs whatever SQL the caller passes via `-c`. Treat it as a
  developer tool; never feed it untrusted input.

---

## Further reading

- [`doc/DEPLOYMENT.md`](doc/DEPLOYMENT.md) - Nginx reverse proxy + prod compose
- [`doc/DATABASE_SETUP.md`](doc/DATABASE_SETUP.md) - PostgreSQL setup variants
- [`doc/ENV_SETUP.md`](doc/ENV_SETUP.md) - environment variable layout
- [`doc/INTEGRATION_GUIDE.md`](doc/INTEGRATION_GUIDE.md) - on-demand vs precomputed fit analysis

## License

MIT
