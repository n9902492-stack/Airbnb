"""add reviews table

Revision ID: 20261002_02
Revises: 20261002_01
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_02"
down_revision = "20261002_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "property_id",
            sa.Integer(),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "guest_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating",
        ),
        sa.UniqueConstraint("booking_id", name="uq_reviews_booking_id"),
    )
    op.create_index("ix_reviews_property_id", "reviews", ["property_id"])
    op.create_index("ix_reviews_guest_id", "reviews", ["guest_id"])


def downgrade() -> None:
    op.drop_table("reviews")
