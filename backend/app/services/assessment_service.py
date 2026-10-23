"""Student active assessment delivery, autosave, telemetry, and submission engine (DEC-008, DEC-009, DEC-010, DEC-018)."""
from datetime import datetime, timezone, timedelta
import random
import uuid
from typing import List, Optional, Dict, Any, Set

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload

from app.models.attempt import (
    QuizAttempt,
    AttemptAnswer,
    AttemptTelemetryEvent,
    AttemptStatus,
    GradingStatus,
)
from app.models.audit import AuditEvent
from app.models.question import Question, QuestionType
from app.models.quiz import Quiz, QuizVersion, MultiAnswerPolicy
from app.models.roster import QuizAssignment
from app.models.user import User, UserRole
from app.schemas.assessment import (
    StudentQuizSummary,
    AttemptStartResponse,
    SanitizedOptionResponse,
    SanitizedQuestionResponse,
    SavedAnswerResponse,
    AttemptContentResponse,
    AssessmentReadinessResponse,
    AnswerSaveRequest,
    AnswerSaveResponse,
    TelemetryEventRequest,
    TelemetryEventResponse,
    AttemptSubmissionResponse,
)
from app.services.eligibility import check_student_quiz_eligibility, ensure_utc


def list_student_quizzes(db: Session, student_user: User) -> List[StudentQuizSummary]:
    """
    List all assessments assigned to the authenticated student with real-time status.
    Excludes archived assessments. Checks schedule windows and attempts taken.
    """
    if student_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted: Only student accounts can query student assessments.",
        )

    # 1. Fetch active assignments for this student
    stmt = (
        select(QuizAssignment)
        .options(
            joinedload(QuizAssignment.quiz).joinedload(Quiz.versions),
        )
        .where(
            QuizAssignment.is_active == True,
            (QuizAssignment.assigned_student_id == student_user.id)
            | (QuizAssignment.student_email == student_user.email.lower()),
        )
    )
    assignments = db.scalars(stmt).unique().all()

    now = datetime.now(timezone.utc)
    results: List[StudentQuizSummary] = []

    for assignment in assignments:
        quiz = assignment.quiz
        if not quiz or quiz.is_archived:
            continue

        published_versions = [v for v in quiz.versions if v.is_published]
        if not published_versions:
            continue
        version = published_versions[-1]

        opens_at = ensure_utc(version.opens_at)
        closes_at = ensure_utc(version.closes_at)

        # Check existing attempts for this student on this published version
        attempts = db.scalars(
            select(QuizAttempt).where(
                QuizAttempt.quiz_version_id == version.id,
                QuizAttempt.student_id == student_user.id,
            )
        ).all()

        attempts_taken = 0
        active_attempt_id: Optional[uuid.UUID] = None

        for att in attempts:
            if att.status == AttemptStatus.IN_PROGRESS:
                deadline = ensure_utc(att.deadline_at)
                if deadline and now > deadline:
                    # Lazily finalize expired attempt
                    finalize_and_grade_attempt(db, att, is_expired=True)
                    attempts_taken += 1
                else:
                    active_attempt_id = att.id
            elif att.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):
                attempts_taken += 1

        # Determine availability status
        if active_attempt_id is not None:
            availability_status = "OPEN"
            status_message = "Attempt in progress. Resume assessment."
        elif attempts_taken >= version.max_attempts:
            availability_status = "COMPLETED"
            status_message = f"Maximum attempts reached ({attempts_taken}/{version.max_attempts})."
        elif opens_at and now < opens_at:
            availability_status = "UPCOMING"
            status_message = f"Opens {opens_at.strftime('%b %d, %Y at %H:%M UTC')}."
        elif closes_at and now > closes_at:
            availability_status = "CLOSED"
            status_message = "Assessment window has closed."
        else:
            availability_status = "OPEN"
            status_message = f"Available to start ({attempts_taken}/{version.max_attempts} attempts used)."

        results.append(
            StudentQuizSummary(
                quiz_id=quiz.id,
                quiz_title=quiz.title,
                course_code=quiz.course_code,
                description=quiz.description,
                opens_at=opens_at,
                closes_at=closes_at,
                duration_minutes=version.duration_minutes,
                max_attempts=version.max_attempts,
                attempts_taken=attempts_taken,
                active_attempt_id=active_attempt_id,
                availability_status=availability_status,
                status_message=status_message,
            )
        )

    return results


