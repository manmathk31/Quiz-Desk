"""Student assignment and roster management models (DEC-007)."""
from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.quiz import Quiz
    from app.models.user import User


class QuizAssignment(Base, UUIDPrimaryKeyMixin):
    """
    Roster record linking a student to an assessment via CSV upload (DEC-007).
    Schema strictly requires: prn, name, email, division.
    Access to a quiz is controlled strictly by existence of this record.
    Division is informational only and not an access-control mechanism.
    """
    __tablename__ = "quiz_assignments"
    __table_args__ = (
        UniqueConstraint("quiz_id", "student_prn", name="uq_quiz_assignment_prn"),
        UniqueConstraint("quiz_id", "student_email", name="uq_quiz_assignment_email"),
        Index("ix_quiz_assignments_lookup", "quiz_id", "student_email"),
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_prn: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    student_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    division: Mapped[str] = mapped_column(String(32), nullable=False)

    assigned_student_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="assignments")
    assigned_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_student_id])

    def __repr__(self) -> str:
        return f"<QuizAssignment quiz_id={self.quiz_id} prn={self.student_prn} division={self.division}>"
