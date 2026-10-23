"""Student assessment inquiry, delivery, autosave, telemetry, and submission endpoints (DEC-008, DEC-009, DEC-010, Phase 6)."""
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_student
from app.models.user import User
from app.services.eligibility import check_student_quiz_eligibility
from app.services.assessment_service import (
    list_student_quizzes,
    get_assessment_readiness,
    start_or_resume_attempt,
    get_attempt_content,
    save_attempt_answer,
    record_telemetry_event,
    finalize_and_grade_attempt,
)
from app.schemas.roster import StudentEligibilityResponse
from app.schemas.assessment import (
    StudentQuizSummary,
    StudentQuizListResponse,
    AttemptStartResponse,
    AttemptContentResponse,
    AssessmentReadinessResponse,
    AnswerSaveRequest,
    AnswerSaveResponse,
    TelemetryEventRequest,
    TelemetryEventResponse,
    AttemptSubmissionResponse,
)
from app.schemas.results import StudentAttemptResultResponse

router = APIRouter(prefix="/student", tags=["Student Assessments"])


@router.get("/quizzes", response_model=StudentQuizListResponse)
def get_student_assigned_quizzes(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    List all assessments assigned to authenticated student.
    Returns real-time availability status, schedule windows, and active attempt indicator.
    """
    items = list_student_quizzes(db, current_user)
    return StudentQuizListResponse(items=items, total=len(items))


@router.get("/quizzes/{id}/eligibility", response_model=StudentEligibilityResponse)
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


@router.get("/quizzes/{id}/readiness", response_model=AssessmentReadinessResponse)
def get_quiz_assessment_readiness(
    id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Inquire assessment instructions, browser readiness requirements, and effective proctoring rules (DEC-021).
    - Checks candidate eligibility and schedule.
    - Provides full transparency on proctoring policy and penalty formulas before attempt starts.
    """
    return get_assessment_readiness(db, id, current_user)


@router.post("/quizzes/{id}/attempts", response_model=AttemptStartResponse, status_code=status.HTTP_201_CREATED)
def start_or_resume_assessment_attempt(
    id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Start a new assessment attempt or resume an active in-progress attempt.
    - Resumes without resetting timer if an active attempt exists.
    - Enforces max attempt limits and schedule window.
    - Authoritative deadline calculation: min(now + duration, closes_at).
    - Persists stable randomized question/option sequence for this session.
    """
    return start_or_resume_attempt(db, id, current_user)


@router.get("/attempts/{attempt_id}", response_model=AttemptContentResponse)
def get_assessment_attempt_content(
    attempt_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Fetch sanitized question set and current student answer state for an attempt.
    - Verified against caller student identity.
    - Sanitized payload: no answer keys, no is_correct fields.
    - Returns stored randomized question & option sequences.
    - Checks deadline: lazily finalizes attempt as EXPIRED if time has elapsed.
    """
    return get_attempt_content(db, attempt_id, current_user)


@router.put("/attempts/{attempt_id}/answers/{question_id}", response_model=AnswerSaveResponse)
def autosave_question_answer(
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AnswerSaveRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Autosave an answer for a specific question during an active attempt.
    - Rejects writes if attempt is finalized or deadline has expired (409 Conflict).
    - Validates options belong strictly to the question and version.
    - Rejects out-of-order stale saves using monotonic client timestamp check.
    - Targeted database operation.
    """
    return save_attempt_answer(db, attempt_id, question_id, payload, current_user)


@router.post("/attempts/{attempt_id}/telemetry", response_model=TelemetryEventResponse)
def report_assessment_telemetry(
    attempt_id: uuid.UUID,
    payload: TelemetryEventRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Record proctoring telemetry (tab switch or window blur event).
    - Increments attempt tab_switch_count.
    - Returns warning threshold status.
    """
    return record_telemetry_event(db, attempt_id, payload, current_user)


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptSubmissionResponse)
def submit_assessment_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Finalize and submit an assessment attempt.
    - Idempotent: repeated calls return consistent final state without re-grading.
    - Evaluates positive marks, negative marks, and multi-answer scoring policies.
    - Applies tab switch deductions if configured.
    - Results held withheld until teacher explicitly releases them.
    """
    from app.models.attempt import QuizAttempt
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.student_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found.",
        )

    return finalize_and_grade_attempt(db, attempt, is_expired=False)


@router.get("/attempts/{attempt_id}/result", response_model=StudentAttemptResultResponse)
def get_student_attempt_result_endpoint(
    attempt_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Retrieve authoritative personal score for a student after instructor release (DEC-010).
    - Caller must own the attempt.
    - Results withheld until released by course instructor (returns HTTP 403).
    - Protects correct answer keys and class-wide score distributions.
    """
    from app.services.results_service import get_student_attempt_result
    return get_student_attempt_result(db, attempt_id, current_user)