def get_assessment_readiness(
    db: Session,
    quiz_id: uuid.UUID,
    student_user: User,
) -> AssessmentReadinessResponse:
    """
    Retrieve pre-quiz assessment instructions, browser prerequisites, and proctoring policy snapshot (DEC-021).
    - Authoritative server-side verification: student enrollment, published version, and time window.
    - Guarantees transparency: student sees full policy and warnings before starting/consuming attempt.
    """
    eligibility = check_student_quiz_eligibility(db, quiz_id, student_user)

    version = db.scalar(
        select(QuizVersion).where(QuizVersion.id == eligibility.quiz_version_id)
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment version definition not found.",
        )

    # Check attempts taken and active attempt
    attempts = db.scalars(
        select(QuizAttempt).where(
            QuizAttempt.quiz_version_id == version.id,
            QuizAttempt.student_id == student_user.id,
        )
    ).all()

    attempts_taken = len([a for a in attempts if a.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED)])
    active_att = next((a for a in attempts if a.status == AttemptStatus.IN_PROGRESS), None)

    can_start = eligibility.is_eligible and (active_att is not None or attempts_taken < version.max_attempts)

    return AssessmentReadinessResponse(
        quiz_id=eligibility.quiz_id,
        quiz_title=eligibility.quiz_title,
        course_code=eligibility.course_code,
        description=version.description,
        opens_at=ensure_utc(eligibility.opens_at),
        closes_at=ensure_utc(eligibility.closes_at),
        duration_minutes=eligibility.duration_minutes,
        max_attempts=eligibility.max_attempts,
        attempts_taken=attempts_taken,
        allow_backtracking=version.allow_backtracking,
        free_violation_allowance=version.tab_switch_limit,
        violation_penalty_marks=float(version.tab_switch_penalty_marks),
        max_proctoring_deduction=float(version.max_proctoring_deduction) if version.max_proctoring_deduction is not None else 5.00,
        enable_copy_paste_restriction=version.enable_copy_paste_restriction,
        count_copy_paste_violations=version.count_copy_paste_violations,
        require_fullscreen=version.require_fullscreen,
        count_fullscreen_exit_violations=version.count_fullscreen_exit_violations,
        count_tab_switch_violations=version.count_tab_switch_violations,
        count_dev_tools_violations=version.count_dev_tools_violations,
        enable_proctoring_warnings=version.enable_proctoring_warnings,
        has_active_attempt=active_att is not None,
        active_attempt_id=active_att.id if active_att else None,
        can_start=can_start,
        status_message=eligibility.status_message,
    )


