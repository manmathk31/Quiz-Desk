"""Quiz and immutable QuizVersion relational models (DEC-006, DEC-008)."""
from datetime import datetime, timezone
import enum
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    Numeric,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.question import Question
    from app.models.roster import QuizAssignment
    from app.models.attempt import QuizAttempt


class QuizStatus(str, enum.Enum):
    """Lifecycle status of a quiz."""
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class MultiAnswerPolicy(str, enum.Enum):
    """Scoring policies for questions with multiple correct options (DEC-006, DEC-008)."""
    ALL_OR_NOTHING = "all_or_nothing"
    PARTIAL_WITH_PENALTY = "partial_with_penalty"
    PARTIAL_NO_PENALTY = "partial_no_penalty"


class Quiz(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Top-level assessment entity.
    Maintains quiz metadata, ownership, and links to published versions.
    """
    __tablename__ = "quizzes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    course_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[QuizStatus] = mapped_column(
        Enum(QuizStatus, name="quiz_status_enum", native_enum=False),
        nullable=False,
        default=QuizStatus.DRAFT,
        index=True,
    )
    current_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_quizzes", foreign_keys=[created_by_id])
    versions: Mapped[List["QuizVersion"]] = relationship(
        "QuizVersion",
        back_populates="quiz",
        order_by="QuizVersion.version_number",
        foreign_keys="QuizVersion.quiz_id",
    )
    assignments: Mapped[List["QuizAssignment"]] = relationship(
        "QuizAssignment",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} title={self.title} status={self.status}>"


class QuizVersion(Base, UUIDPrimaryKeyMixin):
    """
    Immutable version snapshot of an assessment (DEC-006, DEC-008).
    Once published (is_published=True), attempts link directly to this immutable version snapshot.
    Protected with ON DELETE RESTRICT from the parent quiz to prevent accidental history erasure.
    """
    __tablename__ = "quiz_versions"
    __table_args__ = (
        UniqueConstraint("quiz_id", "version_number", name="uq_quiz_version_number"),
        CheckConstraint("duration_minutes > 0", name="ck_quiz_version_duration"),
        CheckConstraint("max_attempts > 0", name="ck_quiz_version_max_attempts"),
        CheckConstraint("closes_at > opens_at", name="ck_quiz_version_time_window"),
        CheckConstraint("tab_switch_limit >= 0", name="ck_quiz_version_tab_limit"),
        CheckConstraint("tab_switch_penalty_marks >= 0", name="ck_quiz_version_tab_penalty"),
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Immutability & Lifecycle Status
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Timings & Duration (DEC-008)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Assessment Rules & Policies
    allow_backtracking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    multi_answer_policy: Mapped[MultiAnswerPolicy] = mapped_column(
        Enum(MultiAnswerPolicy, name="multi_answer_policy_enum", native_enum=False),
        nullable=False,
        default=MultiAnswerPolicy.ALL_OR_NOTHING,
    )

    # Telemetry Configuration (DEC-009)
    tab_switch_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    tab_switch_penalty_marks: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.00
    )

    # Result Release Workflow (DEC-010)
    is_results_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    results_released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    results_released_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="versions", foreign_keys=[quiz_id])
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="quiz_version",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz_version",
    )

    def __repr__(self) -> str:
        return f"<QuizVersion id={self.id} quiz_id={self.quiz_id} v={self.version_number} published={self.is_published}>"
