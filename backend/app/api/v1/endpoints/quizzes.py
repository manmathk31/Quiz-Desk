"""Teacher Quiz Builder, immutable version management, and publishing API endpoints (DEC-006, DEC-008, DEC-014)."""
from datetime import datetime, timezone
import math
from typing import List, Optional, Tuple
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from app.core.auth import require_faculty
from app.core.database import get_db
from app.models.user import User
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.schemas.quiz import (
    QuizCreateRequest,
    QuizUpdateRequest,
    QuizListItemResponse,
    QuizListResponse,
    QuizDetailResponse,
    QuizVersionResponse,
    QuizPreviewResponse,
    PublishQuizResponse,
    AddQuestionsFromBankRequest,
    ReorderQuestionsRequest,
    DifficultyBreakdown,
    PrePublishValidationError,
)
from app.schemas.question import QuestionResponse, QuestionOptionResponse

router = APIRouter(prefix="/quizzes", tags=["Quiz Builder & Management"])


def _calculate_version_metrics(version: QuizVersion) -> Tuple[int, float, DifficultyBreakdown]:
    """Calculate question count, total possible marks, and difficulty distribution for a version."""
    questions = version.questions or []
    total_q = len(questions)
    total_m = sum(float(q.positive_marks) for q in questions)
    easy_count = sum(1 for q in questions if q.difficulty == QuestionDifficulty.EASY)
    med_count = sum(1 for q in questions if q.difficulty == QuestionDifficulty.MEDIUM)
    hard_count = sum(1 for q in questions if q.difficulty == QuestionDifficulty.HARD)

    return total_q, round(total_m, 2), DifficultyBreakdown(easy=easy_count, medium=med_count, hard=hard_count)


def _serialize_version_response(version: QuizVersion) -> QuizVersionResponse:
    """Format QuizVersion with nested questions and metrics."""
    total_q, total_m, diff_breakdown = _calculate_version_metrics(version)
    return QuizVersionResponse(
        id=version.id,
        quiz_id=version.quiz_id,
        version_number=version.version_number,
        title=version.title,
        description=version.description,
        is_published=version.is_published,
        opens_at=version.opens_at,
        closes_at=version.closes_at,
        duration_minutes=version.duration_minutes,
        max_attempts=version.max_attempts,
        allow_backtracking=version.allow_backtracking,
        shuffle_questions=version.shuffle_questions,
        shuffle_options=version.shuffle_options,
        multi_answer_policy=version.multi_answer_policy,
        tab_switch_limit=version.tab_switch_limit,
        tab_switch_penalty_marks=float(version.tab_switch_penalty_marks),
        max_proctoring_deduction=float(version.max_proctoring_deduction) if version.max_proctoring_deduction is not None else 5.00,
        enable_copy_paste_restriction=version.enable_copy_paste_restriction,
        count_copy_paste_violations=version.count_copy_paste_violations,
        require_fullscreen=version.require_fullscreen,
        count_fullscreen_exit_violations=version.count_fullscreen_exit_violations,
        count_tab_switch_violations=version.count_tab_switch_violations,
        count_dev_tools_violations=version.count_dev_tools_violations,
        enable_proctoring_warnings=version.enable_proctoring_warnings,
        is_results_released=version.is_results_released,
        created_at=version.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                created_by_id=q.created_by_id,
                question_type=q.question_type,
                difficulty=q.difficulty,
                prompt=q.prompt,
                positive_marks=float(q.positive_marks),
                negative_marks=float(q.negative_marks),
                options=[
                    QuestionOptionResponse(
                        id=o.id,
                        option_text=o.option_text,
                        order_index=o.order_index,
                        is_correct=o.is_correct,
                    )
                    for o in (q.options or [])
                ],
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in (version.questions or [])
        ],
        total_questions=total_q,
        total_marks=total_m,
        difficulty_breakdown=diff_breakdown,
    )