def start_or_resume_attempt(
    db: Session,
    quiz_id: uuid.UUID,
    student_user: User,
) -> AttemptStartResponse:
    """
    Start a new assessment attempt or resume an active in-progress attempt.
    Guarantees:
    - Authoritative server eligibility check.
    - Idempotent resumption on refresh or repeated clicks without timer reset.
    - Transactional attempt limit enforcement.
    - Authoritative deadline calculation: min(started_at + duration, closes_at).
    - Stable randomized question/option sequence persistence.
    """
    # 1. Authoritative eligibility check
    eligibility = check_student_quiz_eligibility(db, quiz_id, student_user)
    if not eligibility.is_eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=eligibility.status_message,
        )

    version_id = eligibility.quiz_version_id
    version = db.get(QuizVersion, version_id)
    if not version or not version.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment published version is unavailable.",
        )

    now = datetime.now(timezone.utc)

    # 2. Check for active in-progress attempt
    existing_in_progress = db.scalar(
        select(QuizAttempt).where(
            QuizAttempt.quiz_version_id == version.id,
            QuizAttempt.student_id == student_user.id,
            QuizAttempt.status == AttemptStatus.IN_PROGRESS,
        )
    )

    if existing_in_progress:
        deadline = ensure_utc(existing_in_progress.deadline_at)
        if deadline and now > deadline:
            # Lazily finalize expired attempt
            finalize_and_grade_attempt(db, existing_in_progress, is_expired=True)
        else:
            # Resume existing attempt without creating a new record or resetting deadline
            remaining = max(0, int((deadline - now).total_seconds())) if deadline else 0
            return AttemptStartResponse(
                attempt_id=existing_in_progress.id,
                quiz_id=quiz_id,
                quiz_version_id=version.id,
                attempt_number=existing_in_progress.attempt_number,
                status=existing_in_progress.status,
                started_at=ensure_utc(existing_in_progress.started_at),
                deadline_at=deadline,
                remaining_seconds=remaining,
                is_resumed=True,
            )

    # 3. Check attempt count limit
    previous_count = db.scalar(
        select(func.count(QuizAttempt.id)).where(
            QuizAttempt.quiz_version_id == version.id,
            QuizAttempt.student_id == student_user.id,
        )
    ) or 0

    if previous_count >= version.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum attempts limit reached for this assessment ({previous_count}/{version.max_attempts}).",
        )

    # 4. Check assessment schedule window
    opens_at = ensure_utc(version.opens_at)
    closes_at = ensure_utc(version.closes_at)

    if opens_at and now < opens_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Assessment is not yet open. Scheduled to open at {opens_at.strftime('%Y-%m-%d %H:%M UTC')}.",
        )
    if closes_at and now > closes_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessment window has closed. New attempts cannot be started.",
        )

    # 5. Calculate authoritative deadline: min(now + duration, closes_at)
    candidate_deadline = now + timedelta(minutes=version.duration_minutes)
    deadline = min(candidate_deadline, closes_at) if closes_at else candidate_deadline

    # 6. Build and persist stable randomized question & option sequences
    q_stmt = (
        select(Question)
        .options(joinedload(Question.options))
        .where(Question.quiz_version_id == version.id)
        .order_by(Question.order_index)
    )
    questions = db.scalars(q_stmt).unique().all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment content contains no questions.",
        )

    # Question ordering
    if version.shuffle_questions:
        shuffled_q = list(questions)
        random.shuffle(shuffled_q)
    else:
        shuffled_q = sorted(questions, key=lambda q: q.order_index)

    question_order = [str(q.id) for q in shuffled_q]

    # Option ordering per question
    option_order: Dict[str, List[str]] = {}
    for q in questions:
        if version.shuffle_options:
            opts = list(q.options)
            random.shuffle(opts)
        else:
            opts = sorted(q.options, key=lambda o: o.order_index)
        option_order[str(q.id)] = [str(o.id) for o in opts]

    # 7. Create new QuizAttempt atomically
    attempt = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        student_id=student_user.id,
        attempt_number=previous_count + 1,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now,
        deadline_at=deadline,
        tab_switch_count=0,
        grading_status=GradingStatus.PENDING,
        is_finalized=False,
        question_order=question_order,
        option_order=option_order,
    )
    db.add(attempt)

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=student_user.id,
        action="attempt_started",
        entity_type="quiz_attempt",
        entity_id=str(attempt.id),
        details={
            "quiz_id": str(quiz_id),
            "quiz_version_id": str(version.id),
            "attempt_number": attempt.attempt_number,
            "deadline_at": deadline.isoformat(),
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(attempt)

    remaining = max(0, int((deadline - now).total_seconds()))

    return AttemptStartResponse(
        attempt_id=attempt.id,
        quiz_id=quiz_id,
        quiz_version_id=version.id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=ensure_utc(attempt.started_at),
        deadline_at=deadline,
        remaining_seconds=remaining,
        is_resumed=False,
    )


def get_attempt_content(
    db: Session,
    attempt_id: uuid.UUID,
    student_user: User,
) -> AttemptContentResponse:
    """
    Fetch sanitized assessment content and current student answer state.
    Strictly conceals correct-answer keys and scoring explanations.
    """
    attempt = db.scalar(
        select(QuizAttempt)
        .options(
            joinedload(QuizAttempt.quiz_version).joinedload(QuizVersion.quiz),
            joinedload(QuizAttempt.answers),
        )
        .where(QuizAttempt.id == attempt_id)
    )

    if not attempt or attempt.student_id != student_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found.",
        )

    now = datetime.now(timezone.utc)
    deadline = ensure_utc(attempt.deadline_at)

    # Check lazy expiry
    if attempt.status == AttemptStatus.IN_PROGRESS and deadline and now > deadline:
        finalize_and_grade_attempt(db, attempt, is_expired=True)
        db.refresh(attempt)

    version = attempt.quiz_version
    quiz = version.quiz

    # Fetch questions and options for this version
    q_stmt = (
        select(Question)
        .options(joinedload(Question.options))
        .where(Question.quiz_version_id == version.id)
    )
    raw_questions = db.scalars(q_stmt).unique().all()
    q_map = {str(q.id): q for q in raw_questions}

    # Answer map
    answer_map = {str(a.question_id): a for a in attempt.answers}

    # Respect stored question_order or natural ordering
    if attempt.question_order and isinstance(attempt.question_order, list):
        ordered_q_ids = [qid for qid in attempt.question_order if qid in q_map]
        # Append any missing
        for qid in q_map:
            if qid not in ordered_q_ids:
                ordered_q_ids.append(qid)
    else:
        ordered_q_ids = [str(q.id) for q in sorted(raw_questions, key=lambda q: q.order_index)]

    sanitized_questions: List[SanitizedQuestionResponse] = []

    for idx, qid in enumerate(ordered_q_ids):
        q = q_map[qid]
        opt_map = {str(o.id): o for o in q.options}

        # Respect stored option_order for this question
        opt_order = (
            attempt.option_order.get(qid)
            if attempt.option_order and isinstance(attempt.option_order, dict)
            else None
        )
        if opt_order and isinstance(opt_order, list):
            ordered_opt_ids = [oid for oid in opt_order if oid in opt_map]
            for oid in opt_map:
                if oid not in ordered_opt_ids:
                    ordered_opt_ids.append(oid)
        else:
            ordered_opt_ids = [str(o.id) for o in sorted(q.options, key=lambda o: o.order_index)]

        sanitized_options = [
            SanitizedOptionResponse(
                id=opt_map[oid].id,
                option_text=opt_map[oid].option_text,
                order_index=opt_idx,
            )
            for opt_idx, oid in enumerate(ordered_opt_ids)
        ]

        saved_ans = answer_map.get(qid)
        saved_ans_resp = (
            SavedAnswerResponse(
                selected_option_ids=list(saved_ans.selected_option_ids or []),
                is_marked_for_review=saved_ans.is_marked_for_review,
                saved_at=ensure_utc(saved_ans.saved_at),
            )
            if saved_ans
            else None
        )

        sanitized_questions.append(
            SanitizedQuestionResponse(
                id=q.id,
                prompt=q.prompt,
                question_type=q.question_type,
                order_index=idx,
                positive_marks=float(q.positive_marks),
                negative_marks=float(q.negative_marks),
                options=sanitized_options,
                saved_answer=saved_ans_resp,
            )
        )

    remaining = max(0, int((deadline - now).total_seconds())) if deadline else 0

    return AttemptContentResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        course_code=quiz.course_code,
        status=attempt.status,
        started_at=ensure_utc(attempt.started_at),
        deadline_at=deadline,
        server_time=now,
        remaining_seconds=remaining,
        is_finalized=attempt.is_finalized,
        tab_switch_count=attempt.tab_switch_count,
        tab_switch_limit=version.tab_switch_limit,
        violation_count=attempt.violation_count,
        free_violation_allowance=version.tab_switch_limit,
        violation_penalty_marks=float(version.tab_switch_penalty_marks),
        max_proctoring_deduction=float(version.max_proctoring_deduction) if version.max_proctoring_deduction is not None else 5.00,
        current_proctoring_deduction=float(attempt.proctoring_deduction) if attempt.proctoring_deduction is not None else 0.00,
        enable_copy_paste_restriction=version.enable_copy_paste_restriction,
        count_copy_paste_violations=version.count_copy_paste_violations,
        require_fullscreen=version.require_fullscreen,
        count_fullscreen_exit_violations=version.count_fullscreen_exit_violations,
        count_tab_switch_violations=version.count_tab_switch_violations,
        count_dev_tools_violations=version.count_dev_tools_violations,
        enable_proctoring_warnings=version.enable_proctoring_warnings,
        allow_backtracking=version.allow_backtracking,
        questions=sanitized_questions,
    )


