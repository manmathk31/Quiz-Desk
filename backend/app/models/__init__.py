"""SQLAlchemy declarative models registry for Quizdesk."""
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import User, StudentProfile, UserRole
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.models.roster import QuizAssignment
from app.models.attempt import (
    QuizAttempt,
    AttemptAnswer,
    AttemptTelemetryEvent,
    AttemptStatus,
    GradingStatus,
)
from app.models.audit import GradeAdjustment, AuditEvent, ImportJob

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "StudentProfile",
    "UserRole",
    "Quiz",
    "QuizVersion",
    "QuizStatus",
    "MultiAnswerPolicy",
    "Question",
    "QuestionOption",
    "QuestionType",
    "QuestionDifficulty",
    "QuizAssignment",
    "QuizAttempt",
    "AttemptAnswer",
    "AttemptTelemetryEvent",
    "AttemptStatus",
    "GradingStatus",
    "GradeAdjustment",
    "AuditEvent",
    "ImportJob",
]
