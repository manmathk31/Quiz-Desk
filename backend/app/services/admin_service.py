"""Admin service handling platform metrics, user directory, audit trails, bootstrapping, and guarded resets (DEC-022)."""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.attempt import AttemptAnswer, AttemptTelemetryEvent, QuizAttempt, AttemptStatus
from app.models.audit import AuditEvent, GradeAdjustment, ImportJob
from app.models.base import utc_now
from app.models.question import Question, QuestionOption
from app.models.quiz import Quiz, QuizStatus, QuizVersion
from app.models.roster import QuizAssignment
from app.models.user import StudentProfile, User, UserRole
from app.schemas.admin import (
    AdminActivityItem,
    AdminAuditLogItem,
    AdminAuditLogResponse,
    AdminOverviewResponse,
    AdminOverviewStats,
    AdminUserListItem,
    AdminUserListResponse,
)


def get_admin_overview(db: Session) -> AdminOverviewResponse:
    """
    Produce summary operational metrics for the administrator overview.
    Uses bounded aggregate counts on indexed columns to avoid full-table scans.
    """
    total_students = (
        db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar() or 0
    )
    total_teachers = (
        db.query(func.count(User.id)).filter(User.role == UserRole.TEACHER).scalar() or 0
    )
    total_quizzes = db.query(func.count(Quiz.id)).scalar() or 0
    published_quizzes = (
        db.query(func.count(Quiz.id)).filter(Quiz.status == QuizStatus.PUBLISHED).scalar() or 0
    )
    active_attempts = (
        db.query(func.count(QuizAttempt.id))
        .filter(QuizAttempt.status == AttemptStatus.IN_PROGRESS)
        .scalar()
        or 0
    )
    total_attempts = db.query(func.count(QuizAttempt.id)).scalar() or 0

    stats = AdminOverviewStats(
        total_students=total_students,
        total_teachers=total_teachers,
        total_quizzes=total_quizzes,
        published_quizzes=published_quizzes,
        active_attempts=active_attempts,
        total_attempts=total_attempts,
    )

    # Fetch last 10 audit events with outerjoin to user for actor email
    recent_query = (
        select(AuditEvent, User.email)
        .outerjoin(User, AuditEvent.user_id == User.id)
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
    )
    recent_records = db.execute(recent_query).all()

    recent_activity: List[AdminActivityItem] = [
        AdminActivityItem(
            id=event.id,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            user_email=email,
            created_at=event.created_at,
        )
        for event, email in recent_records
    ]

    return AdminOverviewResponse(stats=stats, recent_activity=recent_activity)


