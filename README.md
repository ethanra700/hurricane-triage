# Hurricane Impact Triage System
Hurricane Impact Triage System
Overview

The Hurricane Impact Triage System is a data engineering and analysis project that transforms public, official hurricane updates into structured, queryable operational information.

The system ingests raw hurricane-related updates from multiple government sources, preserves the original data as ground truth, extracts deterministic and explainable “Action” and “Information” cards, groups duplicate reports, and stores everything in a relational database optimized for SQL-based analysis.


This project uses a historical data, Hurricane Ian, to showcase as a demo

Demo Scope (Fixed & Reproducible)

Event: Hurricane Ian
Time Window: September 26–30, 2022
Geography: Broward County & Miami-Dade County (Florida)

Data Sources (Official Only)

National Weather Service (NWS) — alerts, advisories, flood warnings

Broward County Emergency Management — shelters, evacuations, local guidance

Miami-Dade County Emergency Management — shelters, transportation, utilities updates

Florida Division of Emergency Management (FL DEM) — statewide situational context

All sources are:

official

timestamped

operationally relevant

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


