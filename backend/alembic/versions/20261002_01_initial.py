"""initial auth, listings, bookings and OTP tables

Revision ID: 20261002_01
Revises:
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa

revision = '20261002_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum('USER', 'OWNER', 'SUPER_ADMIN', name='user_role')
    property_status = sa.Enum('DRAFT', 'PENDING', 'LIVE', 'REJECTED', 'PAUSED', name='property_status')
    booking_status = sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', name='booking_status')
    verification_purpose = sa.Enum('EMAIL_VERIFICATION', 'PASSWORD_RESET', name='verification_purpose')
    user_role.create(op.get_bind(), checkfirst=True)
    property_status.create(op.get_bind(), checkfirst=True)
    booking_status.create(op.get_bind(), checkfirst=True)
    verification_purpose.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(120), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', user_role, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    op.create_table(
        'properties',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(180), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('property_type', sa.String(80), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('address_line', sa.String(255), nullable=False),
        sa.Column('city', sa.String(120), nullable=False),
        sa.Column('state', sa.String(120), nullable=False),
        sa.Column('country', sa.String(120), nullable=False),
        sa.Column('postal_code', sa.String(20), nullable=False),
        sa.Column('guests', sa.Integer(), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=False),
        sa.Column('beds', sa.Integer(), nullable=False),
        sa.Column('bathrooms', sa.Integer(), nullable=False),
        sa.Column('price_per_night', sa.Numeric(10, 2), nullable=False),
        sa.Column('cleaning_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('amenities', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('house_rules', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('image_urls', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('check_in_time', sa.String(20), nullable=False),
        sa.Column('check_out_time', sa.String(20), nullable=False),
        sa.Column('status', property_status, nullable=False),
        sa.Column('rejection_reason', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_properties_owner_id', 'properties', ['owner_id'])
    op.create_index('ix_properties_city', 'properties', ['city'])
    op.create_index('ix_properties_status', 'properties', ['status'])

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('property_id', sa.Integer(), sa.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False),
        sa.Column('guest_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('check_in', sa.Date(), nullable=False),
        sa.Column('check_out', sa.Date(), nullable=False),
        sa.Column('guest_count', sa.Integer(), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('service_fee', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', booking_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'verification_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purpose', verification_purpose, nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('verification_codes')
    op.drop_table('bookings')
    op.drop_table('properties')
    op.drop_table('users')
