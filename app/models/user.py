from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class User(Base):
    """User database model representing admins, teachers, parents, and students."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # admin, teacher, parent, student

    # Relationships
    # Sessions taught by this user (if teacher)
    sessions_as_teacher: Mapped[list[Session]] = relationship(
        "Session",
        foreign_keys="[Session.teacher_id]",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )

    # Sessions attended by this user (if student)
    sessions_as_student: Mapped[list[Session]] = relationship(
        "Session",
        foreign_keys="[Session.student_id]",
        back_populates="student",
        cascade="all, delete-orphan",
    )
