"""Pydantic schemas for minimal admin portal and operational operations (DEC-022)."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.models.user import UserRole


class AdminOverviewStats(BaseModel):
    """Aggregate statistics for admin dashboard overview."""
    total_students: int = 0
    total_teachers: int = 0
    total_quizzes: int = 0
    published_quizzes: int = 0
    active_attempts: int = 0
    total_attempts: int = 0


class AdminActivityItem(BaseModel):
    """Recent system and assessment activity record."""
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str
    user_email: Optional[str] = None
    created_at: datetime


class AdminOverviewResponse(BaseModel):
    """Consolidated admin dashboard overview response."""
    stats: AdminOverviewStats
    recent_activity: List[AdminActivityItem]


class AdminUserListItem(BaseModel):
    """User directory record displayed in admin portal."""
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    prn: Optional[str] = None
    division: Optional[str] = None
    created_at: datetime


class AdminUserListResponse(BaseModel):
    """Paginated user directory listing."""
    total: int
    items: List[AdminUserListItem]
    page: int
    page_size: int


class AdminUserStatusUpdateRequest(BaseModel):
    """Payload for activating or deactivating a user account."""
    is_active: bool


class AdminAuditLogItem(BaseModel):
    """Audit log entry for administrative visibility."""
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    details: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime


class AdminAuditLogResponse(BaseModel):
    """Paginated audit events listing."""
    total: int
    items: List[AdminAuditLogItem]
    page: int
    page_size: int


class AdminBootstrapRequest(BaseModel):
    """Request payload for server-side administrator initial provisioning."""
    bootstrap_token: Optional[str] = None


class AdminResetStatusResponse(BaseModel):
    """Status report on guarded reset availability."""
    allow_destructive_reset: bool
    environment: str
    can_reset: bool
    warning_notice: str


class AdminDestructiveResetRequest(BaseModel):
    """Guarded reset confirmation payload."""
    confirmation_code: str = Field(
        ...,
        description="Explicit confirmation token; must strictly match 'CONFIRM_DELETE_ALL_TEST_DATA'",
    )


class AdminDestructiveResetResponse(BaseModel):
    """Result of executing the guarded test-data reset."""
    success: bool
    message: str
    cleared_records: Dict[str, int]
    executed_at: datetime


class AdminTeacherCreateRequest(BaseModel):
    """Payload for onboarding a faculty/teacher member."""
    email: str = Field(..., description="Institutional email of the faculty member")
    name: str = Field(..., min_length=2, description="Full name of the faculty member")
    password: str = Field(..., min_length=6, description="Initial temporary or default password")


class AdminUserPurgeRequest(BaseModel):
    """Guarded payload for cautiously purging a single user and all dependent records."""
    target_email: str = Field(..., description="Email address of the user to purge")
    admin_password: str = Field(..., description="Administrative security password or authorization token")


class AdminUserPurgeResponse(BaseModel):
    """Outcome of single user purge operation."""
    success: bool
    message: str
    purged_user_id: str
    purged_email: str
    cleared_records: Dict[str, int]
    executed_at: datetime


class AdminCleanWorkspaceRequest(BaseModel):
    """Guarded reset payload for rehearsal reset (deletes all students & attempts, keeping teachers & admins)."""
    confirmation_code: str = Field(
        ...,
        description="Explicit confirmation token; must strictly match 'CONFIRM_CLEAN_TEACHER_WORKSPACE'",
    )


class AdminCleanWorkspaceResponse(BaseModel):
    """Result of executing clean teacher workspace rehearsal reset."""
    success: bool
    message: str
    cleared_records: Dict[str, int]
    purged_students_count: int
    preserved_teachers_count: int
    executed_at: datetime

