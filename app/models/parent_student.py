from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ParentStudent(Base):
    """Associates parent users with student users to enforce RBAC viewing permissions."""

    __tablename__ = "parent_students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),)

    # Relationships
    parent: Mapped[User] = relationship("User", foreign_keys=[parent_id])
    student: Mapped[User] = relationship("User", foreign_keys=[student_id])
