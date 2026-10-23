"""Teacher assessment evaluation, grading adjustments, result release, and CSV export service (DEC-010, Phase 7)."""
import csv
from datetime import datetime, timezone
import io
import math
import uuid
from typing import List, Optional, Dict, Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.attempt import (
    QuizAttempt,
    AttemptAnswer,
    AttemptTelemetryEvent,
    AttemptStatus,
    GradingStatus,
)
from app.models.audit import GradeAdjustment, AuditEvent
from app.models.question import Question, QuestionOption
from app.models.quiz import Quiz, QuizVersion
from app.models.roster import QuizAssignment
from app.models.user import User, StudentProfile, UserRole
from app.schemas.results import (
    QuizResultSummaryResponse,
    AttemptListItemResponse,
    AttemptListResponse,
    QuestionOptionResultDetail,
    QuestionResultDetail,
    GradeAdjustmentItem,
    TelemetryEventItem,
    AttemptDetailResponse,
    GradeAdjustmentRequest,
    ReleaseResultsResponse,
    StudentAttemptResultResponse,
)
from app.services.eligibility import ensure_utc


def _get_teacher_quiz_or_404(db: Session, quiz_id: uuid.UUID, teacher_user: User) -> Quiz:
    """Ensure quiz exists and belongs to the authenticated teacher (DEC-017)."""
    quiz = db.scalar(
        select(Quiz)
        .options(joinedload(Quiz.versions).joinedload(QuizVersion.questions))
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == teacher_user.id,
            Quiz.is_archived == False,
        )
    )
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or access denied.",
        )
    return quiz


