import logging
import os
import sys
from hashlib import sha256
from typing import List

from sqlalchemy.exc import IntegrityError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.db import SessionLocal  # noqa: E402
from backend.app import models  # noqa: E402
from pipeline.extract import rules  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def summarize(text: str) -> str:
    # Simple summary: first sentence or trimmed chunk.
    for sep in [". ", "! ", "? "]:
        if sep in text:
            return text.split(sep)[0].strip() + sep.strip()
    return text[:240].strip()


def title_from_text(text: str) -> str:
    words = text.split()
    return " ".join(words[:10]) if words else "Update"


def create_card_from_clean(clean: models.CleanUpdate) -> models.Card:
    source = clean.raw_update.source if clean.raw_update else "unknown"
    source_url = clean.raw_update.source_url if clean.raw_update else ""
    published_at = clean.raw_update.published_at if clean.raw_update else None

    mode = rules.detect_mode(clean.cleaned_text)
    category = rules.detect_category(clean.cleaned_text) or "utilities"
    urgency = rules.detect_urgency(clean.cleaned_text)
    action_type = rules.detect_action_type(clean.cleaned_text) if mode == "action" else None
    county, city = rules.infer_location(clean.cleaned_text, source)

    title = title_from_text(clean.cleaned_text)
    summary = summarize(clean.cleaned_text)

    card_id_seed = f"{clean.id}-{category}-{mode}"
    card_id = sha256(card_id_seed.encode("utf-8")).hexdigest()

    return models.Card(
        id=card_id,
        clean_update_id=clean.id,
        mode=mode,
        category=category,
        action_type=action_type,
        urgency=urgency,
        county=county,
        city=city,
        title=title,
        summary=summary,
        source=source,
        source_url=source_url,
        published_at=published_at,
    )


def extract() -> None:
    session = SessionLocal()
    inserted = 0
    pending: List[models.CleanUpdate] = (
        session.query(models.CleanUpdate)
        .outerjoin(models.Card, models.Card.clean_update_id == models.CleanUpdate.id)
        .filter(models.Card.id.is_(None))
        .all()
    )

    logger.info("Found %d clean updates without cards", len(pending))

    for clean in pending:
        card = create_card_from_clean(clean)
        session.add(card)
        try:
            session.commit()
            inserted += 1
            logger.info("Inserted card for clean_update_id=%s", clean.id)
        except IntegrityError:
            session.rollback()
            logger.info("Skip duplicate card for clean_update_id=%s", clean.id)
        except Exception as exc:  # pragma: no cover
            session.rollback()
            logger.error("Failed to insert card for clean_update_id=%s: %s", clean.id, exc)

    logger.info("Done. Inserted=%d", inserted)
    session.close()


if __name__ == "__main__":
    extract()
