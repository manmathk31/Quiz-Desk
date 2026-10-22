"""Question and QuestionOption models supporting single, multi-MCQ, and True/False (DEC-006)."""
from datetime import datetime
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from app.models.quiz import QuizVersion
    from app.models.attempt import AttemptAnswer


class QuestionType(str, enum.Enum):
    """Supported question types (DEC-006)."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Assessment question belonging to an immutable QuizVersion.
    """
    __tablename__ = "questions"

    quiz_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type_enum", native_enum=False),
        nullable=False,
        default=QuestionType.SINGLE_CHOICE,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_marks: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=1.00
    )
    negative_marks: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.00
    )

    # Relationships
    quiz_version: Mapped["QuizVersion"] = relationship("QuizVersion", back_populates="questions")
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order_index",
    )
    answers: Mapped[List["AttemptAnswer"]] = relationship(
        "AttemptAnswer",
        back_populates="question",
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} type={self.question_type} marks={self.positive_marks}>"


class QuestionOption(Base, UUIDPrimaryKeyMixin):
    """
    Answer choice for a question.
    `is_correct` is strictly server-side authoritative and concealed during active assessments.
    """
    __tablename__ = "question_options"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationship
    question: Mapped["Question"] = relationship("Question", back_populates="options")

    def __repr__(self) -> str:
        return f"<QuestionOption id={self.id} question_id={self.question_id} is_correct={self.is_correct}>"
