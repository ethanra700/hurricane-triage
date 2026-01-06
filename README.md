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
- Run all ingestion + cleaning + extraction: `python -m pipeline.run_all`
- (Dependencies/env setup to be added in later slices.)

## Slice checklist
- [x] Slice 0: Scaffold + plumbing
- [ ] Slice 1: Database schema + Alembic migration
- [ ] Slice 2: Ingestion stubs + raw storage
- [ ] Slice 3: Cleaning + deterministic extraction framework
- [ ] Slice 4: Deduplication grouping
- [ ] Slice 5: API endpoints (/cards, /stats, /summary)
- [ ] Slice 6: Pipeline run orchestration
- [ ] Slice 7: Thin frontend tabs (Action vs Information)
- [ ] Slice G: Final polish and documentation
