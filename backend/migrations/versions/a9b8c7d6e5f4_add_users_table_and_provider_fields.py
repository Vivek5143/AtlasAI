"""Add users table and provider fields to company discovery candidates

Revision ID: a9b8c7d6e5f4
Revises: 8f3d7c9a1b2e
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "8f3d7c9a1b2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # Add provider fields to company_discovery_candidates
    op.add_column(
        "company_discovery_candidates",
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="tavily"),
    )
    op.add_column(
        "company_discovery_candidates",
        sa.Column("provider_company_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "company_discovery_candidates",
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_provider"),
        "company_discovery_candidates",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_provider_company_id"),
        "company_discovery_candidates",
        ["provider_company_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_company_discovery_candidates_provider_company_id"),
        table_name="company_discovery_candidates",
    )
    op.drop_index(
        op.f("ix_company_discovery_candidates_provider"),
        table_name="company_discovery_candidates",
    )
    op.drop_column("company_discovery_candidates", "provider_metadata")
    op.drop_column("company_discovery_candidates", "provider_company_id")
    op.drop_column("company_discovery_candidates", "provider")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
