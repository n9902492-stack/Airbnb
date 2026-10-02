"""add availability blocks and payments

Revision ID: 20261002_04
Revises: 20261002_03
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_04"
down_revision = "20261002_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payment_status = sa.Enum(
        "CREATED", "PENDING", "PAID", "FAILED", "REFUNDED",
        name="payment_status",
    )
    payment_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "availability_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_availability_blocks_property_id", "availability_blocks", ["property_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_order_id", sa.String(120)),
        sa.Column("provider_payment_id", sa.String(120)),
        sa.Column("amount", sa.Numeric(10,2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("booking_id", name="uq_payments_booking_id"),
    )
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    op.create_index("ix_payments_status", "payments", ["status"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("availability_blocks")
    sa.Enum(name="payment_status").drop(op.get_bind(), checkfirst=True)
