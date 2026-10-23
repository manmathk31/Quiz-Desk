"""Student active assessment delivery, autosave, telemetry, and submission schemas (DEC-008, DEC-009, DEC-010)."""
from datetime import datetime
import uuid
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.attempt import AttemptStatus
from app.models.question import QuestionType


class StudentQuizSummary(BaseModel):
    """Sanitized summary of an assigned quiz for the student dashboard."""
    model_config = ConfigDict(from_attributes=True)

    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    description: Optional[str] = None
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    max_attempts: int
    attempts_taken: int
    active_attempt_id: Optional[uuid.UUID] = None
    availability_status: str  # "UPCOMING", "OPEN", "CLOSED", "COMPLETED"
    status_message: str


class StudentQuizListResponse(BaseModel):
    """List of quizzes assigned to authenticated student."""
    items: List[StudentQuizSummary]
    total: int


class AttemptStartResponse(BaseModel):
    """Metadata returned when an assessment attempt is started or resumed."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_version_id: uuid.UUID
    attempt_number: int
    status: AttemptStatus
    started_at: datetime
    deadline_at: datetime
    remaining_seconds: int
    is_resumed: bool


class SanitizedOptionResponse(BaseModel):
    """Sanitized option choice. Never includes is_correct flag or scoring keys."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    option_text: str
    order_index: int


class SavedAnswerResponse(BaseModel):
    """Saved answer response attached to question during assessment."""
    model_config = ConfigDict(from_attributes=True)

    selected_option_ids: List[str]
    is_marked_for_review: bool
    saved_at: datetime


class SanitizedQuestionResponse(BaseModel):
    """Sanitized question payload. Conceals answer keys and internal explanations."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt: str
    question_type: QuestionType
    order_index: int
    positive_marks: float
    negative_marks: float
    options: List[SanitizedOptionResponse]
    saved_answer: Optional[SavedAnswerResponse] = None


class AttemptContentResponse(BaseModel):
    """Complete sanitized assessment payload delivered to student."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    status: AttemptStatus
    started_at: datetime
    deadline_at: datetime
    server_time: datetime
    remaining_seconds: int
    is_finalized: bool
    tab_switch_count: int
    tab_switch_limit: int
    allow_backtracking: bool
    questions: List[SanitizedQuestionResponse]


class AnswerSaveRequest(BaseModel):
    """Payload to save an individual question answer."""
    selected_option_ids: List[str] = Field(default_factory=list)
    is_marked_for_review: bool = False
    client_timestamp: Optional[datetime] = None


class AnswerSaveResponse(BaseModel):
    """Acknowledgment of answer autosave."""
    success: bool
    saved_at: datetime
    is_marked_for_review: bool
    selected_option_ids: List[str]


class TelemetryEventRequest(BaseModel):
    """Client proctoring observation event (e.g. tab switch or window blur)."""
    event_type: str = Field(default="tab_switch", max_length=64)
    event_data: Optional[dict[str, Any]] = None


class TelemetryEventResponse(BaseModel):
    """Acknowledgment and warning threshold status."""
    tab_switch_count: int
    limit_exceeded: bool
    tab_switch_limit: int


class AttemptSubmissionResponse(BaseModel):
    """Confirmation returned when an attempt is submitted or finalized."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    status: AttemptStatus
    submitted_at: datetime
    is_finalized: bool
    total_score: Optional[float] = None
    is_results_released: bool
    message: str
