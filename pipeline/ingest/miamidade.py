import logging
import os
import sys
from datetime import datetime, timezone
from hashlib import sha256
from typing import List, Dict, Any

from sqlalchemy.exc import IntegrityError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.db import SessionLocal  # noqa: E402
from backend.app import models  # noqa: E402

DATE_START = datetime(2022, 9, 26, tzinfo=timezone.utc)
DATE_END = datetime(2022, 9, 30, 23, 59, 59, tzinfo=timezone.utc)
SOURCE_NAME = "Miami-Dade EM"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

UPDATES: List[Dict[str, Any]] = [
    {
        "id": "miamidade-2022-09-26-shelters",
        "source_url": "https://www.miamidade.gov/emergency/library/ian-update-1",
        "published_at": datetime(2022, 9, 26, 18, 15, tzinfo=timezone.utc),
        "text": (
            "Miami-Dade Emergency Management: No evacuation orders. Three shelters on standby; "
            "residents needing assistance can call 311. Sandbag distribution available until 7 PM."
        ),
    },
    {
        "id": "miamidade-2022-09-30-transit",
        "source_url": "https://www.miamidade.gov/emergency/library/ian-update-4",
        "published_at": datetime(2022, 9, 30, 9, 0, tzinfo=timezone.utc),
        "text": (
            "Miami-Dade Transit operating weekday schedule; Metromover resumes full service. "
            "Bridge openings for marine traffic remain suspended until conditions improve."
        ),
    },
]


def ingest() -> None:
    session = SessionLocal()
    inserted = 0
    skipped = 0

    logger.info("Processing %d Miami-Dade updates", len(UPDATES))
    for item in UPDATES:
        published_at = item["published_at"]
        if not (DATE_START <= published_at <= DATE_END):
            continue

        alert_id = item["id"]
        existing = (
            session.query(models.RawUpdate)
            .filter(models.RawUpdate.source == SOURCE_NAME, models.RawUpdate.source_item_id == alert_id)
            .one_or_none()
        )
        if existing:
            skipped += 1
            logger.info("Skip duplicate alert_id=%s", alert_id)
            continue

        raw_text = item["text"]
        raw_html = item.get("html")
        content_hash = sha256(raw_text.encode("utf-8")).hexdigest()

        record = models.RawUpdate(
            id=alert_id,
            source=SOURCE_NAME,
            source_url=item["source_url"],
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
