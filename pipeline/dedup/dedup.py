import logging
import os
import sys
from collections import defaultdict
from datetime import timedelta
from hashlib import sha256
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.db import SessionLocal  # noqa: E402
from backend.app import models  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

WINDOW = timedelta(hours=6)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def signature(card: models.Card) -> str:
    parts = [normalize(card.title or ""), card.category or "", card.county or ""]
    if card.action_type:
        parts.append(card.action_type)
    return "|".join(parts)


def deduplicate() -> None:
    session = SessionLocal()
    inserted_groups = 0
    grouped_cards = 0

    cards: List[models.Card] = (
        session.query(models.Card)
        .filter(models.Card.duplicate_group_id.is_(None))
        .order_by(models.Card.published_at.asc())
        .all()
    )

    sig_map: Dict[str, List[models.Card]] = defaultdict(list)
    for card in cards:
        sig = signature(card)
        sig_map[sig].append(card)

    for sig, card_list in sig_map.items():
        if len(card_list) == 1:
            group_id = sha256(f"{sig}|{card_list[0].id}".encode("utf-8")).hexdigest()
            group = models.DuplicateGroup(id=group_id, signature=sig)
            session.add(group)
            session.flush()
            card_list[0].duplicate_group_id = group.id
            grouped_cards += 1
            inserted_groups += 1
            continue

        card_list.sort(key=lambda c: c.published_at or c.id)
        current_group_id: Optional[str] = None
        window_start = None

        for card in card_list:
            if window_start is None or (
                card.published_at and window_start and card.published_at - window_start > WINDOW
            ):
                window_start = card.published_at
                current_group_id = sha256(f"{sig}|{card.id}".encode("utf-8")).hexdigest()
                group = models.DuplicateGroup(id=current_group_id, signature=sig)
                session.add(group)
                session.flush()
                inserted_groups += 1

            if current_group_id:
                card.duplicate_group_id = current_group_id
                grouped_cards += 1

    try:
        session.commit()
        logger.info("Dedup complete. Groups created=%d, cards grouped=%d", inserted_groups, grouped_cards)
    except IntegrityError:
        session.rollback()
        logger.warning("Dedup encountered duplicates during group insert; partial work may be present.")
    finally:
        session.close()


if __name__ == "__main__":
    deduplicate()