def _validate_version_for_publication(version: QuizVersion) -> List[PrePublishValidationError]:
    """Validate server-side publication readiness rules."""
    errors: List[PrePublishValidationError] = []

    questions = version.questions or []
    if len(questions) == 0:
        errors.append(
            PrePublishValidationError(
                field="questions",
                message="A quiz must contain at least one question before it can be published.",
            )
        )

    for idx, q in enumerate(questions, start=1):
        opts = q.options or []
        if len(opts) < 2:
            errors.append(
                PrePublishValidationError(
                    field=f"questions[{idx}]",
                    message=f"Question {idx} ('{q.prompt[:30]}...') must define at least two answer options.",
                )
            )
        correct_count = sum(1 for o in opts if o.is_correct)
        if q.question_type == QuestionType.SINGLE_CHOICE and correct_count != 1:
            errors.append(
                PrePublishValidationError(
                    field=f"questions[{idx}]",
                    message=f"Single-choice question {idx} must have exactly one correct option (found {correct_count}).",
                )
            )
        elif q.question_type == QuestionType.MULTIPLE_CHOICE and correct_count < 1:
            errors.append(
                PrePublishValidationError(
                    field=f"questions[{idx}]",
                    message=f"Multiple-choice question {idx} must have at least one correct option.",
                )
            )
        elif q.question_type == QuestionType.TRUE_FALSE and (len(opts) != 2 or correct_count != 1):
            errors.append(
                PrePublishValidationError(
                    field=f"questions[{idx}]",
                    message=f"True/False question {idx} must define exactly two options with one correct answer.",
                )
            )

    if version.closes_at <= version.opens_at:
        errors.append(
            PrePublishValidationError(
                field="schedule",
                message="Closing time must be strictly after opening time.",
            )
        )

    if version.duration_minutes <= 0:
        errors.append(
            PrePublishValidationError(
                field="duration_minutes",
                message="Duration must be strictly greater than 0 minutes.",
            )
        )

    if version.max_attempts <= 0:
        errors.append(
            PrePublishValidationError(
                field="max_attempts",
                message="Maximum attempts must be at least 1.",
            )
        )

    return errors


