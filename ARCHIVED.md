# Archived repository

**Status:** Archived on 2026-06-28  
**Reason:** Superseded by [SmartFound](https://github.com/vgandhi1/SmartFound)

## Successor

All ongoing development continues in **SmartFound** — Industry 4.0 job board with Supabase auth, ATS scrapers (Greenhouse/Lever/Workday), and scheduled CI.

Critical capabilities from this prototype are **preserved inside SmartFound** at:

- `legacy/ai-job-board/` — reference source (semantic search, fit analysis, LLM providers, board scrapers)
- `docs/semantic-search-from-legacy.md` — porting runbook

## What moved where

| AI Job Board capability | SmartFound location |
|-------------------------|---------------------|
| Semantic search (pgvector) | Planned — see porting runbook |
| Job fit analysis | Planned — `legacy/ai-job-board/backend/app/services/fit_analysis_service.py` |
| Ollama / OpenAI switch | Planned — `legacy/ai-job-board/backend/app/services/llm_client.py` |
| LinkedIn / Indeed / Wellfound scrapers | Reference in `legacy/ai-job-board/backend/app/services/scraper_service.py` |
| Auth, companies, ATS pipeline, production deploy | **Already in SmartFound** (this repo's successor) |

## Local clone

If you have a local checkout, prefer cloning SmartFound instead:

```bash
git clone https://github.com/vgandhi1/SmartFound.git
```

This repository is read-only on GitHub.
