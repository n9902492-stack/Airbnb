"""add marketplace expansion

Revision ID: 20261002_10
Revises: 20261002_09
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20261002_10"
down_revision = "20261002_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum values cannot be added through a normal ALTER COLUMN.
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'REQUESTED'")

    op.add_column(
        "properties",
        sa.Column("booking_mode", sa.String(30), nullable=False, server_default="instant"),
    )
    op.add_column(
        "properties",
        sa.Column("guest_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_properties_booking_mode", "properties", ["booking_mode"])
    op.create_index("ix_properties_guest_favorite", "properties", ["guest_favorite"])

    op.create_table(
        "host_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("languages", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("interests", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("work", sa.String(180), nullable=True),
        sa.Column("verified_identity", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("response_rate", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("response_time_label", sa.String(80), nullable=False, server_default="within an hour"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_host_profiles_user_id"),
    )
    op.create_index("ix_host_profiles_user_id", "host_profiles", ["user_id"])

    op.create_table(
        "property_cohosts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission", sa.String(40), nullable=False, server_default="calendar"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("property_id", "user_id", name="uq_property_cohost"),
    )
    op.create_index("ix_property_cohosts_property_id", "property_cohosts", ["property_id"])
    op.create_index("ix_property_cohosts_user_id", "property_cohosts", ["user_id"])

    op.create_table(
        "wishlist_collections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("share_token", name="uq_wishlist_collections_share_token"),
    )
    op.create_index("ix_wishlist_collections_owner_user_id", "wishlist_collections", ["owner_user_id"])
    op.create_index("ix_wishlist_collections_share_token", "wishlist_collections", ["share_token"])

    op.create_table(
        "wishlist_collection_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("wishlist_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="editor"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("collection_id", "user_id", name="uq_wishlist_collection_member"),
    )
    op.create_index("ix_wishlist_collection_members_collection_id", "wishlist_collection_members", ["collection_id"])
    op.create_index("ix_wishlist_collection_members_user_id", "wishlist_collection_members", ["user_id"])

    op.create_table(
        "wishlist_collection_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("wishlist_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("collection_id", "property_id", name="uq_wishlist_collection_property"),
    )
    op.create_index("ix_wishlist_collection_items_collection_id", "wishlist_collection_items", ["collection_id"])
    op.create_index("ix_wishlist_collection_items_property_id", "wishlist_collection_items", ["property_id"])

    op.create_table(
        "special_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_special_offers_property_id", "special_offers", ["property_id"])
    op.create_index("ix_special_offers_owner_id", "special_offers", ["owner_id"])
    op.create_index("ix_special_offers_guest_id", "special_offers", ["guest_id"])
    op.create_index("ix_special_offers_status", "special_offers", ["status"])

    op.create_table(
        "marketplace_offerings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("state", sa.String(120), nullable=False),
        sa.Column("country", sa.String(120), nullable=False, server_default="India"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("pricing_unit", sa.String(30), nullable=False, server_default="per_guest"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("image_urls", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("included_items", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("requirements", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("instant_book", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketplace_offerings_host_id", "marketplace_offerings", ["host_id"])
    op.create_index("ix_marketplace_offerings_kind", "marketplace_offerings", ["kind"])
    op.create_index("ix_marketplace_offerings_category", "marketplace_offerings", ["category"])
    op.create_index("ix_marketplace_offerings_city", "marketplace_offerings", ["city"])
    op.create_index("ix_marketplace_offerings_status", "marketplace_offerings", ["status"])

    op.create_table(
        "offering_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offering_id", sa.Integer(), sa.ForeignKey("marketplace_offerings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("guest_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("service_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("payment_status", sa.String(30), nullable=False, server_default="unpaid"),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("provider_order_id", sa.String(120), nullable=True),
        sa.Column("provider_payment_id", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_offering_bookings_offering_id", "offering_bookings", ["offering_id"])
    op.create_index("ix_offering_bookings_guest_id", "offering_bookings", ["guest_id"])
    op.create_index("ix_offering_bookings_status", "offering_bookings", ["status"])
    op.create_index("ix_offering_bookings_payment_status", "offering_bookings", ["payment_status"])


def downgrade() -> None:
    op.drop_table("offering_bookings")
    op.drop_table("marketplace_offerings")
    op.drop_table("special_offers")
    op.drop_table("wishlist_collection_items")
    op.drop_table("wishlist_collection_members")
    op.drop_table("wishlist_collections")
    op.drop_table("property_cohosts")
    op.drop_table("host_profiles")
    op.drop_index("ix_properties_guest_favorite", table_name="properties")
    op.drop_index("ix_properties_booking_mode", table_name="properties")
    op.drop_column("properties", "guest_favorite")
    op.drop_column("properties", "booking_mode")
    # PostgreSQL enum value REQUESTED is intentionally retained on downgrade.
