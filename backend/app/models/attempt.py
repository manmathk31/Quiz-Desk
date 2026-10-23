"""Active assessment attempt, autosave, and telemetry models (DEC-008, DEC-009)."""
from datetime import datetime
import enum
import uuid
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    Numeric,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.quiz import QuizVersion
    from app.models.user import User
    from app.models.question import Question
    from app.models.audit import GradeAdjustment


class AttemptStatus(str, enum.Enum):
    """Lifecycle status of a student attempt."""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GradingStatus(str, enum.Enum):
    """
    Status of attempt score calculation and audit history (DEC-010).
    Student score visibility is strictly gated by QuizVersion.is_results_released.
    """
    PENDING = "pending"
    AUTO_GRADED = "auto_graded"
    MANUALLY_ADJUSTED = "manually_adjusted"


class QuizAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Candidate assessment attempt session.
    Server-authoritative timer and status tracking.
    """
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint("quiz_version_id", "student_id", "attempt_number", name="uq_attempt_number_per_student"),
        CheckConstraint("attempt_number >= 1", name="ck_quiz_attempt_number"),
        CheckConstraint("deadline_at >= started_at", name="ck_quiz_attempt_deadline"),
        CheckConstraint("tab_switch_count >= 0", name="ck_quiz_attempt_tab_count"),
        CheckConstraint("proctoring_deduction >= 0", name="ck_quiz_attempt_deduction"),
        CheckConstraint("violation_count >= 0", name="ck_quiz_attempt_violation_count"),
        Index("ix_quiz_attempts_student_status", "student_id", "status"),
    )

    quiz_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status_enum", native_enum=False),
        nullable=False,
        default=AttemptStatus.IN_PROGRESS,
        index=True,
    )

    # Server-Authoritative Timestamps (DEC-008)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Scoring & Release (DEC-010, DEC-021)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    proctoring_deduction: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    grading_status: Mapped[GradingStatus] = mapped_column(
        Enum(GradingStatus, name="grading_status_enum", native_enum=False),
        nullable=False,
        default=GradingStatus.PENDING,
    )
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Telemetry Counter (DEC-009, DEC-021)
    tab_switch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    violation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Stable Randomized Ordering (DEC-008, Phase 6)
    # question_order: list of question UUID strings (e.g. ["uuid1", "uuid2"])
    question_order: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    # option_order: dict mapping question UUID string to list of option UUID strings (e.g. {"uuid1": ["o1", "o2"]})
    option_order: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    quiz_version: Mapped["QuizVersion"] = relationship("QuizVersion", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="quiz_attempts")
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    telemetry_events: Mapped[List["AttemptTelemetryEvent"]] = relationship(
        "AttemptTelemetryEvent",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )
    grade_adjustments: Mapped[List["GradeAdjustment"]] = relationship(
        "GradeAdjustment",
        back_populates="attempt",
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} student_id={self.student_id} status={self.status}>"


class AttemptAnswer(Base, UUIDPrimaryKeyMixin):
    """
    Individual question response autosaved during the attempt (DEC-009).
    """
    __tablename__ = "attempt_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Selected option IDs stored as JSON array (e.g. ["uuid1", "uuid2"])
    selected_option_ids: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    is_marked_for_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    awarded_marks: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    # Monotonic client timestamp to reject out-of-order stale saves
    client_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        return f"<AttemptAnswer attempt_id={self.attempt_id} question_id={self.question_id}>"


class AttemptTelemetryEvent(Base, UUIDPrimaryKeyMixin):
    """
    Audit telemetry for proctoring observations (e.g., tab switches, focus changes).
    Treated strictly as contextual telemetry, not proof of cheating (DEC-009).
    """
    __tablename__ = "attempt_telemetry_events"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    client_event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    event_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationship
    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="telemetry_events")

    def __repr__(self) -> str:
        return f"<AttemptTelemetryEvent attempt_id={self.attempt_id} type={self.event_type}>"