def save_attempt_answer(
    db: Session,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AnswerSaveRequest,
    student_user: User,
) -> AnswerSaveResponse:
    """
    Autosave an individual answer for a question in an active attempt.
    Guarantees:
    - Attempt ownership verification.
    - Rejects answers if attempt is finalized or deadline has expired.
    - Validates options belong strictly to the target question in the attempt's version.
    - Rejects out-of-order writes using monotonic client_timestamp comparison.
    - Targeted database operation (no full quiz reload).
    """
    attempt = db.get(QuizAttempt, attempt_id)
    if not attempt or attempt.student_id != student_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found.",
        )

    if attempt.is_finalized or attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment attempt is already finalized. No further changes can be recorded.",
        )

    now = datetime.now(timezone.utc)
    deadline = ensure_utc(attempt.deadline_at)

    if deadline and now > deadline:
        finalize_and_grade_attempt(db, attempt, is_expired=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment deadline has expired. Attempt has been finalized.",
        )

    # Validate Question exists and belongs to attempt's QuizVersion
    q_stmt = (
        select(Question)
        .options(joinedload(Question.options))
        .where(
            Question.id == question_id,
            Question.quiz_version_id == attempt.quiz_version_id,
        )
    )
    question = db.scalar(q_stmt)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question not found or does not belong to this assessment version.",
        )

    # Validate Option IDs
    valid_option_ids = {str(opt.id) for opt in question.options}
    for opt_id in payload.selected_option_ids:
        if opt_id not in valid_option_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Option choice '{opt_id}' is invalid for this question.",
            )

    # Enforce Question Type Constraints
    if question.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
        if len(payload.selected_option_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Single-choice questions allow at most one selected option.",
            )

    # Check for existing answer
    existing_answer = db.scalar(
        select(AttemptAnswer).where(
            AttemptAnswer.attempt_id == attempt.id,
            AttemptAnswer.question_id == question.id,
        )
    )

    # Out-of-order write protection
    if (
        existing_answer
        and payload.client_timestamp
        and existing_answer.client_timestamp
    ):
        req_ts = ensure_utc(payload.client_timestamp)
        saved_ts = ensure_utc(existing_answer.client_timestamp)
        if req_ts and saved_ts and req_ts < saved_ts:
            # Stale out-of-order delayed request: do not overwrite newer confirmed answer
            return AnswerSaveResponse(
                success=True,
                saved_at=ensure_utc(existing_answer.saved_at),
                is_marked_for_review=existing_answer.is_marked_for_review,
                selected_option_ids=list(existing_answer.selected_option_ids or []),
            )

    if existing_answer:
        existing_answer.selected_option_ids = list(payload.selected_option_ids)
        existing_answer.is_marked_for_review = payload.is_marked_for_review
        existing_answer.saved_at = now
        existing_answer.client_timestamp = payload.client_timestamp
        target_answer = existing_answer
    else:
        target_answer = AttemptAnswer(
            id=uuid.uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_ids=list(payload.selected_option_ids),
            is_marked_for_review=payload.is_marked_for_review,
            saved_at=now,
            client_timestamp=payload.client_timestamp,
        )
        db.add(target_answer)

    db.commit()
    db.refresh(target_answer)

    return AnswerSaveResponse(
        success=True,
        saved_at=ensure_utc(target_answer.saved_at),
        is_marked_for_review=target_answer.is_marked_for_review,
        selected_option_ids=list(target_answer.selected_option_ids or []),
    )


