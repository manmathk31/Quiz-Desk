"""Pydantic schemas for Student Roster imports, assignments, and eligibility (DEC-007, Phase 5)."""
from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RosterRowErrorResponse(BaseModel):
    """Validation error at a specific row/column in the roster file."""
    row_number: int
    column: Optional[str] = None
    message: str


class RosterPreviewItemResponse(BaseModel):
    """Evaluated preview candidate row."""
    row_number: int
    prn: str
    name: str
    email: str
    division: str
    assignment_status: str  # "new", "already_assigned", "conflict"
    match_status: str       # "matched", "unregistered", "pending_profile", "conflict"
    matched_user_id: Optional[uuid.UUID] = None
    conflict_reason: Optional[str] = None
    is_currently_active: Optional[bool] = None


class RosterPreviewResponse(BaseModel):
    """Dry-run preview summary and line-by-line validation results."""
    total_rows: int
    valid_rows: int
    new_assignments_count: int
    already_assigned_count: int
    conflicts_count: int
    matched_count: int
    unregistered_count: int
    pending_profile_count: int
    can_confirm: bool
    items: List[RosterPreviewItemResponse] = []
    errors: List[RosterRowErrorResponse] = []


class RosterImportSummaryResponse(BaseModel):
    """Outcome of confirmed roster import."""
    imported_count: int
    already_assigned_count: int
    matched_accounts_count: int
    unregistered_count: int
    message: str


class AssignmentResponse(BaseModel):
    """Student quiz assignment view with account matching and status."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quiz_id: uuid.UUID
    student_prn: str
    student_name: str
    student_email: str
    division: str
    assigned_student_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime
    revoked_at: Optional[datetime] = None
    match_status: str = "unregistered"
    has_attempts: bool = False


class AssignmentSummaryStats(BaseModel):
    """Aggregate statistics for a quiz roster."""
    total_assigned: int
    active_count: int
    revoked_count: int
    matched_count: int
    unregistered_count: int
    divisions: List[str]


class AssignmentListResponse(BaseModel):
    """Paginated assignment response with summary counts."""
    items: List[AssignmentResponse]
    total_count: int
    page: int
    page_size: int
    summary: AssignmentSummaryStats


import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class AssignmentCreateRequest(BaseModel):
    """Request schema for manually adding a single student assignment."""
    prn: str = Field(..., min_length=1, max_length=64, description="Student institutional PRN")
    name: str = Field(..., min_length=1, max_length=255, description="Student full name")
    email: str = Field(..., min_length=3, max_length=255, description="Student institutional email")
    division: str = Field(..., min_length=1, max_length=32, description="Class division / batch")

    @field_validator("prn", "name", "division")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not EMAIL_REGEX.match(s):
            raise ValueError(f"Invalid email format: '{v}'")
        return s



class AssignmentStatusUpdateRequest(BaseModel):
    """Request to revoke or reactivate an assignment."""
    is_active: bool = Field(..., description="True to activate, False to revoke access")


class StudentEligibilityResponse(BaseModel):
    """Sanitized student assessment eligibility confirmation."""
    is_eligible: bool
    quiz_id: uuid.UUID
    quiz_title: str
    course_code: str
    quiz_version_id: uuid.UUID
    version_number: int
    assignment_id: uuid.UUID
    student_prn: str
    student_name: str
    student_email: str
    division: str
    opens_at: datetime
    closes_at: datetime
    duration_minutes: int
    max_attempts: int
    is_open: bool
    status_message: str
