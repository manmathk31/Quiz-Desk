"""Teacher Student Roster and Quiz Assignment API Endpoints (DEC-007, DEC-014, Phase 5)."""
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_active_user, require_faculty
from app.models.user import User, StudentProfile, UserRole
from app.models.quiz import Quiz, QuizVersion
from app.models.roster import QuizAssignment
from app.models.attempt import QuizAttempt
from app.models.audit import AuditEvent
from app.services.roster_parser import (
    parse_and_validate_roster_file,
    generate_roster_csv_template,
    generate_roster_xlsx_template,
    ParsedRosterRow,
    MAX_ROSTER_FILE_SIZE_BYTES,
)
from app.services.roster_service import (
    evaluate_roster_candidates,
    commit_roster_import,
)
from app.schemas.roster import (
    RosterPreviewResponse,
    RosterPreviewItemResponse,
    RosterRowErrorResponse,
    RosterImportSummaryResponse,
    AssignmentResponse,
    AssignmentListResponse,
    AssignmentSummaryStats,
    AssignmentCreateRequest,
    AssignmentStatusUpdateRequest,
)

router = APIRouter(prefix="/quizzes", tags=["Quiz Rosters & Assignments"])


def _get_teacher_quiz_or_404(db: Session, quiz_id: uuid.UUID, current_user: User) -> Quiz:
    """Ensure quiz exists and is owned by the authenticated teacher."""
    stmt = select(Quiz).where(
        Quiz.id == quiz_id,
        Quiz.is_archived == False,
    )
    quiz = db.scalar(stmt)
    if not quiz or (current_user.role != UserRole.ADMIN and quiz.created_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access restricted.",
        )
    return quiz


@router.get("/{id}/roster/template")
def download_roster_template(
    id: uuid.UUID,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """Download standard sample student roster template in CSV or XLSX format."""
    _get_teacher_quiz_or_404(db, id, current_user)

    if format == "xlsx":
        content = generate_roster_xlsx_template()
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=student_roster_template.xlsx"},
        )
    else:
        content = generate_roster_csv_template()
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=student_roster_template.csv"},
        )


@router.post("/{id}/roster/preview", response_model=RosterPreviewResponse)
async def preview_roster_upload(
    id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Dry-run preview of student roster CSV/XLSX spreadsheet.
    Evaluates headers, row syntax, duplicate identities, and database matching.
    Guarantees ZERO database mutations.
    """
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    content = await file.read()
    if len(content) > MAX_ROSTER_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_ROSTER_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    # Parse and validate file format
    val_result = parse_and_validate_roster_file(content, filename=file.filename)

    if not val_result.is_valid:
        error_items = [
            RosterRowErrorResponse(row_number=e.row_number, column=e.column, message=e.message)
            for e in val_result.errors
        ]
        return RosterPreviewResponse(
            total_rows=val_result.total_rows,
            valid_rows=val_result.valid_rows,
            new_assignments_count=0,
            already_assigned_count=0,
            conflicts_count=len(error_items),
            matched_count=0,
            unregistered_count=0,
            pending_profile_count=0,
            can_confirm=False,
            items=[],
            errors=error_items,
        )

    # Evaluate against database state
    eval_result = evaluate_roster_candidates(db, quiz.id, val_result.rows)

    item_responses = [
        RosterPreviewItemResponse(
            row_number=item.row_number,
            prn=item.prn,
            name=item.name,
            email=item.email,
            division=item.division,
            assignment_status=item.assignment_status,
            match_status=item.match_status,
            matched_user_id=item.matched_user_id,
            conflict_reason=item.conflict_reason,
            is_currently_active=item.is_currently_active,
        )
        for item in eval_result.items
    ]

    error_responses = [
        RosterRowErrorResponse(row_number=e.row_number, column=e.column, message=e.message)
        for e in val_result.errors
    ]

    return RosterPreviewResponse(
        total_rows=eval_result.total_rows,
        valid_rows=len(item_responses),
        new_assignments_count=eval_result.new_assignments_count,
        already_assigned_count=eval_result.already_assigned_count,
        conflicts_count=eval_result.conflicts_count,
        matched_count=eval_result.matched_count,
        unregistered_count=eval_result.unregistered_count,
        pending_profile_count=eval_result.pending_profile_count,
        can_confirm=eval_result.can_confirm,
        items=item_responses,
        errors=error_responses,
    )


@router.post("/{id}/roster/import", response_model=RosterImportSummaryResponse)
async def confirm_roster_upload(
    id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Idempotent transactional roster import.
    Re-validates file and re-evaluates database state inside transaction.
    Rejects with HTTP 422 if any unresolved conflicts exist.
    """
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    content = await file.read()
    if len(content) > MAX_ROSTER_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_ROSTER_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    val_result = parse_and_validate_roster_file(content, filename=file.filename)
    if not val_result.is_valid:
        error_msgs = [f"Row {e.row_number}: {e.message}" for e in val_result.errors]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Spreadsheet validation failed.", "errors": error_msgs[:20]},
        )

    summary = commit_roster_import(db, quiz, current_user.id, val_result.rows)

    return RosterImportSummaryResponse(
        imported_count=summary["imported_count"],
        already_assigned_count=summary["already_assigned_count"],
        matched_accounts_count=summary["matched_accounts_count"],
        unregistered_count=summary["unregistered_count"],
        message=(
            f"Successfully imported roster: {summary['imported_count']} new student(s) assigned, "
            f"{summary['already_assigned_count']} updated, {summary['matched_accounts_count']} matched to registered accounts."
        ),
    )