VALID_TELEMETRY_TYPES = {
    "tab_switch",
    "window_blur",
    "fullscreen_exit",
    "copy_paste_attempt",
    "dev_tools_shortcut",
}


def record_telemetry_event(
    db: Session,
    attempt_id: uuid.UUID,
    payload: TelemetryEventRequest,
    student_user: User,
) -> TelemetryEventResponse:
    """
    Record client proctoring observation with idempotency, deduplication, and policy enforcement (DEC-021).
    - Rejects invalid/unsupported event types.
    - Idempotent via client_event_id: retries return current state without double-counting.
    - Deduplicates related window_blur and tab_switch events occurring within 1000ms.
    - Respects teacher-configured proctoring policy flags for violation accounting.
    - Server-authoritative calculation of remaining free violations and estimated deductions.
    """
    attempt = db.scalar(
        select(QuizAttempt)
        .options(joinedload(QuizAttempt.quiz_version))
        .where(QuizAttempt.id == attempt_id)
    )
    if not attempt or attempt.student_id != student_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt session not found.",
        )

    version = attempt.quiz_version
    event_type = payload.event_type.strip()[:64]
    if event_type not in VALID_TELEMETRY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported telemetry event type '{event_type}'.",
        )

    free_allowance = version.tab_switch_limit
    penalty_rate = float(version.tab_switch_penalty_marks)
    max_deduction = float(version.max_proctoring_deduction) if version.max_proctoring_deduction is not None else 5.00

    # If attempt is already finalized, return current immutable state
    if attempt.is_finalized or attempt.status != AttemptStatus.IN_PROGRESS:
        v_count = attempt.violation_count
        chargeable = max(0, v_count - free_allowance)
        current_ded = min(chargeable * penalty_rate, max_deduction)
        return TelemetryEventResponse(
            tab_switch_count=attempt.tab_switch_count,
            violation_count=v_count,
            free_allowance=free_allowance,
            remaining_free_violations=max(0, free_allowance - v_count),
            chargeable_violations=chargeable,
            current_deduction=round(current_ded, 2),
            limit_exceeded=v_count > free_allowance,
            tab_switch_limit=free_allowance,
            warning_message=None,
        )

    now = datetime.now(timezone.utc)

    # 1. Idempotency check via client_event_id
    client_eid = None
    if payload.client_event_id:
        client_eid = payload.client_event_id.strip()[:64]
        existing_event = db.scalar(
            select(AttemptTelemetryEvent).where(
                AttemptTelemetryEvent.attempt_id == attempt.id,
                AttemptTelemetryEvent.client_event_id == client_eid,
            )
        )
        if existing_event:
            v_count = attempt.violation_count
            chargeable = max(0, v_count - free_allowance)
            current_ded = min(chargeable * penalty_rate, max_deduction)
            return TelemetryEventResponse(
                tab_switch_count=attempt.tab_switch_count,
                violation_count=v_count,
                free_allowance=free_allowance,
                remaining_free_violations=max(0, free_allowance - v_count),
                chargeable_violations=chargeable,
                current_deduction=round(current_ded, 2),
                limit_exceeded=v_count > free_allowance,
                tab_switch_limit=free_allowance,
                warning_message=None,
            )

    # 2. Deduplication check: check last telemetry event on this attempt
    last_event = db.scalar(
        select(AttemptTelemetryEvent)
        .where(AttemptTelemetryEvent.attempt_id == attempt.id)
        .order_by(AttemptTelemetryEvent.event_timestamp.desc())
        .limit(1)
    )

    is_deduplicated = False
    if last_event:
        last_ts = ensure_utc(last_event.event_timestamp)
        delta_seconds = abs((now - last_ts).total_seconds()) if last_ts else 999.0
        # If window_blur and tab_switch occur together within 1000ms for a single incident:
        if delta_seconds < 1.0 and {last_event.event_type, event_type} == {"window_blur", "tab_switch"}:
            is_deduplicated = True

    # 3. Policy rule check: determine if event type counts toward violations
    is_policy_chargeable = False
    if event_type in ("tab_switch", "window_blur"):
        is_policy_chargeable = version.count_tab_switch_violations
    elif event_type == "fullscreen_exit":
        is_policy_chargeable = version.count_fullscreen_exit_violations
    elif event_type == "copy_paste_attempt":
        is_policy_chargeable = version.count_copy_paste_violations
    elif event_type == "dev_tools_shortcut":
        is_policy_chargeable = version.count_dev_tools_violations

    # Record event in audit telemetry log
    event_meta = dict(payload.event_data or {})
    event_meta["is_deduplicated"] = is_deduplicated
    event_meta["is_policy_chargeable"] = is_policy_chargeable
    if payload.client_timestamp:
        event_meta["client_timestamp"] = payload.client_timestamp.isoformat()

    event = AttemptTelemetryEvent(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        event_type=event_type,
        client_event_id=client_eid,
        event_timestamp=now,
        event_data=event_meta,
    )
    db.add(event)

    # Increment counters if not deduplicated
    if not is_deduplicated:
        if is_policy_chargeable:
            attempt.violation_count += 1
        if event_type in ("tab_switch", "window_blur"):
            attempt.tab_switch_count += 1

    db.commit()
    db.refresh(attempt)

    v_count = attempt.violation_count
    chargeable = max(0, v_count - free_allowance)
    current_ded = min(chargeable * penalty_rate, max_deduction)
    remaining_free = max(0, free_allowance - v_count)
    limit_exceeded = v_count > free_allowance

    warning_msg = None
    if version.enable_proctoring_warnings:
        if remaining_free > 0:
            warning_msg = f"Security event detected ({event_type}). You have {remaining_free} free violation(s) remaining."
        elif remaining_free == 0 and chargeable == 0:
            warning_msg = "Your free violation allowance has been exhausted. Further violations will reduce your score."
        else:
            warning_msg = f"Violation penalty applied ({chargeable} chargeable incident(s)). Current estimated deduction: {current_ded:.2f} marks."

    return TelemetryEventResponse(
        tab_switch_count=attempt.tab_switch_count,
        violation_count=v_count,
        free_allowance=free_allowance,
        remaining_free_violations=remaining_free,
        chargeable_violations=chargeable,
        current_deduction=round(current_ded, 2),
        limit_exceeded=limit_exceeded,
        tab_switch_limit=free_allowance,
        warning_message=warning_msg,
    )


