"""Create core Nestora tables.

Revision ID: 0001
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = sa.Enum("user", "owner", "super_admin", name="user_role")
property_status = sa.Enum(
    "draft", "pending", "live", "rejected", "paused", name="property_status"
)
booking_status = sa.Enum(
    "pending", "confirmed", "cancelled", "completed", name="booking_status"
)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    property_status.create(op.get_bind(), checkfirst=True)
    booking_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("property_type", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("guests", sa.Integer(), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=False),
        sa.Column("beds", sa.Integer(), nullable=False),
        sa.Column("bathrooms", sa.Integer(), nullable=False),
        sa.Column("price_per_night", sa.Numeric(10, 2), nullable=False),
        sa.Column("cleaning_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("amenities", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("house_rules", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("image_urls", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("check_in_time", sa.String(length=20), nullable=False),
        sa.Column("check_out_time", sa.String(length=20), nullable=False),
        sa.Column("status", property_status, nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_properties_owner_id", "properties", ["owner_id"])
    op.create_index("ix_properties_city", "properties", ["city"])
    op.create_index("ix_properties_status", "properties", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "property_id",
            sa.Integer(),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "guest_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("service_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", booking_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_bookings_property_id", "bookings", ["property_id"])
    op.create_index("ix_bookings_guest_id", "bookings", ["guest_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("properties")
    op.drop_table("users")

    booking_status.drop(op.get_bind(), checkfirst=True)
    property_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
