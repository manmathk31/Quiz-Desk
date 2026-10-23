"""Teacher Results, Grading Adjustments, Result Release, and Reporting schemas (DEC-010, Phase 7)."""
from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuizResultSummaryResponse(BaseModel):
    """Aggregate KPI metrics and result release status for a teacher's quiz."""
    model_config = ConfigDict(from_attributes=True)

    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    version_number: int
    is_published: bool
    is_results_released: bool
    results_released_at: Optional[datetime] = None
    total_enrolled: int
    total_attempts: int
    submitted_count: int
    in_progress_count: int
    average_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    total_possible_marks: float


class AttemptListItemResponse(BaseModel):
    """Summarized assessment attempt for teacher dashboard tables."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_email: str
    student_prn: str
    student_division: str
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    total_score: Optional[float] = None
    grading_status: str
    tab_switch_count: int
    violation_count: int = 0
    proctoring_deduction: float = 0.0
    is_finalized: bool
    adjustment_count: int = 0


class AttemptListResponse(BaseModel):
    """Paginated list of student assessment attempts for a quiz."""
    items: List[AttemptListItemResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class QuestionOptionResultDetail(BaseModel):
    """Option detail including correctness for teacher inspection."""
    id: uuid.UUID
    option_text: str
    order_index: int
    is_correct: bool


class QuestionResultDetail(BaseModel):
    """Detailed question response and scoring breakdown for a specific attempt."""
    question_id: uuid.UUID
    prompt: str
    question_type: str
    order_index: int
    positive_marks: float
    negative_marks: float
    awarded_marks: Optional[float] = None
    selected_option_ids: List[str]
    options: List[QuestionOptionResultDetail]


class GradeAdjustmentItem(BaseModel):
    """Historical manual score adjustment audit item."""
    id: uuid.UUID
    previous_score: float
    new_score: float
    reason: str
    adjusted_by_name: str
    created_at: datetime


class TelemetryEventItem(BaseModel):
    """Telemetry focus loss / tab switch event."""
    id: uuid.UUID
    event_type: str
    client_event_id: Optional[str] = None
    event_timestamp: datetime
    event_data: Optional[Dict[str, Any]] = None


class AttemptDetailResponse(BaseModel):
    """Full attempt diagnostic view for teacher grading review and adjustment."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    version_number: int
    student_name: str
    student_email: str
    student_prn: str
    student_division: str
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    deadline_at: datetime
    total_score: Optional[float] = None
    max_possible_marks: float
    grading_status: str
    tab_switch_count: int
    violation_count: int = 0
    proctoring_deduction: float = 0.0
    effective_policy: Optional[Dict[str, Any]] = None
    violation_breakdown: Optional[Dict[str, int]] = None
    is_finalized: bool
    questions: List[QuestionResultDetail]
    adjustments: List[GradeAdjustmentItem] = Field(default_factory=list)
    telemetry_events: List[TelemetryEventItem] = Field(default_factory=list)


class GradeAdjustmentRequest(BaseModel):
    """Request payload for manual grade modification (DEC-010)."""
    new_score: float = Field(..., ge=0.0, description="New total score for the attempt")
    reason: str = Field(..., min_length=3, max_length=1000, description="Mandatory reason for audit trail")

    @field_validator("reason")
    @classmethod
    def validate_reason_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("Reason must be at least 3 characters of non-whitespace text.")
        return cleaned


class ReleaseResultsResponse(BaseModel):
    """Response confirming student result release."""
    quiz_id: uuid.UUID
    version_number: int
    is_results_released: bool
    results_released_at: datetime
    message: str


class StudentAttemptResultResponse(BaseModel):
    """Authoritative student-visible score after teacher result release (DEC-010, DEC-019)."""
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    total_score: float
    proctoring_deduction: float = 0.0
    violation_count: int = 0
    max_possible_score: float
    grading_status: str
    tab_switch_count: int
    is_results_released: bool