@router.get("/{id}/assignments", response_model=AssignmentListResponse)
def list_quiz_assignments(
    id: uuid.UUID,
    search: Optional[str] = Query(None, description="Search by PRN, name, or email"),
    division: Optional[str] = Query(None, description="Filter by class division"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """List and filter assigned students for a quiz with roster summary metrics."""
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    # Base query for this quiz
    base_query = select(QuizAssignment).where(QuizAssignment.quiz_id == quiz.id)

    if division:
        base_query = base_query.where(QuizAssignment.division == division.strip())
    if is_active is not None:
        base_query = base_query.where(QuizAssignment.is_active == is_active)
    if search:
        term = f"%{search.strip()}%"
        base_query = base_query.where(
            or_(
                QuizAssignment.student_prn.ilike(term),
                QuizAssignment.student_name.ilike(term),
                QuizAssignment.student_email.ilike(term),
            )
        )

    # Total matching count
    total_count = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

    # Pagination
    paginated_query = (
        base_query.order_by(QuizAssignment.division, QuizAssignment.student_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    assignments = db.scalars(paginated_query).all()

    # Collect attempts for assigned students in this quiz
    assigned_user_ids = [a.assigned_student_id for a in assignments if a.assigned_student_id]
    attempt_user_ids: Set[uuid.UUID] = set()
    if assigned_user_ids:
        attempt_stmt = (
            select(QuizAttempt.student_id)
            .join(QuizVersion, QuizAttempt.quiz_version_id == QuizVersion.id)
            .where(
                QuizVersion.quiz_id == quiz.id,
                QuizAttempt.student_id.in_(assigned_user_ids),
            )
            .distinct()
        )
        attempt_user_ids = set(db.scalars(attempt_stmt).all())

    items = [
        AssignmentResponse(
            id=a.id,
            quiz_id=a.quiz_id,
            student_prn=a.student_prn,
            student_name=a.student_name,
            student_email=a.student_email,
            division=a.division,
            assigned_student_id=a.assigned_student_id,
            is_active=a.is_active,
            created_at=a.created_at,
            revoked_at=a.revoked_at,
            match_status="matched" if a.assigned_student_id else "unregistered",
            has_attempts=(a.assigned_student_id in attempt_user_ids) if a.assigned_student_id else False,
        )
        for a in assignments
    ]

    # Calculate overall summary counts for this quiz
    all_assignments = db.scalars(select(QuizAssignment).where(QuizAssignment.quiz_id == quiz.id)).all()
    divisions = sorted(list({a.division for a in all_assignments if a.division}))
    active_cnt = sum(1 for a in all_assignments if a.is_active)
    revoked_cnt = sum(1 for a in all_assignments if not a.is_active)
    matched_cnt = sum(1 for a in all_assignments if a.assigned_student_id)
    unregistered_cnt = sum(1 for a in all_assignments if not a.assigned_student_id)

    summary_stats = AssignmentSummaryStats(
        total_assigned=len(all_assignments),
        active_count=active_cnt,
        revoked_count=revoked_cnt,
        matched_count=matched_cnt,
        unregistered_count=unregistered_cnt,
        divisions=divisions,
    )

    return AssignmentListResponse(
        items=items,
        total_count=total_count,
        page=page,
        page_size=page_size,
        summary=summary_stats,
    )


@router.post("/{id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def add_single_student_assignment(
    id: uuid.UUID,
    payload: AssignmentCreateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """Manually assign a single student to a quiz following identity matching rules."""
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    parsed_row = ParsedRosterRow(
        row_number=1,
        prn=payload.prn,
        name=payload.name,
        email=str(payload.email).lower(),
        division=payload.division,
    )

    eval_result = evaluate_roster_candidates(db, quiz.id, [parsed_row])
    evaluated = eval_result.items[0]

    if evaluated.assignment_status == "already_assigned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with PRN '{payload.prn}' or email '{payload.email}' is already assigned to this quiz.",
        )
    if evaluated.conflict_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=evaluated.conflict_reason,
        )

    assignment = QuizAssignment(
        quiz_id=quiz.id,
        student_prn=evaluated.prn,
        student_email=evaluated.email,
        student_name=evaluated.name,
        division=evaluated.division,
        assigned_student_id=evaluated.matched_user_id,
        is_active=True,
    )
    db.add(assignment)

    # Record AuditEvent
    audit = AuditEvent(
        user_id=current_user.id,
        action="assignment_created",
        entity_type="quiz",
        entity_id=str(quiz.id),
        details={"student_prn": payload.prn, "student_email": payload.email, "division": payload.division},
    )
    db.add(audit)
    db.commit()
    db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        quiz_id=assignment.quiz_id,
        student_prn=assignment.student_prn,
        student_name=assignment.student_name,
        student_email=assignment.student_email,
        division=assignment.division,
        assigned_student_id=assignment.assigned_student_id,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
        revoked_at=assignment.revoked_at,
        match_status="matched" if assignment.assigned_student_id else "unregistered",
        has_attempts=False,
    )


@router.patch("/{id}/assignments/{assignment_id}/status", response_model=AssignmentResponse)
def update_assignment_status(
    id: uuid.UUID,
    assignment_id: uuid.UUID,
    payload: AssignmentStatusUpdateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """Revoke or reactivate a student's quiz eligibility."""
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    assignment = db.get(QuizAssignment, assignment_id)
    if not assignment or assignment.quiz_id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment record not found for this quiz.",
        )

    action = "assignment_reactivated" if payload.is_active else "assignment_revoked"
    assignment.is_active = payload.is_active
    if not payload.is_active:
        assignment.revoked_at = datetime.now(timezone.utc)
        assignment.revoked_by_id = current_user.id
    else:
        assignment.revoked_at = None
        assignment.revoked_by_id = None

    audit = AuditEvent(
        user_id=current_user.id,
        action=action,
        entity_type="quiz_assignment",
        entity_id=str(assignment.id),
        details={"quiz_id": str(quiz.id), "student_prn": assignment.student_prn, "is_active": assignment.is_active},
    )
    db.add(audit)
    db.commit()
    db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        quiz_id=assignment.quiz_id,
        student_prn=assignment.student_prn,
        student_name=assignment.student_name,
        student_email=assignment.student_email,
        division=assignment.division,
        assigned_student_id=assignment.assigned_student_id,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
        revoked_at=assignment.revoked_at,
        match_status="matched" if assignment.assigned_student_id else "unregistered",
        has_attempts=False,
    )


@router.delete("/{id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """
    Remove an assignment from a quiz roster.
    Rejects removal if student has already started or completed attempts on this quiz.
    """
    quiz = _get_teacher_quiz_or_404(db, id, current_user)

    assignment = db.get(QuizAssignment, assignment_id)
    if not assignment or assignment.quiz_id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment record not found for this quiz.",
        )

    # Check for existing attempts
    if assignment.assigned_student_id:
        has_attempts = db.scalar(
            select(func.count(QuizAttempt.id))
            .join(QuizVersion, QuizAttempt.quiz_version_id == QuizVersion.id)
            .where(
                QuizVersion.quiz_id == quiz.id,
                QuizAttempt.student_id == assignment.assigned_student_id,
            )
        )
        if has_attempts and has_attempts > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete assignment: Student has existing assessment attempts. Revoke assignment instead to preserve audit history.",
            )

    audit = AuditEvent(
        user_id=current_user.id,
        action="assignment_deleted",
        entity_type="quiz_assignment",
        entity_id=str(assignment.id),
        details={"quiz_id": str(quiz.id), "student_prn": assignment.student_prn},
    )
    db.add(audit)
    db.delete(assignment)
    db.commit()
    return None
