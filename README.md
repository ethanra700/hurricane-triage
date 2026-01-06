# Hurricane Impact Triage System

The Hurricane Impact Triage System is a reproducible data pipeline and relational database that transforms historical Hurricane Ian updates (Sep 26–30, 2022) for Broward and Miami-Dade counties into structured, queryable operational information for first responders.

## How to run demo
- Start Postgres: `docker compose up -d postgres`
- Install backend deps: `pip install -r backend/requirements.txt`
- Run migrations: `alembic -c backend/alembic.ini upgrade head`
- Run NWS ingestion: `python -m pipeline.ingest.nws`
- Run Broward ingestion: `python -m pipeline.ingest.broward`
- Run Miami-Dade ingestion: `python -m pipeline.ingest.miamidade`
- Run FL DEM ingestion: `python -m pipeline.ingest.fldem`
- Run cleaning: `python -m pipeline.clean.clean_text`
- Run extraction: `python -m pipeline.extract.extract_cards`
- Run deduplication: `python -m pipeline.dedup.dedup`
- Run all ingestion + cleaning + extraction + dedup: `python -m pipeline.run_all`
- Start API: `uvicorn backend.app.main:app --reload --port 8000`

Frontend (Next.js):
- `cd frontend`
- `npm install`
- (optional) set `NEXT_PUBLIC_API_BASE` (default http://localhost:8000)
- `npm run dev` (open http://localhost:3000)

API endpoints:
- `/health`
- `/cards` (filters: mode, county, category, urgency, from/to, limit/offset)
- `/stats` (counts by category/county/urgency; optional from/to)
- `/summary` (top urgent actions, leading categories, totals; optional from/to)

## Slice checklist
- [x] Slice 0: Scaffold + plumbing
- [x] Slice 1: Database schema + Alembic migration
- [x] Slice 2: Ingestion stubs + raw storage
- [x] Slice 3: Cleaning + deterministic extraction framework
- [x] Slice 4: Deduplication grouping
- [x] Slice 5: API endpoints (/cards, /stats, /summary)
- [x] Slice 7: Thin frontend tabs (Action vs Information)
- [ ] Slice 6: Pipeline run orchestration
- [ ] Slice G: Final polish and documentation
