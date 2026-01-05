"""Initial database schema for hurricane triage."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    card_mode = sa.Enum("action", "info", name="card_mode")
    card_category = sa.Enum(
        "shelter", "medical", "food-water", "utilities", "transportation", name="card_category"
    )
    card_urgency = sa.Enum("low", "medium", "high", name="card_urgency")
    card_county = sa.Enum("broward", "miami-dade", name="card_county")

    op.create_table(
        "raw_updates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_item_id", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.UniqueConstraint("source", "source_url", name="uq_raw_updates_source_url"),
        sa.UniqueConstraint("source", "source_item_id", name="uq_raw_updates_source_item"),
    )
    op.create_index("ix_raw_updates_published_at", "raw_updates", ["published_at"], unique=False)
    op.create_index("ix_raw_updates_source", "raw_updates", ["source"], unique=False)

    op.create_table(
        "clean_updates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("raw_update_id", sa.String(), sa.ForeignKey("raw_updates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cleaned_text", sa.Text(), nullable=False),
        sa.Column("cleaned_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("raw_update_id", name="uq_clean_updates_raw_update_id"),
    )

    op.create_table(
        "duplicate_groups",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
    )

    op.create_table(
        "cards",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "clean_update_id", sa.String(), sa.ForeignKey("clean_updates.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("mode", card_mode, nullable=False),
        sa.Column("category", card_category, nullable=False),
        sa.Column("action_type", sa.String(), nullable=True),
        sa.Column("urgency", card_urgency, nullable=False),
        sa.Column("county", card_county, nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duplicate_group_id", sa.String(), sa.ForeignKey("duplicate_groups.id", ondelete="SET NULL")),
        sa.CheckConstraint("mode in ('action','info')", name="ck_cards_mode_valid"),
    )

    op.create_index("ix_cards_mode", "cards", ["mode"], unique=False)
    op.create_index("ix_cards_category", "cards", ["category"], unique=False)
    op.create_index("ix_cards_urgency", "cards", ["urgency"], unique=False)
    op.create_index("ix_cards_county", "cards", ["county"], unique=False)
    op.create_index("ix_cards_published_at", "cards", ["published_at"], unique=False)
    op.create_index("ix_cards_duplicate_group_id", "cards", ["duplicate_group_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cards_duplicate_group_id", table_name="cards")
    op.drop_index("ix_cards_published_at", table_name="cards")
    op.drop_index("ix_cards_county", table_name="cards")
    op.drop_index("ix_cards_urgency", table_name="cards")
    op.drop_index("ix_cards_category", table_name="cards")
    op.drop_index("ix_cards_mode", table_name="cards")
    op.drop_table("cards")

    op.drop_table("duplicate_groups")

    op.drop_table("clean_updates")

    op.drop_index("ix_raw_updates_source", table_name="raw_updates")
    op.drop_index("ix_raw_updates_published_at", table_name="raw_updates")
    op.drop_table("raw_updates")

    card_mode = sa.Enum("action", "info", name="card_mode")
    card_category = sa.Enum(
        "shelter", "medical", "food-water", "utilities", "transportation", name="card_category"
    )
    card_urgency = sa.Enum("low", "medium", "high", name="card_urgency")
    card_county = sa.Enum("broward", "miami-dade", name="card_county")

    card_mode.drop(op.get_bind(), checkfirst=True)
    card_category.drop(op.get_bind(), checkfirst=True)
    card_urgency.drop(op.get_bind(), checkfirst=True)
    card_county.drop(op.get_bind(), checkfirst=True)