def _ensure_active_draft_version(quiz: Quiz, db: Session) -> QuizVersion:
    """
    Retrieve active draft version for the quiz.
    If the quiz is currently published and has no active draft, spawn a new version
    by cloning the latest published version's settings and questions.
    """
    # Look for existing unpublished draft version
    draft_stmt = (
        select(QuizVersion)
        .options(selectinload(QuizVersion.questions).selectinload(Question.options))
        .where(
            QuizVersion.quiz_id == quiz.id,
            QuizVersion.is_published.is_(False),
        )
        .order_by(QuizVersion.version_number.desc())
    )
    draft = db.scalar(draft_stmt)
    if draft:
        return draft

    # No active draft exists. Find the latest published version to fork from.
    pub_stmt = (
        select(QuizVersion)
        .options(selectinload(QuizVersion.questions).selectinload(Question.options))
        .where(
            QuizVersion.quiz_id == quiz.id,
            QuizVersion.is_published.is_(True),
        )
        .order_by(QuizVersion.version_number.desc())
    )
    latest_pub = db.scalar(pub_stmt)
    if not latest_pub:
        # Should not happen under normal flow, but create v1 draft if none exists at all
        new_v = QuizVersion(
            quiz_id=quiz.id,
            version_number=1,
            title=quiz.title,
            description=quiz.description,
            is_published=False,
            opens_at=datetime.now(timezone.utc),
            closes_at=datetime.now(timezone.utc),
            duration_minutes=60,
            max_attempts=1,
        )
        db.add(new_v)
        db.flush()
        return new_v

    # Spawn new version incrementing version_number
    new_version_num = latest_pub.version_number + 1
    new_draft = QuizVersion(
        quiz_id=quiz.id,
        version_number=new_version_num,
        title=latest_pub.title,
        description=latest_pub.description,
        is_published=False,
        opens_at=latest_pub.opens_at,
        closes_at=latest_pub.closes_at,
        duration_minutes=latest_pub.duration_minutes,
        max_attempts=latest_pub.max_attempts,
        allow_backtracking=latest_pub.allow_backtracking,
        shuffle_questions=latest_pub.shuffle_questions,
        shuffle_options=latest_pub.shuffle_options,
        multi_answer_policy=latest_pub.multi_answer_policy,
        tab_switch_limit=latest_pub.tab_switch_limit,
        tab_switch_penalty_marks=latest_pub.tab_switch_penalty_marks,
        max_proctoring_deduction=latest_pub.max_proctoring_deduction,
        enable_copy_paste_restriction=latest_pub.enable_copy_paste_restriction,
        count_copy_paste_violations=latest_pub.count_copy_paste_violations,
        require_fullscreen=latest_pub.require_fullscreen,
        count_fullscreen_exit_violations=latest_pub.count_fullscreen_exit_violations,
        count_tab_switch_violations=latest_pub.count_tab_switch_violations,
        count_dev_tools_violations=latest_pub.count_dev_tools_violations,
        enable_proctoring_warnings=latest_pub.enable_proctoring_warnings,
    )
    db.add(new_draft)
    db.flush()

    # Deep clone questions and options from published version into new draft
    for prev_q in latest_pub.questions:
        cloned_q = Question(
            quiz_version_id=new_draft.id,
            created_by_id=quiz.created_by_id,
            question_type=prev_q.question_type,
            difficulty=prev_q.difficulty,
            prompt=prev_q.prompt,
            order_index=prev_q.order_index,
            positive_marks=prev_q.positive_marks,
            negative_marks=prev_q.negative_marks,
        )
        db.add(cloned_q)
        db.flush()

        for prev_opt in prev_q.options:
            cloned_opt = QuestionOption(
                question_id=cloned_q.id,
                option_text=prev_opt.option_text,
                order_index=prev_opt.order_index,
                is_correct=prev_opt.is_correct,
            )
            db.add(cloned_opt)

    db.flush()
    # Refresh new draft with cloned questions
    db.refresh(new_draft, ["questions"])
    return new_draft


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get(
    "",
    response_model=QuizListResponse,
    summary="List teacher's quizzes",
    description="Retrieve all quizzes owned by the authenticated teacher with metadata and schedule status.",
)
async def list_quizzes(
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizListResponse:
    """List quizzes owned by the teacher with latest version metrics."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions).selectinload(QuizVersion.questions)
        )
        .where(
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
        .order_by(Quiz.created_at.desc())
    )
    quizzes = db.scalars(stmt).all()

    items: List[QuizListItemResponse] = []
    for q in quizzes:
        # Determine latest version (published or draft)
        active_version = None
        if q.versions:
            # Sort by version number desc
            sorted_versions = sorted(q.versions, key=lambda v: v.version_number, reverse=True)
            active_version = sorted_versions[0]

        if active_version:
            total_q, total_m, diff_breakdown = _calculate_version_metrics(active_version)
            items.append(
                QuizListItemResponse(
                    id=q.id,
                    title=q.title,
                    course_code=q.course_code,
                    description=q.description,
                    status=q.status,
                    created_by_id=q.created_by_id,
                    current_version_id=q.current_version_id,
                    version_number=active_version.version_number,
                    is_published=active_version.is_published,
                    opens_at=active_version.opens_at,
                    closes_at=active_version.closes_at,
                    duration_minutes=active_version.duration_minutes,
                    total_questions=total_q,
                    total_marks=total_m,
                    difficulty_breakdown=diff_breakdown,
                    created_at=q.created_at,
                    updated_at=q.updated_at,
                )
            )

    return QuizListResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=QuizDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft quiz",
    description="Initializes a new quiz and draft version 1 with schedule, rules, and telemetry settings.",
)
async def create_quiz(
    payload: QuizCreateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizDetailResponse:
    """Create quiz entity and initial draft QuizVersion transactionally."""
    quiz = Quiz(
        title=payload.title.strip(),
        course_code=payload.course_code.strip(),
        description=payload.description.strip() if payload.description else None,
        created_by_id=current_user.id,
        status=QuizStatus.DRAFT,
        is_archived=False,
    )
    db.add(quiz)
    db.flush()

    draft_version = QuizVersion(
        quiz_id=quiz.id,
        version_number=1,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        is_published=False,
        opens_at=payload.opens_at,
        closes_at=payload.closes_at,
        duration_minutes=payload.duration_minutes,
        max_attempts=payload.max_attempts,
        allow_backtracking=payload.allow_backtracking,
        shuffle_questions=payload.shuffle_questions,
        shuffle_options=payload.shuffle_options,
        multi_answer_policy=payload.multi_answer_policy,
        tab_switch_limit=payload.tab_switch_limit,
        tab_switch_penalty_marks=payload.tab_switch_penalty_marks,
        max_proctoring_deduction=payload.max_proctoring_deduction,
        enable_copy_paste_restriction=payload.enable_copy_paste_restriction,
        count_copy_paste_violations=payload.count_copy_paste_violations,
        require_fullscreen=payload.require_fullscreen,
        count_fullscreen_exit_violations=payload.count_fullscreen_exit_violations,
        count_tab_switch_violations=payload.count_tab_switch_violations,
        count_dev_tools_violations=payload.count_dev_tools_violations,
        enable_proctoring_warnings=payload.enable_proctoring_warnings,
    )
    db.add(draft_version)
    db.flush()

    quiz.current_version_id = draft_version.id
    db.commit()

    db.refresh(quiz)
    db.refresh(draft_version, ["questions"])

    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        course_code=quiz.course_code,
        description=quiz.description,
        status=quiz.status,
        created_by_id=quiz.created_by_id,
        current_version_id=quiz.current_version_id,
        draft_version=_serialize_version_response(draft_version),
        published_version=None,
        is_published=False,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    summary="Get quiz details and version status",
    description="Retrieve full quiz details, including draft version questions and published version if available.",
)
async def get_quiz(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizDetailResponse:
    """Retrieve quiz details and version snapshots."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    # Separate draft version and published version
    draft_v: Optional[QuizVersion] = None
    pub_v: Optional[QuizVersion] = None

    for v in sorted(quiz.versions, key=lambda x: x.version_number, reverse=True):
        if not v.is_published and draft_v is None:
            draft_v = v
        elif v.is_published and pub_v is None:
            pub_v = v

    is_pub = (pub_v is not None) and (quiz.status == QuizStatus.PUBLISHED)

    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        course_code=quiz.course_code,
        description=quiz.description,
        status=quiz.status,
        created_by_id=quiz.created_by_id,
        current_version_id=quiz.current_version_id,
        draft_version=_serialize_version_response(draft_v) if draft_v else None,
        published_version=_serialize_version_response(pub_v) if pub_v else None,
        is_published=is_pub,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


@router.put(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    summary="Update quiz draft settings",
    description="Update metadata and settings for the active draft. If quiz is currently published without a draft, spawns a new draft version without modifying published state.",
)
async def update_quiz(
    quiz_id: uuid.UUID,
    payload: QuizUpdateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizDetailResponse:
    """Update quiz metadata and draft version settings."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    # Ensure we are editing an active draft version
    draft = _ensure_active_draft_version(quiz, db)

    # Update top-level quiz metadata
    quiz.title = payload.title.strip()
    quiz.course_code = payload.course_code.strip()
    quiz.description = payload.description.strip() if payload.description else None

    # Update draft version settings
    draft.title = payload.title.strip()
    draft.description = payload.description.strip() if payload.description else None
    draft.opens_at = payload.opens_at
    draft.closes_at = payload.closes_at
    draft.duration_minutes = payload.duration_minutes
    draft.max_attempts = payload.max_attempts
    draft.allow_backtracking = payload.allow_backtracking
    draft.shuffle_questions = payload.shuffle_questions
    draft.shuffle_options = payload.shuffle_options
    draft.multi_answer_policy = payload.multi_answer_policy
    draft.tab_switch_limit = payload.tab_switch_limit
    draft.tab_switch_penalty_marks = payload.tab_switch_penalty_marks
    draft.max_proctoring_deduction = payload.max_proctoring_deduction
    draft.enable_copy_paste_restriction = payload.enable_copy_paste_restriction
    draft.count_copy_paste_violations = payload.count_copy_paste_violations
    draft.require_fullscreen = payload.require_fullscreen
    draft.count_fullscreen_exit_violations = payload.count_fullscreen_exit_violations
    draft.count_tab_switch_violations = payload.count_tab_switch_violations
    draft.count_dev_tools_violations = payload.count_dev_tools_violations
    draft.enable_proctoring_warnings = payload.enable_proctoring_warnings

    db.commit()
    db.refresh(quiz)
    db.refresh(draft, ["questions"])

    pub_v = next((v for v in quiz.versions if v.is_published), None)

    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        course_code=quiz.course_code,
        description=quiz.description,
        status=quiz.status,
        created_by_id=quiz.created_by_id,
        current_version_id=quiz.current_version_id,
        draft_version=_serialize_version_response(draft),
        published_version=_serialize_version_response(pub_v) if pub_v else None,
        is_published=(quiz.status == QuizStatus.PUBLISHED),
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


@router.post(
    "/{quiz_id}/questions",
    response_model=QuizVersionResponse,
    summary="Add questions from question bank",
    description="Deep clones selected reusable questions from the teacher's Question Bank into the quiz draft version.",
)
async def add_questions_to_draft(
    quiz_id: uuid.UUID,
    payload: AddQuestionsFromBankRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizVersionResponse:
    """Clone bank questions into the draft version."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    draft = _ensure_active_draft_version(quiz, db)

    # Fetch and verify bank questions
    bank_stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(
            Question.id.in_(payload.question_ids),
            Question.created_by_id == current_user.id,
            Question.quiz_version_id.is_(None),
        )
    )
    bank_questions = {q.id: q for q in db.scalars(bank_stmt).all()}

    # Check for unauthorized or nonexistent question IDs
    missing = [qid for qid in payload.question_ids if qid not in bank_questions]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"One or more selected questions ({len(missing)}) were not found in your Question Bank.",
        )

    # Determine current max order_index in draft
    current_orders = [q.order_index for q in draft.questions]
    next_order = max(current_orders, default=-1) + 1

    # Clone each selected question in the requested order
    for qid in payload.question_ids:
        bank_q = bank_questions[qid]
        cloned_q = Question(
            quiz_version_id=draft.id,
            created_by_id=current_user.id,
            question_type=bank_q.question_type,
            difficulty=bank_q.difficulty,
            prompt=bank_q.prompt,
            order_index=next_order,
            positive_marks=bank_q.positive_marks,
            negative_marks=bank_q.negative_marks,
        )
        db.add(cloned_q)
        db.flush()

        for opt in bank_q.options:
            cloned_opt = QuestionOption(
                question_id=cloned_q.id,
                option_text=opt.option_text,
                order_index=opt.order_index,
                is_correct=opt.is_correct,
            )
            db.add(cloned_opt)

        next_order += 1

    db.commit()
    db.refresh(draft)
    db.refresh(draft, ["questions"])

    return _serialize_version_response(draft)


