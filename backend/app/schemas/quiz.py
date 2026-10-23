"""Pydantic schemas for Teacher Quiz Builder, settings, preview, and immutable publishing (DEC-006, DEC-008)."""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.quiz import QuizStatus, MultiAnswerPolicy
from app.models.question import QuestionDifficulty
from app.schemas.question import QuestionResponse


class DifficultyBreakdown(BaseModel):
    """Distribution count of questions by difficulty level."""
    easy: int = 0
    medium: int = 0
    hard: int = 0


class QuizCreateRequest(BaseModel):
    """Initial payload to create a new draft quiz and its version 1 settings."""
    title: str = Field(..., min_length=1, max_length=255, description="Quiz title")
    course_code: str = Field(..., min_length=1, max_length=64, description="Course / Module code")
    description: Optional[str] = Field(None, description="Assessment instructions or syllabus details")
    opens_at: datetime = Field(..., description="Availability start timestamp (UTC)")
    closes_at: datetime = Field(..., description="Availability end timestamp (UTC)")
    duration_minutes: int = Field(..., gt=0, le=1440, description="Per-attempt duration in minutes")
    max_attempts: int = Field(1, ge=1, le=10, description="Maximum attempts permitted per student")
    allow_backtracking: bool = Field(True, description="Whether students can navigate freely between questions")
    shuffle_questions: bool = Field(False, description="Randomize question sequence for each attempt")
    shuffle_options: bool = Field(False, description="Randomize option order for each question")
    multi_answer_policy: MultiAnswerPolicy = Field(
        MultiAnswerPolicy.ALL_OR_NOTHING,
        description="Scoring policy for questions with multiple correct options",
    )
    tab_switch_limit: int = Field(3, ge=0, description="Proctoring telemetry warning threshold")
    tab_switch_penalty_marks: float = Field(0.00, ge=0, description="Penalty deducted per excess tab switch")

    @model_validator(mode="after")
    def validate_schedule(self) -> "QuizCreateRequest":
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be strictly later than opens_at.")
        return self


class QuizUpdateRequest(QuizCreateRequest):
    """Payload to update quiz metadata and current draft version settings."""
    pass


class AddQuestionsFromBankRequest(BaseModel):
    """Select existing questions from the teacher's Question Bank to clone into the draft."""
    question_ids: List[uuid.UUID] = Field(..., min_length=1, description="Question IDs from bank to clone into draft")


class ReorderQuestionsRequest(BaseModel):
    """Ordered sequence of question IDs in the draft."""
    question_ids: List[uuid.UUID] = Field(..., min_length=1, description="Ordered list of draft question IDs")


class QuizVersionResponse(BaseModel):
    """Immutable version snapshot or draft assessment state."""
    id: uuid.UUID
    quiz_id: uuid.UUID
    version_number: int
    title: str
    description: Optional[str]
    is_published: bool
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    max_attempts: int
    allow_backtracking: bool
    shuffle_questions: bool
    shuffle_options: bool
    multi_answer_policy: MultiAnswerPolicy
    tab_switch_limit: int
    tab_switch_penalty_marks: float
    is_results_released: bool
    created_at: datetime
    questions: List[QuestionResponse] = []
    total_questions: int = 0
    total_marks: float = 0.0
    difficulty_breakdown: DifficultyBreakdown = Field(default_factory=DifficultyBreakdown)

    model_config = ConfigDict(from_attributes=True)


class QuizListItemResponse(BaseModel):
    """Summary of quiz for teacher dashboard."""
    id: uuid.UUID
    title: str
    course_code: str
    description: Optional[str]
    status: QuizStatus
    created_by_id: uuid.UUID
    current_version_id: Optional[uuid.UUID]
    version_number: int
    is_published: bool
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    total_questions: int
    total_marks: float
    difficulty_breakdown: DifficultyBreakdown = Field(default_factory=DifficultyBreakdown)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizListResponse(BaseModel):
    """Collection response for teacher quizzes."""
    items: List[QuizListItemResponse]
    total: int


class QuizDetailResponse(BaseModel):
    """Full quiz state including active draft version and published version."""
    id: uuid.UUID
    title: str
    course_code: str
    description: Optional[str]
    status: QuizStatus
    created_by_id: uuid.UUID
    current_version_id: Optional[uuid.UUID]
    draft_version: Optional[QuizVersionResponse] = None
    published_version: Optional[QuizVersionResponse] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrePublishValidationError(BaseModel):
    """Pre-publish validation error detail."""
    field: str
    message: str


class QuizPreviewResponse(BaseModel):
    """Teacher pre-publication review and readiness validation."""
    quiz_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    title: str
    course_code: str
    description: Optional[str]
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    max_attempts: int
    allow_backtracking: bool
    shuffle_questions: bool
    shuffle_options: bool
    multi_answer_policy: MultiAnswerPolicy
    tab_switch_limit: int
    tab_switch_penalty_marks: float
    is_results_released: bool
    total_questions: int
    total_marks: float
    difficulty_breakdown: DifficultyBreakdown
    can_publish: bool
    validation_errors: List[PrePublishValidationError] = []
    questions: List[QuestionResponse] = []


class PublishQuizResponse(BaseModel):
    """Response returned upon successful immutable publication."""
    success: bool
    message: str
    quiz_id: uuid.UUID
    published_version_id: uuid.UUID
    version_number: int
