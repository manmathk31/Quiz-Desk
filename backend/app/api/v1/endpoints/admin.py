"""Admin Portal and operational API endpoints (DEC-022)."""
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.auth import decode_supabase_jwt, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminAuditLogResponse,
    AdminBootstrapRequest,
    AdminDestructiveResetRequest,
    AdminDestructiveResetResponse,
    AdminOverviewResponse,
    AdminResetStatusResponse,
    AdminUserListResponse,
    AdminUserStatusUpdateRequest,
)
from app.schemas.user import UserResponse
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.post(
    "/bootstrap",
    response_model=UserResponse,
    summary="Bootstrap administrator account",
    description="Provision or promote the initial administrator account matching ADMIN_EMAIL configured in the server environment.",
)
async def bootstrap_admin(
    request: Request,
    body: AdminBootstrapRequest = AdminBootstrapRequest(),
    db: Session = Depends(get_db),
) -> User:
    """
    Bootstrap the initial administrator account using a verified Supabase JWT.
    Enforces server-authoritative matching against settings.ADMIN_EMAIL and settings.ADMIN_BOOTSTRAP_TOKEN.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, sep, token = auth_header.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme; Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_supabase_jwt(token.strip())
    admin_user = admin_service.bootstrap_admin_user(
        db=db,
        token_payload=payload,
        bootstrap_token=body.bootstrap_token,
    )
    return admin_user


@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Get admin dashboard overview metrics",
    description="Retrieve bounded summary metrics and recent activity for the operational dashboard.",
)
async def get_overview(
    _current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    return admin_service.get_admin_overview(db)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List users directory",
    description="Search and view basic user profiles, assigned roles, and student PRNs.",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or PRN"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    _current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    return admin_service.list_admin_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Update user active status",
    description="Activate or deactivate a user account. Administrators cannot deactivate their own account.",
)
async def update_user_status(
    user_id: uuid.UUID,
    body: AdminUserStatusUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return admin_service.update_user_status(
        db=db,
        admin_user=current_admin,
        target_user_id=user_id,
        is_active=body.is_active,
    )


@router.get(
    "/audit-logs",
    response_model=AdminAuditLogResponse,
    summary="View system audit trail",
    description="Paginated inspection of security and administrative audit events.",
)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    _current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminAuditLogResponse:
    return admin_service.list_audit_logs(
        db=db,
        page=page,
        page_size=page_size,
        action=action,
    )


@router.get(
    "/reset-status",
    response_model=AdminResetStatusResponse,
    summary="Check guarded reset status",
    description="Check whether the destructive test data reset is enabled in the current environment.",
)
async def get_reset_status(
    _current_admin: User = Depends(require_admin),
) -> AdminResetStatusResponse:
    env_clean = (settings.ENVIRONMENT or "").strip().lower()
    can_reset = (env_clean != "production") and settings.ALLOW_DESTRUCTIVE_RESET
    warning = (
        "DANGER: Destructive reset permanently deletes all quizzes, versions, questions, assignments, and student attempts. This operation cannot be undone."
        if can_reset
        else "Destructive reset is disabled or blocked in this environment."
    )
    return AdminResetStatusResponse(
        allow_destructive_reset=settings.ALLOW_DESTRUCTIVE_RESET,
        environment=settings.ENVIRONMENT,
        can_reset=can_reset,
        warning_notice=warning,
    )


@router.post(
    "/reset-test-data",
    response_model=AdminDestructiveResetResponse,
    summary="Execute guarded destructive test data reset",
    description="Atomically clear test assessment data in non-production environments with mandatory confirmation.",
)
async def reset_test_data(
    body: AdminDestructiveResetRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return admin_service.execute_destructive_test_data_reset(
        db=db,
        admin_user=current_admin,
        confirmation_code=body.confirmation_code,
    )