def get_quiz_result_summary(
    db: Session,
    quiz_id: uuid.UUID,
    teacher_user: User,
) -> QuizResultSummaryResponse:
    """
    Retrieve aggregate score distributions, attempt counts, and result release status.
    Uses server-side calculations and bounded queries.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)

    published_versions = [v for v in quiz.versions if v.is_published]
    active_version = published_versions[-1] if published_versions else (quiz.versions[-1] if quiz.versions else None)

    if not active_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment version definition not found.",
        )

    # 1. Total active assignments (enrolled students)
    total_enrolled = db.scalar(
        select(func.count(QuizAssignment.id)).where(
            QuizAssignment.quiz_id == quiz.id,
            QuizAssignment.is_active == True,
        )
    ) or 0

    # 2. Total attempts across versions of this quiz
    version_ids = [v.id for v in quiz.versions]
    attempts_stmt = select(QuizAttempt).where(QuizAttempt.quiz_version_id.in_(version_ids))
    attempts = db.scalars(attempts_stmt).all()

    total_attempts = len(attempts)
    submitted_attempts = [a for a in attempts if a.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED)]
    submitted_count = len(submitted_attempts)
    in_progress_count = sum(1 for a in attempts if a.status == AttemptStatus.IN_PROGRESS)

    scores = [float(a.total_score) for a in submitted_attempts if a.total_score is not None]
    average_score = round(sum(scores) / len(scores), 2) if scores else None
    highest_score = max(scores) if scores else None
    lowest_score = min(scores) if scores else None

    # Total possible marks
    total_possible_marks = sum(float(q.positive_marks) for q in (active_version.questions or []))

    return QuizResultSummaryResponse(
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        course_code=quiz.course_code,
        version_number=active_version.version_number,
        is_published=active_version.is_published,
        is_results_released=active_version.is_results_released,
        results_released_at=ensure_utc(active_version.results_released_at),
        total_enrolled=total_enrolled,
        total_attempts=total_attempts,
        submitted_count=submitted_count,
        in_progress_count=in_progress_count,
        average_score=average_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        total_possible_marks=round(total_possible_marks, 2),
    )


def get_quiz_attempts_paginated(
    db: Session,
    quiz_id: uuid.UUID,
    teacher_user: User,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[AttemptStatus] = None,
    search: Optional[str] = None,
) -> AttemptListResponse:
    """
    Retrieve paginated attempt summaries for an owned quiz with bounded queries.
    Supports filtering by status and searching across PRN, name, and email.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)
    version_ids = [v.id for v in quiz.versions]

    bounded_limit = min(max(1, limit), 100)
    page_num = max(1, page)
    offset = (page_num - 1) * bounded_limit

    # Fetch assignments for this quiz to resolve student details if user has no student profile yet
    assignments = db.scalars(
        select(QuizAssignment).where(QuizAssignment.quiz_id == quiz.id)
    ).all()
    assign_by_user_id = {a.assigned_student_id: a for a in assignments if a.assigned_student_id}
    assign_by_email = {a.student_email.lower(): a for a in assignments}

    base_query = (
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.student).joinedload(User.student_profile),
            selectinload(QuizAttempt.grade_adjustments),
        )
        .where(QuizAttempt.quiz_version_id.in_(version_ids))
    )

    if status_filter:
        base_query = base_query.where(QuizAttempt.status == status_filter)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        # Search against User name, email, PRN from StudentProfile or QuizAssignment
        base_query = base_query.join(QuizAttempt.student).outerjoin(User.student_profile).where(
            or_(
                func.lower(User.name).like(term),
                func.lower(User.email).like(term),
                func.lower(StudentProfile.prn).like(term),
            )
        )

    # Total count query
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = db.scalar(count_stmt) or 0

    # Paginated attempts
    items_stmt = (
        base_query
        .order_by(QuizAttempt.started_at.desc(), QuizAttempt.created_at.desc())
        .offset(offset)
        .limit(bounded_limit)
    )
    attempts = db.scalars(items_stmt).all()

    items: List[AttemptListItemResponse] = []
    for att in attempts:
        student = att.student
        profile = student.student_profile if student else None
        assignment = assign_by_user_id.get(student.id) or (assign_by_email.get(student.email.lower()) if student else None)

        student_name = student.name if student else (assignment.student_name if assignment else "Unknown")
        student_email = student.email if student else (assignment.student_email if assignment else "N/A")
        student_prn = profile.prn if profile else (assignment.student_prn if assignment else "N/A")
        student_division = profile.current_division if profile and profile.current_division else (assignment.division if assignment else "N/A")

        items.append(
            AttemptListItemResponse(
                attempt_id=att.id,
                student_id=att.student_id,
                student_name=student_name,
                student_email=student_email,
                student_prn=student_prn,
                student_division=student_division,
                attempt_number=att.attempt_number,
                status=att.status.value,
                started_at=ensure_utc(att.started_at),
                submitted_at=ensure_utc(att.submitted_at),
                total_score=float(att.total_score) if att.total_score is not None else None,
                grading_status=att.grading_status.value,
                tab_switch_count=att.tab_switch_count,
                is_finalized=att.is_finalized,
                adjustment_count=len(att.grade_adjustments),
            )
        )

    total_pages = math.ceil(total / bounded_limit) if total > 0 else 1

    return AttemptListResponse(
        items=items,
        total=total,
        page=page_num,
        limit=bounded_limit,
        total_pages=total_pages,
    )


