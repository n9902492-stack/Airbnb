"""add trust promotions collaboration and messaging expansion

Revision ID: 20261002_11
Revises: 20261002_10
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_11"
down_revision = "20261002_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("cancellation_policy", sa.String(30), nullable=False, server_default="moderate"),
    )

    op.add_column(
        "bookings",
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "bookings",
        sa.Column("promo_code", sa.String(40), nullable=True),
    )

    op.add_column(
        "booking_messages",
        sa.Column("attachment_url", sa.String(600), nullable=True),
    )
    op.add_column(
        "booking_messages",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column(
        "booking_messages",
        "body",
        existing_type=sa.Text(),
        nullable=False,
        server_default="",
    )

    op.add_column(
        "wishlist_collections",
        sa.Column("proposed_start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "wishlist_collections",
        sa.Column("proposed_end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "wishlist_collections",
        sa.Column("guest_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "wishlist_collection_items",
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_table(
        "wishlist_votes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("wishlist_collection_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("item_id", "user_id", name="uq_wishlist_vote_user_item"),
    )
    op.create_index("ix_wishlist_votes_item_id", "wishlist_votes", ["item_id"])
    op.create_index("ix_wishlist_votes_user_id", "wishlist_votes", ["user_id"])

    op.create_table(
        "promotion_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("minimum_spend", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_promotion_codes_code"),
    )
    op.create_index("ix_promotion_codes_code", "promotion_codes", ["code"])

    op.create_table(
        "promotion_redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("promotion_id", sa.Integer(), sa.ForeignKey("promotion_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("booking_id", name="uq_promotion_redemption_booking"),
    )
    op.create_index("ix_promotion_redemptions_promotion_id", "promotion_redemptions", ["promotion_id"])
    op.create_index("ix_promotion_redemptions_booking_id", "promotion_redemptions", ["booking_id"])
    op.create_index("ix_promotion_redemptions_user_id", "promotion_redemptions", ["user_id"])

    op.create_table(
        "identity_verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_started"),
        sa.Column("provider", sa.String(60), nullable=False, server_default="manual_review"),
        sa.Column("provider_reference", sa.String(180), nullable=True),
        sa.Column("document_type", sa.String(50), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_identity_verifications_user_id"),
    )
    op.create_index("ix_identity_verifications_user_id", "identity_verifications", ["user_id"])
    op.create_index("ix_identity_verifications_status", "identity_verifications", ["status"])

    op.create_table(
        "support_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("case_type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("assigned_admin_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_support_cases_reporter_id", "support_cases", ["reporter_id"])
    op.create_index("ix_support_cases_booking_id", "support_cases", ["booking_id"])
    op.create_index("ix_support_cases_case_type", "support_cases", ["case_type"])
    op.create_index("ix_support_cases_status", "support_cases", ["status"])

    op.create_table(
        "resolution_claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claimant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("respondent_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_urls", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="requested"),
        sa.Column("response_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resolution_claims_booking_id", "resolution_claims", ["booking_id"])
    op.create_index("ix_resolution_claims_claimant_id", "resolution_claims", ["claimant_id"])
    op.create_index("ix_resolution_claims_respondent_id", "resolution_claims", ["respondent_id"])
    op.create_index("ix_resolution_claims_status", "resolution_claims", ["status"])

    op.create_table(
        "offering_availability_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offering_id", sa.Integer(), sa.ForeignKey("marketplace_offerings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("price_override", sa.Numeric(10, 2), nullable=True),
        sa.Column("private_group_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_private_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_offering_availability_slots_offering_id", "offering_availability_slots", ["offering_id"])
    op.create_index("ix_offering_availability_slots_starts_at", "offering_availability_slots", ["starts_at"])

    op.create_table(
        "message_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_message_templates_owner_user_id", "message_templates", ["owner_user_id"])

    op.create_table(
        "scheduled_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scheduled_messages_booking_id", "scheduled_messages", ["booking_id"])
    op.create_index("ix_scheduled_messages_sender_id", "scheduled_messages", ["sender_id"])
    op.create_index("ix_scheduled_messages_send_at", "scheduled_messages", ["send_at"])


def downgrade() -> None:
    op.drop_table("scheduled_messages")
    op.drop_table("message_templates")
    op.drop_table("offering_availability_slots")
    op.drop_table("resolution_claims")
    op.drop_table("support_cases")
    op.drop_table("identity_verifications")
    op.drop_table("promotion_redemptions")
    op.drop_table("promotion_codes")
    op.drop_table("wishlist_votes")

    op.drop_column("wishlist_collection_items", "note")
    op.drop_column("wishlist_collections", "guest_count")
    op.drop_column("wishlist_collections", "proposed_end_date")
    op.drop_column("wishlist_collections", "proposed_start_date")

    op.drop_column("booking_messages", "read_at")
    op.drop_column("booking_messages", "attachment_url")

    op.drop_column("bookings", "promo_code")
    op.drop_column("bookings", "discount_amount")

    op.drop_column("properties", "cancellation_policy")
