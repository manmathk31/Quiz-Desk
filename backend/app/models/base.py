"""Base declarative class and mixins for SQLAlchemy 2.x models."""
from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base class for all Quizdesk database models."""
    pass


class TimestampMixin:
    """Standard timestamp mixin with timezone-aware UTC datetime."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """UUID primary key mixin."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