def get_attempt_detail_for_teacher(
    db: Session,
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    teacher_user: User,
) -> AttemptDetailResponse:
    """
    Retrieve full attempt diagnostic view for an authorized teacher.
    Includes question-level student selections, answer keys, awarded marks, telemetry, and adjustments.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)

    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.student).joinedload(User.student_profile),
            joinedload(QuizAttempt.quiz_version).joinedload(QuizVersion.questions).joinedload(Question.options),
            joinedload(QuizAttempt.answers),
            joinedload(QuizAttempt.telemetry_events),
            joinedload(QuizAttempt.grade_adjustments).joinedload(GradeAdjustment.adjusted_by),
        )
        .where(QuizAttempt.id == attempt_id)
    )

    if not attempt or attempt.quiz_version.quiz_id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found for this quiz.",
        )

    student = attempt.student
    profile = student.student_profile if student else None

    # Lookup assignment
    assignment = db.scalar(
        select(QuizAssignment).where(
            QuizAssignment.quiz_id == quiz.id,
            (QuizAssignment.assigned_student_id == student.id)
            | (QuizAssignment.student_email == student.email.lower()),
        )
    )

    student_name = student.name if student else (assignment.student_name if assignment else "Unknown")
    student_email = student.email if student else (assignment.student_email if assignment else "N/A")
    student_prn = profile.prn if profile else (assignment.student_prn if assignment else "N/A")
    student_division = profile.current_division if profile and profile.current_division else (assignment.division if assignment else "N/A")

    # Map answers
    ans_map = {str(a.question_id): a for a in attempt.answers}

    # Questions and option ordering
    version = attempt.quiz_version
    questions = sorted(version.questions, key=lambda q: q.order_index)

    question_details: List[QuestionResultDetail] = []
    max_marks = 0.0

    for q in questions:
        max_marks += float(q.positive_marks)
        ans = ans_map.get(str(q.id))
        selected_ids = list(ans.selected_option_ids or []) if ans else []
        awarded = float(ans.awarded_marks) if (ans and ans.awarded_marks is not None) else None

        opts = sorted(q.options, key=lambda o: o.order_index)
        opt_details = [
            QuestionOptionResultDetail(
                id=o.id,
                option_text=o.option_text,
                order_index=o.order_index,
                is_correct=o.is_correct,
            )
            for o in opts
        ]

        question_details.append(
            QuestionResultDetail(
                question_id=q.id,
                prompt=q.prompt,
                question_type=q.question_type.value,
                order_index=q.order_index,
                positive_marks=float(q.positive_marks),
                negative_marks=float(q.negative_marks),
                awarded_marks=awarded,
                selected_option_ids=selected_ids,
                options=opt_details,
            )
        )

    # Adjustments
    adjustments: List[GradeAdjustmentItem] = [
        GradeAdjustmentItem(
            id=adj.id,
            previous_score=float(adj.previous_score),
            new_score=float(adj.new_score),
            reason=adj.reason,
            adjusted_by_name=adj.adjusted_by.name if adj.adjusted_by else "Instructor",
            created_at=ensure_utc(adj.created_at),
        )
        for adj in sorted(attempt.grade_adjustments, key=lambda a: a.created_at, reverse=True)
    ]

    # Telemetry events
    telemetry_events: List[TelemetryEventItem] = [
        TelemetryEventItem(
            id=t.id,
            event_type=t.event_type,
            event_timestamp=ensure_utc(t.event_timestamp),
            event_data=t.event_data,
        )
        for t in sorted(attempt.telemetry_events, key=lambda t: t.event_timestamp)
    ]

    return AttemptDetailResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        course_code=quiz.course_code,
        version_number=version.version_number,
        student_name=student_name,
        student_email=student_email,
        student_prn=student_prn,
        student_division=student_division,
        attempt_number=attempt.attempt_number,
        status=attempt.status.value,
        started_at=ensure_utc(attempt.started_at),
        submitted_at=ensure_utc(attempt.submitted_at),
        deadline_at=ensure_utc(attempt.deadline_at),
        total_score=float(attempt.total_score) if attempt.total_score is not None else None,
        max_possible_marks=round(max_marks, 2),
        grading_status=attempt.grading_status.value,
        tab_switch_count=attempt.tab_switch_count,
        is_finalized=attempt.is_finalized,
        questions=question_details,
        adjustments=adjustments,
        telemetry_events=telemetry_events,
    )


def adjust_attempt_grade(
    db: Session,
    quiz_id: uuid.UUID,
    attempt_id: uuid.UUID,
    payload: GradeAdjustmentRequest,
    teacher_user: User,
) -> AttemptDetailResponse:
    """
    Perform an authoritative manual score adjustment with mandatory audit logging (DEC-010).
    - Preserves previous score in GradeAdjustment audit table.
    - Rejects in-progress attempts.
    - Rejects scores outside the valid range [0, max_possible_marks].
    - Safe to retry.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)

    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.quiz_version).joinedload(QuizVersion.questions),
        )
        .where(QuizAttempt.id == attempt_id)
    )

    if not attempt or attempt.quiz_version.quiz_id != quiz.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found for this quiz.",
        )

    if not attempt.is_finalized and attempt.status == AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot adjust score for an in-progress attempt. The attempt must be submitted or expired.",
        )

    max_marks = sum(float(q.positive_marks) for q in attempt.quiz_version.questions)

    new_score = round(payload.new_score, 2)
    if math.isnan(new_score) or math.isinf(new_score):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Score must be a finite numeric value.",
        )

    if new_score < 0.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Score cannot be negative.",
        )

    if new_score > max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Adjusted score ({new_score}) cannot exceed maximum possible marks ({max_marks}).",
        )

    current_score = float(attempt.total_score) if attempt.total_score is not None else 0.0

    # Idempotent check: if score is unchanged, return existing state without duplicate log
    if round(current_score, 2) == new_score:
        return get_attempt_detail_for_teacher(db, quiz_id, attempt_id, teacher_user)

    # Record GradeAdjustment
    adjustment = GradeAdjustment(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        adjusted_by_id=teacher_user.id,
        previous_score=current_score,
        new_score=new_score,
        reason=payload.reason.strip(),
    )
    db.add(adjustment)

    attempt.total_score = new_score
    attempt.grading_status = GradingStatus.MANUALLY_ADJUSTED

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=teacher_user.id,
        action="grade_manually_adjusted",
        entity_type="quiz_attempt",
        entity_id=str(attempt.id),
        details={
            "quiz_id": str(quiz.id),
            "previous_score": current_score,
            "new_score": new_score,
            "reason": payload.reason.strip(),
        },
    )
    db.add(audit)
    db.commit()

    return get_attempt_detail_for_teacher(db, quiz_id, attempt_id, teacher_user)


