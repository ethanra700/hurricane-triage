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
SOURCE_NAME = "Broward County EM"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Static, historical advisories within scope.
UPDATES: List[Dict[str, Any]] = [
    {
        "id": "broward-2022-09-27-shelters",
        "source_url": "https://www.broward.org/Hurricane/Pages/Updates.aspx#2022-09-27-shelters",
        "published_at": datetime(2022, 9, 27, 10, 30, tzinfo=timezone.utc),
        "text": (
            "Broward County Emergency Management: Two general population shelters will open at 2 PM today. "
            "Locations: Plantation Elementary and Lyons Creek Middle. Residents in low-lying areas urged to relocate."
        ),
    },
    {
        "id": "broward-2022-09-29-transport",
        "source_url": "https://www.broward.org/Hurricane/Pages/Updates.aspx#2022-09-29-transport",
        "published_at": datetime(2022, 9, 29, 14, 0, tzinfo=timezone.utc),
        "text": (
            "Broward County Transit will suspend fixed-route service at 6 PM due to tropical storm conditions. "
            "Paratransit trips for medical needs will continue until weather deteriorates."
        ),
    },
]


def ingest() -> None:
    session = SessionLocal()
    inserted = 0
    skipped = 0

    logger.info("Processing %d Broward updates", len(UPDATES))
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
