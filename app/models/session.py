from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.user import User


class Session(Base):
    """Session database model linking teachers and students."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    teacher: Mapped[User] = relationship(
        "User", foreign_keys=[teacher_id], back_populates="sessions_as_teacher"
    )
    student: Mapped[User] = relationship(
        "User", foreign_keys=[student_id], back_populates="sessions_as_student"
    )
    evaluations: Mapped[list[Evaluation]] = relationship(
        "Evaluation", back_populates="session", cascade="all, delete-orphan"
    )
