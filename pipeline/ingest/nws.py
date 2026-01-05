import os
import sys
import logging
from datetime import datetime, timezone
from hashlib import sha256
from typing import List, Dict, Any

import requests
from sqlalchemy.exc import IntegrityError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.db import SessionLocal  # noqa: E402
from backend.app import models  # noqa: E402

NWS_ALERTS_URL = "https://api.weather.gov/alerts"
DATE_START = datetime(2022, 9, 26, tzinfo=timezone.utc)
DATE_END = datetime(2022, 9, 30, 23, 59, 59, tzinfo=timezone.utc)
SOURCE_NAME = "NWS"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def fetch_alerts() -> List[Dict[str, Any]]:
    params = {
        "start": DATE_START.isoformat(),
        "end": DATE_END.isoformat(),
        "status": "actual",
        "limit": 200,
    }
    headers = {"User-Agent": "hurricane-triage/0.1 (contact: none)"}
    resp = requests.get(NWS_ALERTS_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("features", [])


def within_scope(feature: Dict[str, Any]) -> bool:
    props = feature.get("properties", {})
    sent = props.get("sent")
    if not sent:
        return False
    try:
        sent_dt = datetime.fromisoformat(sent.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return False
    if not (DATE_START <= sent_dt <= DATE_END):
        return False

    area = (props.get("areaDesc") or "").lower()
    return "broward" in area or "miami-dade" in area or "miami dade" in area


def build_raw_text(props: Dict[str, Any]) -> str:
    parts = []
    for key in ("headline", "description", "instruction"):
        val = props.get(key)
        if val:
            parts.append(val.strip())
    return "\n\n".join(parts) if parts else ""


def ingest() -> None:
    session = SessionLocal()
    inserted = 0
    skipped = 0

    features = fetch_alerts()
    logger.info("Fetched %d alerts from NWS API", len(features))

    for feature in features:
        if not within_scope(feature):
            continue

        props = feature.get("properties", {})
        alert_id = props.get("id") or feature.get("id")
        if not alert_id:
            continue

        source_url = props.get("id") or ""
        published_at_raw = props.get("sent") or props.get("onset")
        if not published_at_raw:
            continue
        try:
            published_at = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue

        raw_text = build_raw_text(props)
        raw_html = None
        content_hash = sha256(raw_text.encode("utf-8")).hexdigest()

        exists = (
            session.query(models.RawUpdate)
            .filter(
                models.RawUpdate.source == SOURCE_NAME,
                models.RawUpdate.source_item_id == alert_id,
            )
            .one_or_none()
        )
        if exists:
            skipped += 1
            logger.info("Skip duplicate alert_id=%s", alert_id)
            continue

        record = models.RawUpdate(
            id=alert_id,
            source=SOURCE_NAME,
            source_url=source_url,
            source_item_id=alert_id,
            published_at=published_at,
            raw_text=raw_text,
            raw_html=raw_html,
            content_hash=content_hash,
        )
        session.add(record)
        try:
            session.commit()
            inserted += 1
            logger.info("Inserted alert_id=%s", alert_id)
        except IntegrityError:
            session.rollback()
            skipped += 1
            logger.info("Skip duplicate on commit alert_id=%s", alert_id)
        except Exception as exc:  # pragma: no cover
            session.rollback()
            logger.error("Failed to insert alert_id=%s: %s", alert_id, exc)

    logger.info("Done. Inserted=%d skipped=%d", inserted, skipped)
    session.close()


if __name__ == "__main__":
    ingest()