def release_quiz_results(
    db: Session,
    quiz_id: uuid.UUID,
    teacher_user: User,
) -> ReleaseResultsResponse:
    """
    Explicitly release student results for an owned quiz (DEC-010, DEC-014).
    Safe to retry idempotently without generating redundant audit entries.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)

    published_versions = [v for v in quiz.versions if v.is_published]
    if not published_versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot release results: Assessment does not have a published version.",
        )

    version = published_versions[-1]

    if version.is_results_released:
        return ReleaseResultsResponse(
            quiz_id=quiz.id,
            version_number=version.version_number,
            is_results_released=True,
            results_released_at=ensure_utc(version.results_released_at),
            message="Results for this assessment are already released.",
        )

    now = datetime.now(timezone.utc)
    version.is_results_released = True
    version.results_released_at = now
    version.results_released_by_id = teacher_user.id

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=teacher_user.id,
        action="results_released",
        entity_type="quiz_version",
        entity_id=str(version.id),
        details={
            "quiz_id": str(quiz.id),
            "version_number": version.version_number,
            "released_at": now.isoformat(),
        },
    )
    db.add(audit)
    db.commit()

    return ReleaseResultsResponse(
        quiz_id=quiz.id,
        version_number=version.version_number,
        is_results_released=True,
        results_released_at=now,
        message="Assessment results successfully released to assigned students.",
    )


def sanitize_csv_cell(val: Any) -> str:
    """
    Mitigate spreadsheet formula injection in CSV exports (DEC-013).
    Escapes leading characters =, +, -, @, \\t, \\r with a single quote.
    """
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


def export_quiz_results_csv(
    db: Session,
    quiz_id: uuid.UUID,
    teacher_user: User,
) -> str:
    """
    Generate teacher CSV export of assessment results.
    - Stable, documented column headers.
    - Formula injection protection.
    - Bounded streaming generation.
    - Handles empty result sets correctly.
    """
    quiz = _get_teacher_quiz_or_404(db, quiz_id, teacher_user)
    version_ids = [v.id for v in quiz.versions]

    published_versions = [v for v in quiz.versions if v.is_published]
    active_version = published_versions[-1] if published_versions else (quiz.versions[-1] if quiz.versions else None)
    max_marks = (
        round(sum(float(q.positive_marks) for q in active_version.questions), 2)
        if (active_version and active_version.questions)
        else 0.0
    )

    # Fetch attempts
    stmt = (
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.student).joinedload(User.student_profile),
        )
        .where(QuizAttempt.quiz_version_id.in_(version_ids))
        .order_by(QuizAttempt.started_at.asc())
    )
    attempts = db.scalars(stmt).all()

    # Roster lookup
    assignments = db.scalars(select(QuizAssignment).where(QuizAssignment.quiz_id == quiz.id)).all()
    assign_by_user_id = {a.assigned_student_id: a for a in assignments if a.assigned_student_id}
    assign_by_email = {a.student_email.lower(): a for a in assignments}

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Documented CSV headers
    writer.writerow([
        "PRN",
        "Student Name",
        "Student Email",
        "Division",
        "Attempt Number",
        "Status",
        "Started At (UTC)",
        "Submitted At (UTC)",
        "Score",
        "Max Marks",
        "Grading Status",
        "Tab Switches",
    ])

    for att in attempts:
        student = att.student
        profile = student.student_profile if student else None
        assignment = assign_by_user_id.get(student.id) or (assign_by_email.get(student.email.lower()) if student else None)

        student_name = student.name if student else (assignment.student_name if assignment else "Unknown")
        student_email = student.email if student else (assignment.student_email if assignment else "N/A")
        student_prn = profile.prn if profile else (assignment.student_prn if assignment else "N/A")
        student_division = profile.current_division if profile and profile.current_division else (assignment.division if assignment else "N/A")

        score_str = f"{float(att.total_score):.2f}" if att.total_score is not None else "N/A"
        started_str = att.started_at.strftime("%Y-%m-%d %H:%M:%S") if att.started_at else ""
        submitted_str = att.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if att.submitted_at else ""

        writer.writerow([
            sanitize_csv_cell(student_prn),
            sanitize_csv_cell(student_name),
            sanitize_csv_cell(student_email),
            sanitize_csv_cell(student_division),
            att.attempt_number,
            att.status.value,
            started_str,
            submitted_str,
            score_str,
            f"{max_marks:.2f}",
            att.grading_status.value,
            att.tab_switch_count,
        ])

    return output.getvalue()


def get_student_attempt_result(
    db: Session,
    attempt_id: uuid.UUID,
    student_user: User,
) -> StudentAttemptResultResponse:
    """
    Retrieve authoritative personal score for a student after result release (DEC-010).
    - Caller must own the attempt.
    - Withheld before release (returns 403 Forbidden).
    - Protects correct answer keys and class-wide score distributions.
    """
    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.quiz_version).joinedload(QuizVersion.quiz),
            joinedload(QuizAttempt.quiz_version).joinedload(QuizVersion.questions),
        )
        .where(QuizAttempt.id == attempt_id)
    )

    if not attempt or attempt.student_id != student_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt not found.",
        )

    if not attempt.is_finalized and attempt.status == AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment attempt is still in progress.",
        )

    version = attempt.quiz_version
    quiz = version.quiz

    if not version.is_results_released:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Results for this assessment have not been released by the instructor yet.",
        )

    max_possible = sum(float(q.positive_marks) for q in (version.questions or []))

    return StudentAttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        course_code=quiz.course_code,
        attempt_number=attempt.attempt_number,
        status=attempt.status.value,
        started_at=ensure_utc(attempt.started_at),
        submitted_at=ensure_utc(attempt.submitted_at),
        total_score=float(attempt.total_score) if attempt.total_score is not None else 0.0,
        max_possible_score=round(max_possible, 2),
        grading_status=attempt.grading_status.value,
        tab_switch_count=attempt.tab_switch_count,
        is_results_released=True,
    )
