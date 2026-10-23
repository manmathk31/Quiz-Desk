"""Student assessment inquiry and eligibility endpoints (DEC-005, DEC-007, Phase 5)."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_student
from app.models.user import User
from app.services.eligibility import check_student_quiz_eligibility
from app.schemas.roster import StudentEligibilityResponse

router = APIRouter(prefix="/student/quizzes", tags=["Student Assessments"])


@router.get("/{id}/eligibility", response_model=StudentEligibilityResponse)
def check_assessment_eligibility(
    id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Inquire assessment eligibility for authenticated student.
    Authoritative server-side verification:
    - User is active student.
    - Assessment is published.
    - Student is assigned and assignment is active.
    - Identity matches (email and PRN alignment).
    - Checks schedule window (opens_at <= now <= closes_at).
    Does NOT leak questions, options, or answer keys.
    """
    res = check_student_quiz_eligibility(db, id, current_user)

    return StudentEligibilityResponse(
        is_eligible=res.is_eligible,
        quiz_id=res.quiz_id,
        quiz_title=res.quiz_title,
        course_code=res.course_code,
        quiz_version_id=res.quiz_version_id,
        version_number=res.version_number,
        assignment_id=res.assignment_id,
        student_prn=res.student_prn,
        student_name=res.student_name,
        student_email=res.student_email,
        division=res.division,
        opens_at=res.opens_at,
        closes_at=res.closes_at,
        duration_minutes=res.duration_minutes,
        max_attempts=res.max_attempts,
        is_open=res.is_open,
        status_message=res.status_message,
    )
