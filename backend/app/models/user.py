"""User and student profile relational models (DEC-005)."""
import enum
import uuid
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.quiz import Quiz, QuizVersion
    from app.models.attempt import QuizAttempt
    from app.models.audit import GradeAdjustment, AuditEvent, ImportJob


class UserRole(str, enum.Enum):
    """System-level access roles."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Application user profile.
    ID corresponds directly to the Supabase Auth user UUID.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        nullable=False,
        default=UserRole.STUDENT,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    created_quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz",
        back_populates="creator",
        foreign_keys="Quiz.created_by_id",
    )
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="student",
    )

    @property
    def prn(self) -> Optional[str]:
        return self.student_profile.prn if self.student_profile else None

    @property
    def current_division(self) -> Optional[str]:
        return self.student_profile.current_division if self.student_profile else None

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Academic student profile linking user to Permanent Registration Number (PRN).
    PRN is strictly an institutional identifier, never a credential (DEC-005).
    """
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    prn: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    current_division: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="student_profile")

    def __repr__(self) -> str:
        return f"<StudentProfile prn={self.prn} division={self.current_division}>"
