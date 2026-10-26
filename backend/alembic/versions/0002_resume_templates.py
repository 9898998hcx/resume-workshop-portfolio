"""Add resume template catalog storage.

Revision ID: 0002_resume_templates
Revises: 0001_foundation
Create Date: 2026-10-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0002_resume_templates"
down_revision: Union[str, None] = "0001_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONTENT_TYPE = sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


def upgrade() -> None:
    op.create_table(
        "resume_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="professional"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(length=20), nullable=False, server_default="html_css"),
        sa.Column("html_content", CONTENT_TYPE, nullable=True),
        sa.Column("css_content", CONTENT_TYPE, nullable=True),
        sa.Column("schema_json", CONTENT_TYPE, nullable=True),
        sa.Column("preview_image", sa.String(length=2048), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(length=20), nullable=False, server_default="github"),
        sa.Column("source_commit", sa.String(length=80), nullable=True),
        sa.Column("license", sa.String(length=80), nullable=False),
        sa.Column("license_url", sa.String(length=2048), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name="pk_resume_templates"),
        sa.UniqueConstraint("slug", name="uq_resume_templates_slug"),
        sa.UniqueConstraint("source_url", "source_path", name="uq_resume_templates_source_path"),
    )
    op.create_index(
        "ix_resume_templates_public",
        "resume_templates",
        ["status", "is_active", "category"],
        unique=False,
    )
    op.create_index("ix_resume_templates_created", "resume_templates", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resume_templates_created", table_name="resume_templates")
    op.drop_index("ix_resume_templates_public", table_name="resume_templates")
    op.drop_table("resume_templates")
