"""add optional transfer service

Revision ID: 20261002_03
Revises: 20261002_02
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_03"
down_revision = "20261002_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    direction = sa.Enum("PICKUP_TO_STAY", "STAY_TO_DROPOFF", name="transfer_direction")
    place_type = sa.Enum("AIRPORT", "RAILWAY", "BUS_STAND", "CUSTOM", name="transfer_place_type")
    status = sa.Enum("REQUESTED", "CONFIRMED", "CANCELLED", "COMPLETED", name="transfer_status")

    direction.create(op.get_bind(), checkfirst=True)
    place_type.create(op.get_bind(), checkfirst=True)
    status.create(op.get_bind(), checkfirst=True)

    op.add_column("properties", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("properties", sa.Column("longitude", sa.Float(), nullable=True))

    op.create_table(
        "transfer_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("direction", direction, nullable=False),
        sa.Column("place_type", place_type, nullable=False),
        sa.Column("place_name", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("booking_id", name="uq_transfer_requests_booking_id"),
    )
    op.create_index("ix_transfer_requests_booking_id", "transfer_requests", ["booking_id"])
    op.create_index("ix_transfer_requests_guest_id", "transfer_requests", ["guest_id"])
    op.create_index("ix_transfer_requests_property_id", "transfer_requests", ["property_id"])


def downgrade() -> None:
    op.drop_table("transfer_requests")
    op.drop_column("properties", "longitude")
    op.drop_column("properties", "latitude")
    sa.Enum(name="transfer_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transfer_place_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transfer_direction").drop(op.get_bind(), checkfirst=True)
