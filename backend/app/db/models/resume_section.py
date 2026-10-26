from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .resume import Resume


class ResumeSection(TimestampMixin, Base):
    __tablename__ = "resume_sections"
    __table_args__ = (
        Index("ix_resume_sections_resume_position", "resume_id", "position"),
        Index("ix_resume_sections_resume_type", "resume_id", "section_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_visible: Mapped[bool] = mapped_column(nullable=False, default=True)
    content: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON, nullable=False, default=dict)

    resume: Mapped["Resume"] = relationship(back_populates="sections")
