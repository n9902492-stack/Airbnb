"""add booking changes

Revision ID: 20261002_12
Revises: 20261002_11
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_12"
down_revision = "20261002_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "booking_change_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("new_check_in", sa.Date(), nullable=False),
        sa.Column("new_check_out", sa.Date(), nullable=False),
        sa.Column("new_guest_count", sa.Integer(), nullable=False),
        sa.Column("old_total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_difference", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="requested"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_booking_change_requests_booking_id", "booking_change_requests", ["booking_id"])
    op.create_index("ix_booking_change_requests_status", "booking_change_requests", ["status"])

    op.create_table(
        "booking_change_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("change_request_id", sa.Integer(), sa.ForeignKey("booking_change_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("provider_order_id", sa.String(120), nullable=True),
        sa.Column("provider_payment_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("change_request_id", name="uq_booking_change_payment_request"),
    )
    op.create_index("ix_booking_change_payments_change_request_id", "booking_change_payments", ["change_request_id"])


def downgrade() -> None:
    op.drop_table("booking_change_payments")
    op.drop_table("booking_change_requests")
