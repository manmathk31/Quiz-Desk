"""Teacher Assessment Results, Grading Review, Score Adjustments, and Release Endpoints (DEC-010, Phase 7)."""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_faculty
from app.core.database import get_db
from app.models.attempt import AttemptStatus
from app.models.user import User
from app.schemas.results import (
    QuizResultSummaryResponse,
    AttemptListResponse,
    AttemptDetailResponse,
    GradeAdjustmentRequest,
    ReleaseResultsResponse,
)
from app.services.results_service import (
    get_quiz_result_summary,
    get_quiz_attempts_paginated,
    get_attempt_detail_for_teacher,
    adjust_attempt_grade,
    release_quiz_results,
    export_quiz_results_csv,
)

router = APIRouter(prefix="/quizzes", tags=["Teacher Assessment Results & Grading"])


@router.get("/{quiz_id}/results/summary", response_model=QuizResultSummaryResponse)
def get_quiz_summary_endpoint(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Retrieve assessment summary metrics: total enrollment, participation, average/high/low score,
    and current student result release status.
    Strictly verifies teacher ownership of the quiz.
    """
    return get_quiz_result_summary(db, quiz_id, current_user)


@router.get("/{quiz_id}/results/attempts", response_model=AttemptListResponse)
def get_quiz_attempts_endpoint(
    quiz_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[AttemptStatus] = Query(None, description="Filter by attempt lifecycle status"),
    search: Optional[str] = Query(None, description="Search across student PRN, name, or email"),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated attempt summaries for an owned assessment.
    Supports filtering by attempt status and text search across student identifiers.
    """
    return get_quiz_attempts_paginated(
        db=db,
        quiz_id=quiz_id,
        teacher_user=current_user,
        page=page,
        limit=limit,
        status_filter=status,
        search=search,
    )


@router.get("/{quiz_id}/results/attempts/{attempt_id}", response_model=AttemptDetailResponse)
def get_attempt_detail_endpoint(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Retrieve full attempt diagnostic view: question-level responses, answer keys,
    awarded marks, telemetry log, and score adjustment history.
    """
    return get_attempt_detail_for_teacher(db, quiz_id, attempt_id, current_user)


@router.post("/{quiz_id}/results/attempts/{attempt_id}/adjust", response_model=AttemptDetailResponse)
def adjust_attempt_score_endpoint(
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    payload: GradeAdjustmentRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Perform an authoritative manual score adjustment for a finalized attempt (DEC-010).
    - Requires mandatory non-empty reason for immutable audit trail.
    - Validates score within range [0, total_possible_marks].
    - Preserves previous score and full adjustment history.
    """
    return adjust_attempt_grade(db, quiz_id, attempt_id, payload, current_user)


@router.post("/{quiz_id}/results/release", response_model=ReleaseResultsResponse)
def release_quiz_results_endpoint(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Explicitly release assessment scores to assigned students (DEC-010).
    Idempotent: safe to retry without corrupting state or generating redundant audit entries.
    """
    return release_quiz_results(db, quiz_id, current_user)


@router.get("/{quiz_id}/results/export")
def export_quiz_results_endpoint(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Export assessment attempts to CSV with formula-injection protection (DEC-013).
    Includes PRN, Name, Email, Division, Attempt #, Status, Timestamps, and Scores.
    """
    csv_data = export_quiz_results_csv(db, quiz_id, current_user)
    filename = f"quiz_{quiz_id}_results.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
