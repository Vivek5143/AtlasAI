"""Add company discovery candidates

Revision ID: 8f3d7c9a1b2e
Revises: 3019536ec637
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f3d7c9a1b2e"
down_revision: Union[str, Sequence[str], None] = "3019536ec637"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "company_discovery_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("website_domain", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ai_category", sa.String(length=255), nullable=True),
        sa.Column("evidence_url", sa.String(length=1000), nullable=False),
        sa.Column("evidence_title", sa.String(length=500), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("source_domain", sa.String(length=255), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("confidence_reasons", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_company_id", sa.Uuid(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_company_discovery_candidates_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_approved_company_id"),
        "company_discovery_candidates",
        ["approved_company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_company_name"),
        "company_discovery_candidates",
        ["company_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_country"),
        "company_discovery_candidates",
        ["country"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_discovered_at"),
        "company_discovery_candidates",
        ["discovered_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_normalized_name"),
        "company_discovery_candidates",
        ["normalized_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_source_domain"),
        "company_discovery_candidates",
        ["source_domain"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_status"),
        "company_discovery_candidates",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_company_discovery_candidates_status_score_discovered",
        "company_discovery_candidates",
        ["status", "confidence_score", "discovered_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_website"),
        "company_discovery_candidates",
        ["website"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_discovery_candidates_website_domain"),
        "company_discovery_candidates",
        ["website_domain"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_company_discovery_candidates_website_domain"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_website"), table_name="company_discovery_candidates")
    op.drop_index("ix_company_discovery_candidates_status_score_discovered", table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_status"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_source_domain"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_normalized_name"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_discovered_at"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_country"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_company_name"), table_name="company_discovery_candidates")
    op.drop_index(op.f("ix_company_discovery_candidates_approved_company_id"), table_name="company_discovery_candidates")
    op.drop_table("company_discovery_candidates")
