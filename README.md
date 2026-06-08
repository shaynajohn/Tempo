# Tempo

AI-powered running coach that ingests Garmin data, explains your runs, surfaces patterns, and warns before burnout.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, Recharts, Tailwind |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL + pgvector |
| AI | LangGraph agents, OpenAI embeddings |
| Analytics | pandas, numpy, scipy, scikit-learn |

## MVP Features

1. **Garmin ingestion** — manual JSON/CSV export (FIT planned)
2. **AI run explanations** — pace, cadence, HR drift analysis with natural-language insights
3. **Semantic workout search** — pgvector RAG over workout summaries
4. **Recovery & burnout detection** — resting HR, sleep, volume spikes, pace trends
5. **Training pattern discovery** — mileage sweet spots, recovery windows, conditions

## Quick Start

### 1. Database

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # add OPENAI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

App: http://localhost:3000

### 4. Import data

**Full Garmin export** (activities + sleep + stress) — on **Import**, click *Import full export*, or:

```bash
curl -X POST http://localhost:8001/api/v1/ingest/garmin-export \
  -H "Content-Type: application/json" \
  -d '{"export_path": "/path/to/DI_CONNECT"}'
```

Or run: `python backend/scripts/import_garmin_export.py /path/to/DI_CONNECT`

Single file upload also works for JSON/CSV.

## Project Layout

```
backend/app/
  api/          # REST routes
  ingestion/    # Garmin parsers
  analytics/    # fatigue, patterns, metrics
  ai/           # LangGraph agents, embeddings, explanations
  models/       # SQLAlchemy models
frontend/src/
  app/          # Next.js pages
  components/   # Dashboard, charts
sample-data/    # Example Garmin exports
```

## Garmin Export (manual)

1. Garmin Connect → Settings → Account → Export Data
2. Or export individual activities as JSON/CSV from third-party tools
3. Upload via the Import page or `POST /api/v1/ingest/upload`

Supported formats: `.json`, `.csv` (activities). FIT support is stubbed for a later pass.

## Environment

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Async PostgreSQL URL |
| `OPENAI_API_KEY` | Required for explanations & semantic search |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend |
| `GARMIN_EMAIL` | Garmin Connect email for local sync |
| `GARMIN_PASSWORD` | Garmin Connect password for local sync |
| `GARMIN_AUTO_SYNC` | Enables background Garmin sync while the backend is running |
| `GARMIN_SYNC_INTERVAL_MINUTES` | Background Garmin sync interval, defaults to `60` |
| `GARMIN_SYNC_LIMIT` | Recent Garmin activities to fetch per sync, defaults to `50` |

## Garmin Connect Sync

Tempo can pull recent running activities from Garmin Connect without repeatedly
uploading exports. This uses an unofficial Garmin Connect client, so keep it for
local/personal MVP use and keep manual export as a fallback.

Add these to `backend/.env`:

```bash
GARMIN_EMAIL=you@example.com
GARMIN_PASSWORD=your-garmin-password
GARMIN_AUTO_SYNC=true
GARMIN_SYNC_INTERVAL_MINUTES=60
GARMIN_SYNC_LIMIT=50
```

Then restart the backend and open **Import → Sync Garmin**. Tempo will also sync
in the background while the backend is running. Manual Garmin export is still
useful for sleep, stress, Body Battery, and other wellness signals.

Strava sync code is still present as an optional later path, but Strava may
require a subscription to create API apps.

## Roadmap

- [ ] FIT file parser (`fitparse`)
- [ ] Garmin Health API OAuth
- [ ] Athlete Memory Graph (cross-signal relationships)
- [ ] Race time projections
