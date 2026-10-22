"""Audit logging, grade adjustments, and CSV import job models (DEC-010, DEC-013)."""
from datetime import datetime
import uuid
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.attempt import QuizAttempt
    from app.models.user import User
    from app.models.quiz import Quiz


class GradeAdjustment(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit log entry for manual score modifications by teachers (DEC-010).
    Requires mandatory written justification.
    """
    __tablename__ = "grade_adjustments"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    adjusted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    previous_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    new_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="grade_adjustments")
    adjusted_by: Mapped["User"] = relationship("User", foreign_keys=[adjusted_by_id])

    def __repr__(self) -> str:
        return f"<GradeAdjustment attempt_id={self.attempt_id} old={self.previous_score} new={self.new_score}>"


class AuditEvent(Base, UUIDPrimaryKeyMixin):
    """
    General tamper-resistant audit event record for consequential platform actions (DEC-013).
    """
    __tablename__ = "audit_events"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False, index=True
    )

    # Relationship
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AuditEvent action={self.action} entity={self.entity_type}:{self.entity_id}>"


class ImportJob(Base, UUIDPrimaryKeyMixin):
    """
    Tracking entity for CSV import jobs (questions or student rosters).
    Preserves validation errors and dry-run outcomes before committing (DEC-006, DEC-007).
    """
    __tablename__ = "import_jobs"

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    import_type: Mapped[str] = mapped_column(String(64), nullable=False)  # "question_csv" or "roster_csv"
    target_quiz_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    target_quiz: Mapped[Optional["Quiz"]] = relationship("Quiz", foreign_keys=[target_quiz_id])

    def __repr__(self) -> str:
        return f"<ImportJob id={self.id} type={self.import_type} status={self.status}>"
