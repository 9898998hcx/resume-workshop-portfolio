"""Create the phase-one foundation tables.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-10-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def upgrade() -> None:
    created_at, updated_at = _timestamps()
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        created_at,
        updated_at,
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_status", "users", ["status"], unique=False)
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("identifier_normalized", sa.String(length=255), nullable=False),
        sa.Column("credential_hash", sa.String(length=255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=False), nullable=True),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_auth_identities_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_identities"),
        sa.UniqueConstraint(
            "provider", "identifier_normalized", name="uq_auth_identity_provider_identifier"
        ),
    )
    op.create_index("ix_auth_identity_user_id", "auth_identities", ["user_id"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "phone_otp",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("phone_hash", sa.String(length=128), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("consumed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=False), nullable=True),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_phone_otp_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_phone_otp"),
    )
    op.create_index(
        "ix_phone_otp_lookup", "phone_otp", ["phone_hash", "purpose", "created_at"], unique=False
    )
    op.create_index("ix_phone_otp_expiry", "phone_otp", ["expires_at", "consumed_at"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("template_key", sa.String(length=80), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name="fk_resumes_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_resumes"),
    )
    op.create_index("ix_resumes_user_updated", "resumes", ["user_id", "updated_at"], unique=False)
    op.create_index("ix_resumes_user_status", "resumes", ["user_id", "status"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "resume_sections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("section_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("content", sa.JSON(), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["resume_id"], ["resumes.id"], ondelete="CASCADE", name="fk_resume_sections_resume_id_resumes"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_resume_sections"),
    )
    op.create_index(
        "ix_resume_sections_resume_position", "resume_sections", ["resume_id", "position"], unique=False
    )
    op.create_index(
        "ix_resume_sections_resume_type", "resume_sections", ["resume_id", "section_type"], unique=False
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "ai_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("resume_id", sa.String(length=36), nullable=True),
        sa.Column("job_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("provider", sa.String(length=30), nullable=False, server_default="mock"),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=False), nullable=True),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL", name="fk_ai_jobs_user_id_users"
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"], ["resumes.id"], ondelete="SET NULL", name="fk_ai_jobs_resume_id_resumes"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_jobs"),
    )
    op.create_index("ix_ai_jobs_user_created", "ai_jobs", ["user_id", "created_at"], unique=False)
    op.create_index("ix_ai_jobs_status_created", "ai_jobs", ["status", "created_at"], unique=False)

    created_at, updated_at = _timestamps()
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="SET NULL", name="fk_audit_logs_actor_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "ix_audit_logs_actor_created", "audit_logs", ["actor_user_id", "created_at"], unique=False
    )
    op.create_index("ix_audit_logs_target", "audit_logs", ["target_type", "target_id"], unique=False)
    op.create_index(
        "ix_audit_logs_action_created", "audit_logs", ["action", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_ai_jobs_status_created", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_user_created", table_name="ai_jobs")
    op.drop_table("ai_jobs")
    op.drop_index("ix_resume_sections_resume_type", table_name="resume_sections")
    op.drop_index("ix_resume_sections_resume_position", table_name="resume_sections")
    op.drop_table("resume_sections")
    op.drop_index("ix_resumes_user_status", table_name="resumes")
    op.drop_index("ix_resumes_user_updated", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index("ix_phone_otp_expiry", table_name="phone_otp")
    op.drop_index("ix_phone_otp_lookup", table_name="phone_otp")
    op.drop_table("phone_otp")
    op.drop_index("ix_auth_identity_user_id", table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
