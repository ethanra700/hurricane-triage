import logging
import os
import re
import sys
from hashlib import sha256
from typing import Optional

from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.db import SessionLocal  # noqa: E402
from backend.app import models  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_raw_text(raw_text: str, raw_html: Optional[str]) -> str:
    if raw_html:
        text = strip_html(raw_html)
    else:
        text = raw_text
    text = normalize_whitespace(text)
    return text


def ingest_clean() -> None:
    session = SessionLocal()
    processed = 0
    inserted = 0
    skipped = 0

    raw_without_clean = (
        session.query(models.RawUpdate)
        .outerjoin(models.CleanUpdate, models.CleanUpdate.raw_update_id == models.RawUpdate.id)
        .filter(models.CleanUpdate.id.is_(None))
        .all()
    )

    logger.info("Found %d raw updates without clean records", len(raw_without_clean))

    for raw in raw_without_clean:
        processed += 1
        cleaned_text = clean_raw_text(raw.raw_text, raw.raw_html)
        cleaned_hash = sha256(cleaned_text.encode("utf-8")).hexdigest()

        clean_record = models.CleanUpdate(
            id=raw.id,
            raw_update_id=raw.id,
            cleaned_text=cleaned_text,
            cleaned_hash=cleaned_hash,
        )
        session.add(clean_record)
        try:
            session.commit()
            inserted += 1
            logger.info("Inserted clean_update for raw_update_id=%s", raw.id)
        except IntegrityError:
            session.rollback()
            skipped += 1
            logger.info("Skip duplicate clean_update for raw_update_id=%s", raw.id)
        except Exception as exc:  # pragma: no cover
            session.rollback()
            logger.error("Failed to insert clean_update for raw_update_id=%s: %s", raw.id, exc)

    logger.info("Done. Processed=%d inserted=%d skipped=%d", processed, inserted, skipped)
    session.close()


if __name__ == "__main__":
    ingest_clean()
