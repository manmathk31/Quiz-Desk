"""Question Bank API endpoints for teachers (DEC-006, DEC-013)."""
import math
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.core.auth import require_faculty
from app.core.database import get_db
from app.models.user import User
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.schemas.question import (
    QuestionCreateRequest,
    QuestionUpdateRequest,
    QuestionResponse,
    QuestionListResponse,
    CSVPreviewResponse,
    CSVImportResponse,
    CSVRowErrorResponse,
    ParsedQuestionResponse,
    ParsedOptionResponse,
)
from app.services.csv_parser import parse_and_validate_question_csv, MAX_FILE_SIZE_BYTES

router = APIRouter(prefix="/question-bank", tags=["Question Bank"])

CSV_SAMPLE_TEMPLATE = (
    "question_type,difficulty,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
    'single_choice,medium,"What is the time complexity of binary search on a sorted array?",O(1),O(n),O(log n),O(n^2),C,2.0,0.5\n'
    'multiple_choice,hard,"Which of the following are linear data structures?",Array,Stack,Tree,Queue,"A, B, D",3.0,1.0\n'
    'true_false,easy,"An AVL tree is a self-balancing binary search tree.",True,False,,,A,1.0,0.0\n'
    'single_choice,easy,"Which protocol is used for secure web browsing?",HTTP,FTP,HTTPS,SSH,C,1.0,0.25\n'
    'true_false,medium,"Python strings are mutable.",True,False,,,B,1.0,0.0\n'
)


@router.get(
    "/csv/template",
    summary="Download question CSV template",
    description="Provides a documented CSV template with valid examples for single MCQ, multi MCQ, and True/False.",
)
async def download_csv_template(
    _current_user: User = Depends(require_faculty),
):
    """Return downloadable sample CSV template."""
    return Response(
        content=CSV_SAMPLE_TEMPLATE,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="quizdesk_question_bank_template.csv"',
        },
    )


@router.get(
    "",
    response_model=QuestionListResponse,
    summary="List teacher's question bank",
    description="Retrieve paginated reusable draft questions owned by the authenticated teacher.",
)
async def list_question_bank(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    difficulty: Optional[QuestionDifficulty] = Query(None, description="Filter by question difficulty"),
    search: Optional[str] = Query(None, description="Search prompt substring"),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> QuestionListResponse:
    """List questions in the teacher's bank with pagination and filters."""
    query = (
        select(Question)
        .options(selectinload(Question.options))
        .where(
            Question.created_by_id == current_user.id,
            Question.quiz_version_id.is_(None),
        )
    )

    if question_type:
        query = query.where(Question.question_type == question_type)

    if difficulty:
        query = query.where(Question.difficulty == difficulty)

    if search and search.strip():
        search_filter = f"%{search.strip()}%"
        query = query.where(Question.prompt.ilike(search_filter))

    # Count total matching items
    count_query = (
        select(func.count())
        .select_from(Question)
        .where(
            Question.created_by_id == current_user.id,
            Question.quiz_version_id.is_(None),
        )
    )
    if question_type:
        count_query = count_query.where(Question.question_type == question_type)
    if difficulty:
        count_query = count_query.where(Question.difficulty == difficulty)
    if search and search.strip():
        count_query = count_query.where(Question.prompt.ilike(f"%{search.strip()}%"))

    total = db.scalar(count_query) or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Apply ordering and pagination
    offset = (page - 1) * page_size
    query = query.order_by(Question.created_at.desc()).offset(offset).limit(page_size)

    items = db.scalars(query).all()

    return QuestionListResponse(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question manually",
    description="Add a new reusable question to the teacher's question bank.",
)
async def create_question(
    payload: QuestionCreateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> Question:
    """Manually create a question with validated options in teacher's bank."""
    question = Question(
        created_by_id=current_user.id,
        quiz_version_id=None,
        question_type=payload.question_type,
        difficulty=payload.difficulty,
        prompt=payload.prompt.strip(),
        positive_marks=payload.positive_marks,
        negative_marks=payload.negative_marks,
    )
    db.add(question)
    db.flush()  # Generate question ID

    for opt_idx, opt_data in enumerate(payload.options):
        option = QuestionOption(
            question_id=question.id,
            option_text=opt_data.option_text.strip(),
            order_index=opt_data.order_index if opt_data.order_index else opt_idx,
            is_correct=opt_data.is_correct,
        )
        db.add(option)

    db.commit()
    db.refresh(question)

    # Eagerly load options
    db.refresh(question, ["options"])
    return question


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Get single question details",
    description="Retrieve a single question from the teacher's question bank.",
)
async def get_question(
    question_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> Question:
    """Retrieve single bank question with options."""
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(
            Question.id == question_id,
            Question.created_by_id == current_user.id,
            Question.quiz_version_id.is_(None),
        )
    )
    question = db.scalar(stmt)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in your question bank.",
        )
    return question


