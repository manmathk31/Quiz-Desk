"""Student Quiz Eligibility verification service (DEC-005, DEC-007, Phase 5)."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.quiz import Quiz, QuizVersion
from app.models.roster import QuizAssignment
from app.models.user import User, UserRole


@dataclass
class StudentEligibilityResult:
    """Sanitized student eligibility assessment outcome."""
    is_eligible: bool
    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    quiz_version_id: uuid.UUID
    version_number: int
    assignment_id: uuid.UUID
    student_prn: str
    student_name: str
    student_email: str
    division: str
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    max_attempts: int
    is_open: bool
    status_message: str


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has UTC timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def check_student_quiz_eligibility(
    db: Session,
    quiz_id: uuid.UUID,
    student_user: User,
) -> StudentEligibilityResult:
    """
    Authoritative server-side student eligibility gate.
    Verifies:
    1. Caller is an active student.
    2. Target quiz exists, is not archived, and has a published version.
    3. Student is assigned to this quiz via an active QuizAssignment.
    4. Student identity is verified (email and PRN alignment).
    5. Returns sanitized eligibility metadata without leaking questions or answer keys.
    """
    if student_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only student accounts can check student assessment eligibility.",
        )

    if not student_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact institutional administrator.",
        )

    # Ensure student_user has profile loaded if not already in session
    if student_user.student_profile is None:
        fresh_user = db.scalar(
            select(User).options(joinedload(User.student_profile)).where(User.id == student_user.id)
        )
        if fresh_user:
            student_user = fresh_user

    # 1. Look up Quiz with published versions eager-loaded
    quiz = db.scalar(
        select(Quiz).options(joinedload(Quiz.versions)).where(Quiz.id == quiz_id)
    )
    if not quiz or quiz.is_archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or is no longer available.",
        )

    # 2. Find published version
    published_versions = [v for v in quiz.versions if v.is_published]
    if not published_versions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assessment is not currently published.",
        )
    # Use latest published version snapshot
    version: QuizVersion = published_versions[-1]

    # 3. Look up QuizAssignment (combined check: assigned ID or matching email)
    assignment_stmt = (
        select(QuizAssignment)
        .where(
            QuizAssignment.quiz_id == quiz.id,
            (QuizAssignment.assigned_student_id == student_user.id)
            | (QuizAssignment.student_email == student_user.email.lower()),
        )
        .order_by((QuizAssignment.assigned_student_id == student_user.id).desc())
    )
    assignment = db.scalar(assignment_stmt)

    if assignment and assignment.assigned_student_id is None:
            # Verify PRN alignment before binding
            if student_user.student_profile and student_user.student_profile.prn:
                if student_user.student_profile.prn.upper() == assignment.student_prn.upper():
                    # Safely bind student account to assignment
                    assignment.assigned_student_id = student_user.id
                    db.commit()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Identity conflict: Your registered student PRN "
                            f"('{student_user.student_profile.prn}') does not match the "
                            f"assigned roster PRN ('{assignment.student_prn}') for this assessment."
                        ),
                    )
            else:
                # Registered student has not completed PRN profile setup
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student profile incomplete: A registered PRN is required to take assigned assessments.",
                )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this assessment. Contact your course instructor.",
        )

    # 4. Check assignment active status
    if not assignment.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your assignment eligibility for this assessment has been revoked by the instructor.",
        )

    # 5. Check schedule window
    now = datetime.now(timezone.utc)
    opens_at = ensure_utc(version.opens_at)
    closes_at = ensure_utc(version.closes_at)

    if opens_at and now < opens_at:
        is_open = False
        status_message = f"Assessment scheduled to open on {opens_at.strftime('%Y-%m-%d %H:%M UTC')}."
    elif closes_at and now > closes_at:
        is_open = False
        status_message = "Assessment availability window has closed."
    else:
        is_open = True
        status_message = "Assessment is currently open."

    return StudentEligibilityResult(
        is_eligible=True,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        course_code=quiz.course_code,
        quiz_version_id=version.id,
        version_number=version.version_number,
        assignment_id=assignment.id,
        student_prn=assignment.student_prn,
        student_name=assignment.student_name,
        student_email=assignment.student_email,
        division=assignment.division,
        opens_at=opens_at,
        closes_at=closes_at,
        duration_minutes=version.duration_minutes,
        max_attempts=version.max_attempts,
        is_open=is_open,
        status_message=status_message,
    )
