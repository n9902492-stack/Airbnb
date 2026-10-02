"""add payment lifecycle fields

Revision ID: 20261002_05
Revises: 20261002_04
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_05"
down_revision = "20261002_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("cancellation_reason", sa.String(255), nullable=True),
    )

    op.add_column(
        "payments",
        sa.Column(
            "refund_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "payments",
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payments", "refunded_at")
    op.drop_column("payments", "refund_amount")
    op.drop_column("bookings", "cancellation_reason")
    op.drop_column("bookings", "cancelled_at")
    op.drop_column("bookings", "expires_at")