@router.put(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Update question",
    description="Update a reusable draft question and replace its option set.",
)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdateRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> Question:
    """Update bank question and options transactionally."""
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .where(
            Question.id == question_id,
            Question.created_by_id == current_user.id,
            Question.quiz_version_id.is_(None),
        )
    )
    question = db.scalar(stmt)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in your question bank.",
        )

    question.prompt = payload.prompt.strip()
    question.question_type = payload.question_type
    question.difficulty = payload.difficulty
    question.positive_marks = payload.positive_marks
    question.negative_marks = payload.negative_marks

    # Replace options cleanly
    question.options.clear()
    db.flush()

    for opt_idx, opt_data in enumerate(payload.options):
        option = QuestionOption(
            question_id=question.id,
            option_text=opt_data.option_text.strip(),
            order_index=opt_data.order_index if opt_data.order_index else opt_idx,
            is_correct=opt_data.is_correct,
        )
        db.add(option)

    db.commit()
    db.refresh(question)
    db.refresh(question, ["options"])
    return question


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete question",
    description="Remove a question from the teacher's question bank.",
)
async def delete_question(
    question_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
):
    """Delete a reusable bank question and its options."""
    stmt = select(Question).where(
        Question.id == question_id,
        Question.created_by_id == current_user.id,
        Question.quiz_version_id.is_(None),
    )
    question = db.scalar(stmt)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in your question bank.",
        )

    db.delete(question)
    db.commit()
    return None


@router.post(
    "/csv/preview",
    response_model=CSVPreviewResponse,
    summary="Preview and validate question CSV or XLSX",
    description="Upload a CSV or XLSX file for dry-run parsing and validation. Returns parsed questions and line-by-line errors without writing to the database.",
)
async def preview_question_csv(
    file: UploadFile = File(...),
    _current_user: User = Depends(require_faculty),
) -> CSVPreviewResponse:
    """Dry-run validation of uploaded CSV or XLSX file."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    result = parse_and_validate_question_csv(content, filename=file.filename)

    return CSVPreviewResponse(
        is_valid=result.is_valid,
        total_rows=result.total_rows,
        valid_count=result.valid_count,
        error_count=result.error_count,
        questions=[
            ParsedQuestionResponse(
                row_number=q.row_number,
                question_type=q.question_type,
                difficulty=q.difficulty,
                prompt=q.prompt,
                positive_marks=q.positive_marks,
                negative_marks=q.negative_marks,
                options=[
                    ParsedOptionResponse(
                        option_text=o.option_text,
                        order_index=o.order_index,
                        is_correct=o.is_correct,
                    )
                    for o in q.options
                ],
            )
            for q in result.questions
        ],
        errors=[
            CSVRowErrorResponse(
                row_number=e.row_number,
                column=e.column,
                message=e.message,
            )
            for e in result.errors
        ],
    )


@router.post(
    "/csv/import",
    response_model=CSVImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import validated question CSV or XLSX",
    description="Re-validates and transactionally persists questions from an uploaded CSV or XLSX into the teacher's question bank. Rejects all rows if any validation error is detected.",
)
async def import_question_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> CSVImportResponse:
    """All-or-nothing transactional import of CSV/XLSX questions into question bank."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    result = parse_and_validate_question_csv(content, filename=file.filename)

    if not result.is_valid:
        error_messages = [f"Row {e.row_number} [{e.column or 'file'}]: {e.message}" for e in result.errors[:5]]
        if len(result.errors) > 5:
            error_messages.append(f"...and {len(result.errors) - 5} more error(s)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "CSV validation failed. Please fix all errors and re-upload.",
                "error_count": result.error_count,
                "sample_errors": error_messages,
                "errors": [
                    {"row_number": e.row_number, "column": e.column, "message": e.message}
                    for e in result.errors
                ],
            },
        )

    created_ids: list[uuid.UUID] = []

    try:
        for q_item in result.questions:
            question = Question(
                created_by_id=current_user.id,
                quiz_version_id=None,
                question_type=q_item.question_type,
                difficulty=q_item.difficulty,
                prompt=q_item.prompt,
                positive_marks=q_item.positive_marks,
                negative_marks=q_item.negative_marks,
            )
            db.add(question)
            db.flush()
            created_ids.append(question.id)

            for opt_item in q_item.options:
                option = QuestionOption(
                    question_id=question.id,
                    option_text=opt_item.option_text,
                    order_index=opt_item.order_index,
                    is_correct=opt_item.is_correct,
                )
                db.add(option)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist question batch: {str(e)}",
        )

    return CSVImportResponse(
        success=True,
        imported_count=len(created_ids),
        message=f"Successfully imported {len(created_ids)} questions into your question bank.",
        question_ids=created_ids,
    )
