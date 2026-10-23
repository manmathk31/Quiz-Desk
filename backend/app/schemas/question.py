"""Pydantic schemas for Question Bank and CSV Import (DEC-006)."""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.question import QuestionType, QuestionDifficulty


# Option schemas
class QuestionOptionBase(BaseModel):
    option_text: str = Field(..., min_length=1, description="Option answer text")
    order_index: int = Field(0, ge=0, description="Display order index")
    is_correct: bool = Field(False, description="Whether this choice is correct")


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionResponse(QuestionOptionBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# Question schemas
class QuestionCreateRequest(BaseModel):
    question_type: QuestionType = Field(
        QuestionType.SINGLE_CHOICE, description="Question type"
    )
    difficulty: QuestionDifficulty = Field(
        QuestionDifficulty.MEDIUM, description="Difficulty level (easy, medium, hard)"
    )
    prompt: str = Field(..., min_length=1, description="Question prompt / statement")
    positive_marks: float = Field(1.0, gt=0, description="Marks awarded for correct answer")
    negative_marks: float = Field(0.0, ge=0, description="Penalty deducted for incorrect answer")
    options: List[QuestionOptionCreate] = Field(
        ..., min_length=2, description="List of at least two answer options"
    )

    @model_validator(mode="after")
    def validate_options_for_type(self) -> "QuestionCreateRequest":
        q_type = self.question_type
        opts = self.options

        if len(opts) < 2:
            raise ValueError("A question must define at least two options.")

        # Check for duplicate option texts
        texts = [o.option_text.strip().lower() for o in opts]
        if len(texts) != len(set(texts)):
            raise ValueError("All options for a question must have unique text.")

        correct_count = sum(1 for o in opts if o.is_correct)

        if q_type == QuestionType.SINGLE_CHOICE:
            if correct_count != 1:
                raise ValueError("Single-choice question must have exactly one correct option.")
        elif q_type == QuestionType.MULTIPLE_CHOICE:
            if correct_count < 1:
                raise ValueError("Multiple-choice question must have at least one correct option.")
        elif q_type == QuestionType.TRUE_FALSE:
            if len(opts) != 2:
                raise ValueError("True/False question must define exactly two options.")
            if correct_count != 1:
                raise ValueError("True/False question must have exactly one correct option.")

        return self


class QuestionUpdateRequest(QuestionCreateRequest):
    """Update payload replaces question fields and its option set."""
    pass


class QuestionResponse(BaseModel):
    id: uuid.UUID
    created_by_id: Optional[uuid.UUID]
    question_type: QuestionType
    difficulty: QuestionDifficulty
    prompt: str
    positive_marks: float
    negative_marks: float
    options: List[QuestionOptionResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionListResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# CSV / Spreadsheet Preview and Import Schemas
class CSVRowErrorResponse(BaseModel):
    row_number: int
    column: Optional[str] = None
    message: str


class ParsedOptionResponse(BaseModel):
    option_text: str
    order_index: int
    is_correct: bool


class ParsedQuestionResponse(BaseModel):
    row_number: int
    question_type: QuestionType
    difficulty: QuestionDifficulty
    prompt: str
    positive_marks: float
    negative_marks: float
    options: List[ParsedOptionResponse]


class CSVPreviewResponse(BaseModel):
    is_valid: bool
    total_rows: int
    valid_count: int
    error_count: int
    questions: List[ParsedQuestionResponse]
    errors: List[CSVRowErrorResponse]


class CSVImportResponse(BaseModel):
    success: bool
    imported_count: int
    message: str
    question_ids: List[uuid.UUID]