@router.delete(
    "/{quiz_id}/questions/{question_id}",
    response_model=QuizVersionResponse,
    summary="Remove question from draft",
    description="Deletes a question from the draft version and normalizes the sequence order. Reusable bank question remains intact.",
)
async def remove_question_from_draft(
    quiz_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizVersionResponse:
    """Remove question from active draft version."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    draft = _ensure_active_draft_version(quiz, db)

    target_q = next((q for q in draft.questions if q.id == question_id), None)
    if not target_q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in draft quiz version.",
        )

    db.delete(target_q)
    db.flush()

    # Re-normalize remaining question orders
    remaining_questions = [q for q in draft.questions if q.id != question_id]
    remaining_questions.sort(key=lambda x: x.order_index)
    for idx, q in enumerate(remaining_questions):
        q.order_index = idx

    db.commit()
    db.refresh(draft)
    db.refresh(draft, ["questions"])

    return _serialize_version_response(draft)


@router.put(
    "/{quiz_id}/questions/order",
    response_model=QuizVersionResponse,
    summary="Reorder questions in draft",
    description="Updates the presentation sequence of questions in the active draft.",
)
async def reorder_draft_questions(
    quiz_id: uuid.UUID,
    payload: ReorderQuestionsRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizVersionResponse:
    """Update order_index of draft questions."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    draft = _ensure_active_draft_version(quiz, db)

    draft_questions_map = {q.id: q for q in draft.questions}
    if set(payload.question_ids) != set(draft_questions_map.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided question IDs must exactly match all questions present in the draft.",
        )

    for order_idx, qid in enumerate(payload.question_ids):
        draft_questions_map[qid].order_index = order_idx

    db.commit()
    db.refresh(draft)
    db.refresh(draft, ["questions"])

    return _serialize_version_response(draft)


@router.get(
    "/{quiz_id}/preview",
    response_model=QuizPreviewResponse,
    summary="Preview assessment before publishing",
    description="Displays pre-flight validation warnings, difficulty summary, total marks, and readiness status.",
)
async def preview_quiz(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuizPreviewResponse:
    """Pre-publish review endpoint for teachers."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    # Check draft first, fallback to published
    active_version = None
    for v in sorted(quiz.versions, key=lambda x: x.version_number, reverse=True):
        if not v.is_published:
            active_version = v
            break
    if not active_version and quiz.versions:
        active_version = quiz.versions[-1]

    if not active_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz has no versions configured.",
        )

    total_q, total_m, diff_breakdown = _calculate_version_metrics(active_version)
    validation_errors = _validate_version_for_publication(active_version)

    return QuizPreviewResponse(
        quiz_id=quiz.id,
        version_id=active_version.id,
        version_number=active_version.version_number,
        title=quiz.title,
        course_code=quiz.course_code,
        description=quiz.description,
        opens_at=active_version.opens_at,
        closes_at=active_version.closes_at,
        duration_minutes=active_version.duration_minutes,
        max_attempts=active_version.max_attempts,
        allow_backtracking=active_version.allow_backtracking,
        shuffle_questions=active_version.shuffle_questions,
        shuffle_options=active_version.shuffle_options,
        multi_answer_policy=active_version.multi_answer_policy,
        tab_switch_limit=active_version.tab_switch_limit,
        tab_switch_penalty_marks=float(active_version.tab_switch_penalty_marks),
        max_proctoring_deduction=float(active_version.max_proctoring_deduction) if active_version.max_proctoring_deduction is not None else 5.00,
        enable_copy_paste_restriction=active_version.enable_copy_paste_restriction,
        count_copy_paste_violations=active_version.count_copy_paste_violations,
        require_fullscreen=active_version.require_fullscreen,
        count_fullscreen_exit_violations=active_version.count_fullscreen_exit_violations,
        count_tab_switch_violations=active_version.count_tab_switch_violations,
        count_dev_tools_violations=active_version.count_dev_tools_violations,
        enable_proctoring_warnings=active_version.enable_proctoring_warnings,
        is_results_released=active_version.is_results_released,
        total_questions=total_q,
        total_marks=total_m,
        difficulty_breakdown=diff_breakdown,
        can_publish=(len(validation_errors) == 0),
        validation_errors=validation_errors,
        questions=[
            QuestionResponse(
                id=q.id,
                created_by_id=q.created_by_id,
                question_type=q.question_type,
                difficulty=q.difficulty,
                prompt=q.prompt,
                positive_marks=float(q.positive_marks),
                negative_marks=float(q.negative_marks),
                options=[
                    QuestionOptionResponse(
                        id=o.id,
                        option_text=o.option_text,
                        order_index=o.order_index,
                        is_correct=o.is_correct,
                    )
                    for o in (q.options or [])
                ],
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in (active_version.questions or [])
        ],
    )


@router.post(
    "/{quiz_id}/publish",
    response_model=PublishQuizResponse,
    summary="Publish quiz version",
    description="Validates and locks the active draft version as an immutable snapshot. Subsequent modifications will fork a new version.",
)
async def publish_quiz(
    quiz_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> PublishQuizResponse:
    """Validate and atomically publish quiz version snapshot."""
    stmt = (
        select(Quiz)
        .options(
            selectinload(Quiz.versions)
            .selectinload(QuizVersion.questions)
            .selectinload(Question.options)
        )
        .where(
            Quiz.id == quiz_id,
            Quiz.created_by_id == current_user.id,
            Quiz.is_archived.is_(False),
        )
    )
    quiz = db.scalar(stmt)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized.",
        )

    # Find the active draft version
    draft = next((v for v in quiz.versions if not v.is_published), None)
    if not draft:
        # Check if already published
        if quiz.status == QuizStatus.PUBLISHED:
            pub_v = next((v for v in quiz.versions if v.is_published), None)
            return PublishQuizResponse(
                success=True,
                message="Quiz is already published with immutable version lock.",
                quiz_id=quiz.id,
                published_version_id=pub_v.id if pub_v else quiz.current_version_id,
                version_number=pub_v.version_number if pub_v else 1,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active draft version found to publish.",
        )

    # Validate server-side publication rules
    validation_errors = _validate_version_for_publication(draft)
    if validation_errors:
        error_details = [{"field": e.field, "message": e.message} for e in validation_errors]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Cannot publish quiz: pre-publication validation failed.",
                "errors": error_details,
            },
        )

    # Atomically lock version and update quiz status
    draft.is_published = True
    quiz.status = QuizStatus.PUBLISHED
    quiz.current_version_id = draft.id

    db.commit()

    return PublishQuizResponse(
        success=True,
        message=f"Quiz version {draft.version_number} has been published and locked as immutable.",
        quiz_id=quiz.id,
        published_version_id=draft.id,
        version_number=draft.version_number,
    )
