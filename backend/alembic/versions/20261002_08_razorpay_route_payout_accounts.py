"""add razorpay route owner payout accounts

Revision ID: 20261002_08
Revises: 20261002_07
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_08"
down_revision = "20261002_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owner_payout_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(40),
            nullable=False,
            server_default="razorpay_route",
        ),
        sa.Column("linked_account_id", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
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
        sa.UniqueConstraint("owner_id", name="uq_owner_payout_accounts_owner_id"),
    )
    op.create_index(
        "ix_owner_payout_accounts_owner_id",
        "owner_payout_accounts",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_table("owner_payout_accounts")