def finalize_and_grade_attempt(
    db: Session,
    attempt: QuizAttempt,
    is_expired: bool = False,
) -> AttemptSubmissionResponse:
    """
    Authoritative attempt evaluation and grading engine.
    Guarantees:
    - Idempotency: repeated calls return consistent finalized state without re-grading.
    - Evaluates positive marks, negative marks, and multi-answer scoring policies:
      all_or_nothing, partial_with_penalty, and partial_no_penalty.
    - Evaluates proctoring deduction with policy caps and boundaries (DEC-021).
    - Gated result release: student receives score breakdown only if results are released.
    """
    version = db.scalar(
        select(QuizVersion)
        .options(
            joinedload(QuizVersion.questions).joinedload(Question.options),
        )
        .where(QuizVersion.id == attempt.quiz_version_id)
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment version definition not found for grading.",
        )

    # Idempotent check: if already finalized, return stored score
    if attempt.is_finalized:
        return AttemptSubmissionResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            submitted_at=ensure_utc(attempt.submitted_at or attempt.updated_at),
            is_finalized=True,
            total_score=float(attempt.total_score) if version.is_results_released and attempt.total_score is not None else None,
            is_results_released=version.is_results_released,
            message="Assessment attempt is already submitted and finalized.",
        )

    now = datetime.now(timezone.utc)
    deadline = ensure_utc(attempt.deadline_at)

    if is_expired or (deadline and now > deadline):
        attempt.status = AttemptStatus.EXPIRED
    else:
        attempt.status = AttemptStatus.SUBMITTED

    attempt.submitted_at = now
    attempt.is_finalized = True

    # Load existing answers
    answers = db.scalars(
        select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)
    ).all()
    answer_map = {a.question_id: a for a in answers}

    raw_total_score = 0.0

    # Grade each question according to institutional scoring policies (DEC-006, DEC-008, DEC-014)
    for q in version.questions:
        ans = answer_map.get(q.id)
        selected_ids: Set[str] = set(ans.selected_option_ids) if (ans and ans.selected_option_ids) else set()

        correct_opt_ids = {str(opt.id) for opt in q.options if opt.is_correct}
        incorrect_opt_ids = {str(opt.id) for opt in q.options if not opt.is_correct}

        pos_marks = float(q.positive_marks)
        neg_marks = float(q.negative_marks)
        q_score = 0.0

        if not selected_ids:
            # Unattempted question
            q_score = 0.0
        elif q.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
            if selected_ids == correct_opt_ids:
                q_score = pos_marks
            else:
                q_score = -neg_marks
        elif q.question_type == QuestionType.MULTIPLE_CHOICE:
            policy = version.multi_answer_policy
            if policy == MultiAnswerPolicy.ALL_OR_NOTHING:
                if selected_ids == correct_opt_ids:
                    q_score = pos_marks
                else:
                    # Apply negative marks only if incorrect options were selected
                    has_incorrect = bool(selected_ids & incorrect_opt_ids)
                    q_score = -neg_marks if has_incorrect else 0.0
            elif policy == MultiAnswerPolicy.PARTIAL_NO_PENALTY:
                # Fractional credit for correct options, bounded below by 0
                c_total = len(correct_opt_ids) or 1
                i_total = len(incorrect_opt_ids) or 1
                c_chosen = len(selected_ids & correct_opt_ids)
                i_chosen = len(selected_ids & incorrect_opt_ids)
                fraction = max(0.0, (c_chosen / c_total) - (i_chosen / i_total))
                q_score = round(fraction * pos_marks, 2)
            elif policy == MultiAnswerPolicy.PARTIAL_WITH_PENALTY:
                # Proportional credit with penalty, bounded below by -negative_marks
                c_total = len(correct_opt_ids) or 1
                i_total = len(incorrect_opt_ids) or 1
                c_chosen = len(selected_ids & correct_opt_ids)
                i_chosen = len(selected_ids & incorrect_opt_ids)
                fraction = (c_chosen / c_total) - (i_chosen / i_total)
                raw_score = fraction * pos_marks
                q_score = round(max(-neg_marks, raw_score), 2)

        if ans:
            ans.awarded_marks = q_score

        raw_total_score += q_score

    # Configurable Proctoring Penalty Calculation (DEC-008, DEC-009, DEC-021)
    # V = total chargeable violations
    # F = configured free violation allowance
    # D = configured deduction per chargeable violation
    # C = configured maximum cumulative proctoring deduction
    # S = raw score before proctoring deduction
    V = attempt.violation_count
    F = version.tab_switch_limit
    D = float(version.tab_switch_penalty_marks)
    C = float(version.max_proctoring_deduction) if version.max_proctoring_deduction is not None else 5.00
    S = raw_total_score

    chargeable_violations = max(0, V - F)
    # proctoring_deduction = min(chargeable_violations * D, C, max(0, S))
    calculated_deduction = chargeable_violations * D
    proctoring_deduction = min(calculated_deduction, C, max(0.0, S))

    final_score = max(0.0, round(S - proctoring_deduction, 2))
    attempt.proctoring_deduction = round(proctoring_deduction, 2)
    attempt.total_score = final_score
    attempt.grading_status = GradingStatus.AUTO_GRADED

    # Audit event
    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=attempt.student_id,
        action="attempt_finalized",
        entity_type="quiz_attempt",
        entity_id=str(attempt.id),
        details={
            "status": attempt.status.value,
            "raw_total": raw_total_score,
            "total_violations": V,
            "free_allowance": F,
            "chargeable_violations": chargeable_violations,
            "deduction_rate": D,
            "max_cap": C,
            "proctoring_deduction": attempt.proctoring_deduction,
            "final_score": final_score,
            "is_expired": is_expired,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(attempt)

    message = (
        "Assessment submitted successfully. Results will be released by your course instructor."
        if not version.is_results_released
        else f"Assessment submitted. Your evaluated score: {final_score}."
    )

    return AttemptSubmissionResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        submitted_at=ensure_utc(attempt.submitted_at),
        is_finalized=True,
        total_score=final_score if version.is_results_released else None,
        is_results_released=version.is_results_released,
        message=message,
    )
