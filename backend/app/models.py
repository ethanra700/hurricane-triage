from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RawUpdate(Base):
    __tablename__ = "raw_updates"

    id = Column("id", String, primary_key=True)
    source = Column(String, nullable=False)
    source_url = Column(Text, nullable=False)
    source_item_id = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_text = Column(Text, nullable=False)
    raw_html = Column(Text, nullable=True)
    content_hash = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "source_url", name="uq_raw_updates_source_url"),
        UniqueConstraint("source", "source_item_id", name="uq_raw_updates_source_item"),
        Index("ix_raw_updates_published_at", "published_at"),
        Index("ix_raw_updates_source", "source"),
    )

    clean_update = relationship("CleanUpdate", back_populates="raw_update", uselist=False)


class CleanUpdate(Base):
    __tablename__ = "clean_updates"

    id = Column("id", String, primary_key=True)
    raw_update_id = Column(String, ForeignKey("raw_updates.id", ondelete="CASCADE"), nullable=False, unique=True)
    cleaned_text = Column(Text, nullable=False)
    cleaned_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    raw_update = relationship("RawUpdate", back_populates="clean_update")
    cards = relationship("Card", back_populates="clean_update")


class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"

    id = Column("id", String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    signature = Column(Text, nullable=True)

    cards = relationship("Card", back_populates="duplicate_group")


mode_enum = Enum("action", "info", name="card_mode")
category_enum = Enum(
    "shelter",
    "medical",
    "food-water",
    "utilities",
    "transportation",
    name="card_category",
)
urgency_enum = Enum("low", "medium", "high", name="card_urgency")
county_enum = Enum("broward", "miami-dade", name="card_county")


class Card(Base):
    __tablename__ = "cards"

    id = Column("id", String, primary_key=True)
    clean_update_id = Column(String, ForeignKey("clean_updates.id", ondelete="CASCADE"), nullable=False)
    mode = Column(mode_enum, nullable=False)
    category = Column(category_enum, nullable=False)
    action_type = Column(String, nullable=True)
    urgency = Column(urgency_enum, nullable=False)
    county = Column(county_enum, nullable=False)
    city = Column(String, nullable=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    source_url = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    duplicate_group_id = Column(String, ForeignKey("duplicate_groups.id", ondelete="SET NULL"), nullable=True)

    clean_update = relationship("CleanUpdate", back_populates="cards")
    duplicate_group = relationship("DuplicateGroup", back_populates="cards")

    __table_args__ = (
        Index("ix_cards_mode", "mode"),
        Index("ix_cards_category", "category"),
        Index("ix_cards_urgency", "urgency"),
        Index("ix_cards_county", "county"),
        Index("ix_cards_published_at", "published_at"),
        Index("ix_cards_duplicate_group_id", "duplicate_group_id"),
        CheckConstraint("mode in ('action','info')", name="ck_cards_mode_valid"),
    )