def list_admin_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
) -> AdminUserListResponse:
    """
    Paginated user directory query with optional search on name/email/PRN and role filtering.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    stmt = (
        select(
            User,
            StudentProfile.prn,
            StudentProfile.current_division,
        )
        .outerjoin(StudentProfile, User.id == StudentProfile.user_id)
    )

    if role:
        stmt = stmt.where(User.role == role)

    if search:
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
                StudentProfile.prn.ilike(search_pattern),
            )
        )

    # Count total matching rows
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.scalar(count_stmt) or 0

    # Paginate
    stmt = (
        stmt.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(stmt).all()

    items: List[AdminUserListItem] = []
    for user, prn, division in rows:
        items.append(
            AdminUserListItem(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                is_active=user.is_active,
                prn=prn,
                division=division,
                created_at=user.created_at,
            )
        )

    return AdminUserListResponse(
        total=total_count,
        items=items,
        page=page,
        page_size=page_size,
    )


def update_user_status(
    db: Session,
    admin_user: User,
    target_user_id: uuid.UUID,
    is_active: bool,
) -> User:
    """
    Activate or deactivate a user account.
    Prevents self-deactivation by administrators.
    Maintains full audit trail.
    """
    if admin_user.id == target_user_id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account.",
        )

    target_user = db.get(User, target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {target_user_id} not found.",
        )

    previous_status = target_user.is_active
    target_user.is_active = is_active

    # Log audit event
    audit = AuditEvent(
        user_id=admin_user.id,
        action="user.status_updated",
        entity_type="user",
        entity_id=str(target_user.id),
        details={
            "target_email": target_user.email,
            "previous_is_active": previous_status,
            "new_is_active": is_active,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(target_user)

    return target_user


def list_audit_logs(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
) -> AdminAuditLogResponse:
    """
    Paginated administrative view of tamper-evident audit events.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    stmt = select(AuditEvent, User.email).outerjoin(User, AuditEvent.user_id == User.id)

    if action:
        stmt = stmt.where(AuditEvent.action == action.strip())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.scalar(count_stmt) or 0

    stmt = (
        stmt.order_by(AuditEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.execute(stmt).all()

    items: List[AdminAuditLogItem] = [
        AdminAuditLogItem(
            id=event.id,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            user_id=event.user_id,
            user_email=email,
            details=event.details,
            ip_address=event.ip_address,
            created_at=event.created_at,
        )
        for event, email in rows
    ]

    return AdminAuditLogResponse(
        total=total_count,
        items=items,
        page=page,
        page_size=page_size,
    )


def execute_destructive_test_data_reset(
    db: Session,
    admin_user: User,
    confirmation_code: str,
) -> dict:
    """
    Atomically clears test assessment data in designated non-production environments.

    Guards enforced:
    1. Rejects if ENVIRONMENT is 'production' (strictly forbidden).
    2. Rejects if ALLOW_DESTRUCTIVE_RESET is not True (disabled by default).
    3. Rejects if confirmation_code is not strictly 'CONFIRM_DELETE_ALL_TEST_DATA'.
    4. Authenticated admin only.
    5. Preserves all User accounts (including Admin), passwords, credentials, and audit records.
    6. Strictly executed in transactional dependency order to prevent orphaned records.
    7. Creates tamper-evident AuditEvent before committing.
    """
    env_normalized = (settings.ENVIRONMENT or "").strip().lower()
    if env_normalized == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Destructive reset is strictly forbidden in production environment.",
        )

    if not settings.ALLOW_DESTRUCTIVE_RESET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Destructive reset is disabled by system configuration (ALLOW_DESTRUCTIVE_RESET=false).",
        )

    if confirmation_code != "CONFIRM_DELETE_ALL_TEST_DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation code. Must be strictly 'CONFIRM_DELETE_ALL_TEST_DATA'.",
        )

    # Execute transactional cleanup in strict foreign-key dependency order
    cleared_records: Dict[str, int] = {}

    try:
        # 1. Active student attempt answers & telemetry
        cleared_records["attempt_answers"] = db.query(AttemptAnswer).delete()
        cleared_records["attempt_telemetry_events"] = db.query(AttemptTelemetryEvent).delete()

        # 2. Grade adjustments & student quiz attempts
        cleared_records["grade_adjustments"] = db.query(GradeAdjustment).delete()
        cleared_records["quiz_attempts"] = db.query(QuizAttempt).delete()

        # 3. Quiz assignments & import jobs
        cleared_records["quiz_assignments"] = db.query(QuizAssignment).delete()
        cleared_records["import_jobs"] = db.query(ImportJob).delete()

        # 4. Questions and question options (quiz questions + question bank questions)
        cleared_records["question_options"] = db.query(QuestionOption).delete()
        cleared_records["questions"] = db.query(Question).delete()

        # 5. Break foreign key cycle on quizzes.current_version_id
        db.execute(update(Quiz).values(current_version_id=None))

        # 6. Quiz versions & parent quizzes
        cleared_records["quiz_versions"] = db.query(QuizVersion).delete()
        cleared_records["quizzes"] = db.query(Quiz).delete()

        # 7. Record an authoritative audit event documenting this reset operation
        audit = AuditEvent(
            user_id=admin_user.id,
            action="system.destructive_reset",
            entity_type="system",
            entity_id="all_test_data",
            details={
                "environment": settings.ENVIRONMENT,
                "cleared_records": cleared_records,
                "executed_by": admin_user.email,
            },
        )
        db.add(audit)
        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Destructive reset failed and was rolled back cleanly: {str(exc)}",
        )

    return {
        "success": True,
        "message": "All assessment test data was permanently removed. System restored to clean state.",
        "cleared_records": cleared_records,
        "executed_at": utc_now(),
    }


def bootstrap_admin_user(
    db: Session,
    token_payload: dict,
    bootstrap_token: Optional[str] = None,
) -> User:
    """
    Secure server-side initial administrator provisioning (DEC-022).
    - Requires matching ADMIN_EMAIL configured in server environment.
    - If ADMIN_BOOTSTRAP_TOKEN is configured in server environment, requires token match.
    - Never trusts client-supplied roles or metadata.
    - Promotes or creates the user with UserRole.ADMIN in the database.
    - Logs an AuditEvent for provisioning.
    """
    if not settings.ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrator provisioning is not configured (ADMIN_EMAIL is missing).",
        )

    token_email = token_payload.get("email")
    token_sub = token_payload.get("sub")

    if not token_email or not token_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing required claims (email or sub).",
        )

    if token_email.strip().lower() != settings.ADMIN_EMAIL.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not authorized for administrator provisioning.",
        )

    if settings.ADMIN_BOOTSTRAP_TOKEN:
        if not bootstrap_token or bootstrap_token.strip() != settings.ADMIN_BOOTSTRAP_TOKEN.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing administrator bootstrap token.",
            )

    try:
        user_uuid = uuid.UUID(str(token_sub))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user UUID in token subject.",
        )

    user = db.get(User, user_uuid)
    if not user:
        user = db.query(User).filter(User.email == token_email.strip().lower()).first()

    if user:
        user.role = UserRole.ADMIN
        user.is_active = True
        if settings.ADMIN_NAME and user.name in ("Pending Name", "System Administrator"):
            user.name = settings.ADMIN_NAME
    else:
        user = User(
            id=user_uuid,
            email=token_email.strip().lower(),
            name=settings.ADMIN_NAME or "System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(user)

    audit = AuditEvent(
        user_id=user.id,
        action="admin.bootstrap_provisioned",
        entity_type="user",
        entity_id=str(user.id),
        details={"email": user.email, "role": "admin"},
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    return user
