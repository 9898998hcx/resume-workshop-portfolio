from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from .ai_job import AiJob
    from .resume_section import ResumeSection
    from .user import User


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"
    __table_args__ = (
        Index("ix_resumes_user_updated", "user_id", "updated_at"),
        Index("ix_resumes_user_status", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    template_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user: Mapped["User"] = relationship(back_populates="resumes")
    sections: Mapped[list["ResumeSection"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeSection.position"
    )
    ai_jobs: Mapped[list["AiJob"]] = relationship(back_populates="resume")
