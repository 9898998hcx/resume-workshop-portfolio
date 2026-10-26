from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


CONTENT_TYPE = Text().with_variant(MEDIUMTEXT(), "mysql")


class ResumeTemplate(TimestampMixin, Base):
    __tablename__ = "resume_templates"
    __table_args__ = (
        UniqueConstraint("source_url", "source_path", name="uq_resume_templates_source_path"),
        Index("ix_resume_templates_public", "status", "is_active", "category"),
        Index("ix_resume_templates_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="professional")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(20), nullable=False, default="html_css")
    # SQLite uses TEXT; MySQL uses MEDIUMTEXT so reviewed templates up to the
    # collector's 400 KB file limit fit without truncation.
    html_content: Mapped[str | None] = mapped_column(CONTENT_TYPE, nullable=True)
    css_content: Mapped[str | None] = mapped_column(CONTENT_TYPE, nullable=True)
    schema_json: Mapped[str | None] = mapped_column(CONTENT_TYPE, nullable=True)
    preview_image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="github")
    source_commit: Mapped[str | None] = mapped_column(String(80), nullable=True)
    license: Mapped[str] = mapped_column(String(80), nullable=False)
    license_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
