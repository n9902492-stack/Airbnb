"""add pricing payout and auth security

Revision ID: 20261002_07
Revises: 20261002_06
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_07"
down_revision = "20261002_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payout_status = sa.Enum(
        "PENDING", "READY", "PROCESSING", "PAID", "FAILED", "CANCELLED",
        name="payout_status",
    )
    payout_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "properties",
        sa.Column("weekend_price_per_night", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column("minimum_stay_nights", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "properties",
        sa.Column("maximum_stay_nights", sa.Integer(), nullable=True),
    )

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("nightly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("minimum_stay_nights", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pricing_rules_property_id", "pricing_rules", ["property_id"])

    op.create_table(
        "owner_payouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gross_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("platform_commission", sa.Numeric(10, 2), nullable=False),
        sa.Column("owner_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("refund_adjustment", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", payout_status, nullable=False),
        sa.Column("provider_reference", sa.String(160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("booking_id", name="uq_owner_payout_booking_id"),
    )
    op.create_index("ix_owner_payouts_booking_id", "owner_payouts", ["booking_id"])
    op.create_index("ix_owner_payouts_owner_id", "owner_payouts", ["owner_id"])
    op.create_index("ix_owner_payouts_status", "owner_payouts", ["status"])

    op.create_table(
        "auth_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_events_email", "auth_events", ["email"])
    op.create_index("ix_auth_events_event_type", "auth_events", ["event_type"])
    op.create_index("ix_auth_events_created_at", "auth_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("auth_events")
    op.drop_table("owner_payouts")
    op.drop_table("pricing_rules")
    op.drop_column("properties", "maximum_stay_nights")
    op.drop_column("properties", "minimum_stay_nights")
    op.drop_column("properties", "weekend_price_per_night")
    sa.Enum(name="payout_status").drop(op.get_bind(), checkfirst=True)
