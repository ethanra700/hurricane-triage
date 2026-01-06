# Hurricane Impact Triage System

The Hurricane Impact Triage System is a reproducible data pipeline and relational database that transforms historical Hurricane Ian updates (Sep 26�30, 2022) for Broward and Miami-Dade counties into structured, queryable operational information for first responders.

## How to run demo (full stack)
1) Start Postgres
```
docker compose up -d postgres
```

2) Install backend deps
```
pip install -r backend/requirements.txt
```

3) Apply database migration
```
alembic -c backend/alembic.ini upgrade head
```

4) Run pipeline (ingest + clean + extract + dedup)
```
python -m pipeline.run_all
```

5) Start API (default port 8000; change if busy)
```
uvicorn backend.app.main:app --reload --port 8000
```

6) Start frontend (default port 3000)
```
cd frontend
npm install
set NEXT_PUBLIC_API_BASE=http://localhost:8000   # or export on bash
npm run dev -- --port 3000
```

7) Open
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

If a port is in use, pick another and adjust `NEXT_PUBLIC_API_BASE` accordingly.

## API endpoints
- `/health`
- `/cards` (filters: mode, county, category, urgency, from/to, limit/offset; action mode sorted by urgency/published_at)
- `/stats` (counts by category/county/urgency; optional from/to)
- `/summary` (top urgent actions, leading categories, totals; optional from/to)


