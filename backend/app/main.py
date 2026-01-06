from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.db import get_db


def create_app() -> FastAPI:
    app = FastAPI(title="Hurricane Impact Triage System API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    def parse_ts(ts: Optional[str]) -> Optional[datetime]:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp: {ts}") from exc

    @app.get("/cards")
    async def get_cards(
        mode: str = Query(..., pattern="^(action|info)$"),
        county: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        urgency: Optional[str] = Query(None),
        from_ts: Optional[str] = Query(None, alias="from"),
        to_ts: Optional[str] = Query(None, alias="to"),
        limit: int = Query(30, ge=1, le=30),
        offset: int = Query(0, ge=0),
        db: Session = Depends(get_db),
    ):
        q = db.query(models.Card).filter(models.Card.mode == mode)
        if county:
            q = q.filter(models.Card.county == county)
        if category:
            q = q.filter(models.Card.category == category)
        if urgency:
            q = q.filter(models.Card.urgency == urgency)

        start_dt = parse_ts(from_ts)
        end_dt = parse_ts(to_ts)
        if start_dt:
            q = q.filter(models.Card.published_at >= start_dt)
        if end_dt:
            q = q.filter(models.Card.published_at <= end_dt)

        if mode == "action":
            urgency_order = case(
                (models.Card.urgency == "high", 3),
                (models.Card.urgency == "medium", 2),
                else_=1,
            )
            q = q.order_by(urgency_order.desc(), models.Card.published_at.desc())
        else:
            q = q.order_by(models.Card.published_at.desc())

        records: List[models.Card] = q.offset(offset).limit(limit).all()
        return [
            {
                "id": c.id,
                "mode": c.mode,
                "category": c.category,
                "urgency": c.urgency,
                "action_type": c.action_type,
                "county": c.county,
                "city": c.city,
                "title": c.title,
                "summary": c.summary,
                "source": c.source,
                "source_url": c.source_url,
                "published_at": c.published_at,
                "duplicate_group_id": c.duplicate_group_id,
            }
            for c in records
        ]

    @app.get("/stats")
    async def stats(
        from_ts: Optional[str] = Query(None, alias="from"),
        to_ts: Optional[str] = Query(None, alias="to"),
        db: Session = Depends(get_db),
    ):
        start_dt = parse_ts(from_ts)
        end_dt = parse_ts(to_ts)

        base = db.query(models.Card)
        if start_dt:
            base = base.filter(models.Card.published_at >= start_dt)
        if end_dt:
            base = base.filter(models.Card.published_at <= end_dt)

        by_category = (
            base.with_entities(models.Card.category, func.count().label("count"))
            .group_by(models.Card.category)
            .all()
        )
        by_county = (
            base.with_entities(models.Card.county, func.count().label("count"))
            .group_by(models.Card.county)
            .all()
        )
        by_urgency = (
            base.with_entities(models.Card.urgency, func.count().label("count"))
            .group_by(models.Card.urgency)
            .all()
        )

        return {
            "category": {row.category: row.count for row in by_category},
            "county": {row.county: row.count for row in by_county},
            "urgency": {row.urgency: row.count for row in by_urgency},
        }

    @app.get("/summary")
    async def summary(
        from_ts: Optional[str] = Query(None, alias="from"),
        to_ts: Optional[str] = Query(None, alias="to"),
        db: Session = Depends(get_db),
    ):
        start_dt = parse_ts(from_ts)
        end_dt = parse_ts(to_ts)

        base = db.query(models.Card)
        if start_dt:
            base = base.filter(models.Card.published_at >= start_dt)
        if end_dt:
            base = base.filter(models.Card.published_at <= end_dt)

        urgency_order = case(
            (models.Card.urgency == "high", 3),
            (models.Card.urgency == "medium", 2),
            else_=1,
        )
        top_actions = (
            base.filter(models.Card.mode == "action")
            .order_by(urgency_order.desc(), models.Card.published_at.desc())
            .limit(5)
            .all()
        )

        cat_counts = (
            base.with_entities(models.Card.category, func.count().label("count"))
            .group_by(models.Card.category)
            .order_by(func.count().desc())
            .limit(3)
            .all()
        )

        action_count = base.filter(models.Card.mode == "action").count()
        info_count = base.filter(models.Card.mode == "info").count()

        summary_text = []
        if top_actions:
            summary_text.append(f"Top urgent actions: {', '.join([c.title for c in top_actions])}")
        if cat_counts:
            summary_text.append(
                "Leading categories: " + ", ".join([f"{row.category} ({row.count})" for row in cat_counts])
            )
        summary_text.append(f"Totals - action: {action_count}, info: {info_count}")

        return {
            "top_urgent_actions": [
                {
                    "id": c.id,
                    "title": c.title,
                    "urgency": c.urgency,
                    "published_at": c.published_at,
                    "county": c.county,
                    "category": c.category,
                }
                for c in top_actions
            ],
            "leading_categories": [{"category": row.category, "count": row.count} for row in cat_counts],
            "totals": {"action": action_count, "info": info_count},
            "summary_text": " | ".join(summary_text),
        }

    return app


app = create_app()
