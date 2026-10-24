"""Admin service handling platform metrics, user directory, audit trails, bootstrapping, and guarded resets (DEC-022)."""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple
import uuid

from fastapi import HTTPException, status
import httpx
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
    AdminCleanWorkspaceRequest,
    AdminOverviewResponse,
    AdminOverviewStats,
    AdminStudentCreateRequest,
    AdminTeacherCreateRequest,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserPurgeRequest,
)

logger = logging.getLogger(__name__)



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


def _sync_supabase_user_auth(email: str, password: str, name: str, role: str = "teacher") -> Optional[uuid.UUID]:
    """
    Provision or update an account in Supabase Auth via Admin REST API.
    Enforces email_confirm=True and sets user_metadata.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None

    admin_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "name": name,
            "role": role,
        },
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(admin_url, headers=headers, json=payload)
            if resp.is_success:
                data = resp.json()
                return uuid.UUID(data["id"])

            if resp.status_code == 422:
                # User already exists in Supabase auth; locate user and update password/metadata
                get_resp = client.get(
                    f"{admin_url}?filter=email.eq.{email}",
                    headers=headers,
                )
                if get_resp.is_success:
                    users_data = get_resp.json()
                    users_list = (
                        users_data.get("users", [])
                        if isinstance(users_data, dict)
                        else users_data
                    )
                    for u in users_list:
                        if u.get("email", "").lower() == email.lower():
                            existing_id = uuid.UUID(u["id"])
                            client.put(
                                f"{admin_url}/{existing_id}",
                                headers=headers,
                                json={
                                    "password": password,
                                    "user_metadata": {"name": name, "role": role},
                                },
                            )
                            return existing_id
    except Exception as exc:
        logger.warning(f"Failed to communicate with Supabase Admin API for {role} sync: {exc}")

    return None


def _sync_supabase_teacher_auth(email: str, password: str, name: str) -> Optional[uuid.UUID]:
    return _sync_supabase_user_auth(email, password, name, role="teacher")


def _sync_supabase_student_auth(email: str, password: str, name: str) -> Optional[uuid.UUID]:
    return _sync_supabase_user_auth(email, password, name, role="student")


def _delete_supabase_auth_user(user_id: uuid.UUID) -> bool:
    """
    Permanently delete a user from Supabase Auth via Admin REST API.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return False

    admin_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{user_id}"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.delete(admin_url, headers=headers)
            return resp.is_success
    except Exception as exc:
        logger.warning(f"Failed to delete Supabase Auth user {user_id}: {exc}")
        return False


def _verify_admin_password(admin_email: str, password: str) -> bool:
    """
    Verify security authorization for destructive or sensitive administrative operations.
    Validates against:
    1. ADMIN_BOOTSTRAP_TOKEN if configured.
    2. Supabase Auth password grant endpoint if Supabase is active.
    3. Test / non-production safe credentials in development / testing environments.
    """
    # 1. Direct match on configured administrator bootstrap token
    if settings.ADMIN_BOOTSTRAP_TOKEN and password.strip() == settings.ADMIN_BOOTSTRAP_TOKEN.strip():
        return True

    # 2. Authenticate against Supabase Auth password grant if active
    if settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY):
        auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    auth_url,
                    headers=headers,
                    json={"email": admin_email, "password": password},
                )
                if resp.is_success:
                    return True
        except Exception as exc:
            logger.warning(f"Failed to verify admin password against Supabase: {exc}")

    # 3. Development / testing fallback credentials
    env_clean = (settings.ENVIRONMENT or "").strip().lower()
    if env_clean in ("development", "test", "testing"):
        if password in ("test-admin-password", "admin123", "password123", "secure-admin-pass"):
            return True

    return False


def create_teacher_user(
    db: Session,
    admin_user: User,
    req: AdminTeacherCreateRequest,
) -> User:
    """
    Onboard a new faculty member with institutional email and initial password.
    Creates or synchronizes their account in Supabase Auth (confirmed) and registers them
    as UserRole.TEACHER in the PostgreSQL database.
    """
    norm_email = req.email.strip().lower()
    norm_name = req.name.strip()

    if not norm_email or "@" not in norm_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid institutional email address is required.",
        )
    if len(norm_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty name must be at least 2 characters.",
        )
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial password must be at least 6 characters.",
        )

    # Check for existing email in database
    existing_user = db.query(User).filter(User.email == norm_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{norm_email}' is already registered as a {existing_user.role}.",
        )

    # Synchronize with Supabase Auth
    user_uuid = _sync_supabase_teacher_auth(norm_email, req.password, norm_name)
    if not user_uuid:
        user_uuid = uuid.uuid4()

    new_teacher = User(
        id=user_uuid,
        email=norm_email,
        name=norm_name,
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(new_teacher)

    audit = AuditEvent(
        user_id=admin_user.id,
        action="admin.teacher_created",
        entity_type="user",
        entity_id=str(new_teacher.id),
        details={
            "email": norm_email,
            "name": norm_name,
            "role": "teacher",
            "created_by": admin_user.email,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(new_teacher)

    return new_teacher


def create_student_user(
    db: Session,
    admin_user: User,
    req: AdminStudentCreateRequest,
) -> User:
    """
    Directly enroll/onboard a student member with institutional email, PRN, and initial password.
    Creates or synchronizes their account in Supabase Auth (confirmed), registers them
    as UserRole.STUDENT, and creates their StudentProfile in the PostgreSQL database.
    """
    norm_email = req.email.strip().lower()
    norm_name = req.name.strip()
    norm_prn = req.prn.strip().upper()
    norm_division = req.division.strip().upper() if req.division and req.division.strip() else None

    if not norm_email or "@" not in norm_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid institutional email address is required.",
        )
    if len(norm_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student name must be at least 2 characters.",
        )
    if len(norm_prn) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student PRN must be at least 3 characters.",
        )
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial password must be at least 6 characters.",
        )

    # Check for existing email in database
    existing_user = db.query(User).filter(User.email == norm_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{norm_email}' is already registered as a {existing_user.role}.",
        )

    # Check for existing PRN in database
    existing_profile = db.query(StudentProfile).filter(StudentProfile.prn == norm_prn).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with PRN '{norm_prn}' is already registered in the system.",
        )

    # Synchronize with Supabase Auth
    user_uuid = _sync_supabase_student_auth(norm_email, req.password, norm_name)
    if not user_uuid:
        user_uuid = uuid.uuid4()

    new_student = User(
        id=user_uuid,
        email=norm_email,
        name=norm_name,
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(new_student)
    db.flush()

    student_profile = StudentProfile(
        user_id=new_student.id,
        prn=norm_prn,
        current_division=norm_division,
    )
    db.add(student_profile)

    audit = AuditEvent(
        user_id=admin_user.id,
        action="admin.student_created",
        entity_type="user",
        entity_id=str(new_student.id),
        details={
            "email": norm_email,
            "name": norm_name,
            "prn": norm_prn,
            "division": norm_division,
            "role": "student",
            "created_by": admin_user.email,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(new_student)

    return new_student


def purge_single_user(
    db: Session,
    admin_user: User,
    req: AdminUserPurgeRequest,
) -> dict:
    """
    Cautiously and permanently purge a single user and all dependent records:
    - Verifies administrator security authorization password.
    - Prevents deleting the calling administrator or any administrator account.
    - Cascades attempt answers, telemetry, grade adjustments, and attempts.
    - Removes student profile and roster links.
    - Deletes user from PostgreSQL database.
    - Deletes user from Supabase Auth so re-enrollment works cleanly.
    - Logs an immutable AuditEvent.
    """
    if not _verify_admin_password(admin_user.email, req.admin_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid administrative security password or confirmation token.",
        )

    target_email = req.target_email.strip().lower()
    target_user = db.query(User).filter(User.email == target_email).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{target_email}' does not exist in the platform.",
        )

    if target_user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own account.",
        )

    if target_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator accounts cannot be deleted through this interface.",
        )

    cleared_records: Dict[str, int] = {}
    target_user_id = target_user.id
    target_user_name = target_user.name
    target_user_role = str(target_user.role)

    try:
        # 1. Collect and delete attempts by this student
        user_attempt_ids = [
            a.id for a in db.query(QuizAttempt.id).filter(QuizAttempt.student_id == target_user_id).all()
        ]
        if user_attempt_ids:
            cleared_records["attempt_answers"] = (
                db.query(AttemptAnswer)
                .filter(AttemptAnswer.attempt_id.in_(user_attempt_ids))
                .delete(synchronize_session=False)
            )
            cleared_records["attempt_telemetry_events"] = (
                db.query(AttemptTelemetryEvent)
                .filter(AttemptTelemetryEvent.attempt_id.in_(user_attempt_ids))
                .delete(synchronize_session=False)
            )
            cleared_records["grade_adjustments"] = (
                db.query(GradeAdjustment)
                .filter(GradeAdjustment.attempt_id.in_(user_attempt_ids))
                .delete(synchronize_session=False)
            )
            cleared_records["quiz_attempts"] = (
                db.query(QuizAttempt)
                .filter(QuizAttempt.id.in_(user_attempt_ids))
                .delete(synchronize_session=False)
            )
        else:
            cleared_records["attempt_answers"] = 0
            cleared_records["attempt_telemetry_events"] = 0
            cleared_records["grade_adjustments"] = 0
            cleared_records["quiz_attempts"] = 0

        # 2. Delete roster assignments linked to this user
        cleared_records["quiz_assignments"] = (
            db.query(QuizAssignment)
            .filter(
                or_(
                    QuizAssignment.assigned_student_id == target_user_id,
                    QuizAssignment.student_email == target_email,
                )
            )
            .delete(synchronize_session=False)
        )

        # 3. Delete student profile
        cleared_records["student_profiles"] = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == target_user_id)
            .delete(synchronize_session=False)
        )

        # 4. If target user was teacher and created quizzes, cascade test quizzes
        if target_user.role == UserRole.TEACHER:
            teacher_quizzes = db.query(Quiz.id).filter(Quiz.created_by_id == target_user_id).all()
            teacher_quiz_ids = [q.id for q in teacher_quizzes]
            if teacher_quiz_ids:
                t_version_ids = [
                    v.id for v in db.query(QuizVersion.id).filter(QuizVersion.quiz_id.in_(teacher_quiz_ids)).all()
                ]
                if t_version_ids:
                    t_attempts = [
                        a.id for a in db.query(QuizAttempt.id).filter(QuizAttempt.quiz_version_id.in_(t_version_ids)).all()
                    ]
                    if t_attempts:
                        db.query(AttemptAnswer).filter(AttemptAnswer.attempt_id.in_(t_attempts)).delete(synchronize_session=False)
                        db.query(AttemptTelemetryEvent).filter(AttemptTelemetryEvent.attempt_id.in_(t_attempts)).delete(synchronize_session=False)
                        db.query(GradeAdjustment).filter(GradeAdjustment.attempt_id.in_(t_attempts)).delete(synchronize_session=False)
                        db.query(QuizAttempt).filter(QuizAttempt.id.in_(t_attempts)).delete(synchronize_session=False)

                    db.query(QuestionOption).filter(
                        QuestionOption.question_id.in_(
                            db.query(Question.id).filter(Question.quiz_version_id.in_(t_version_ids))
                        )
                    ).delete(synchronize_session=False)
                    db.query(Question).filter(Question.quiz_version_id.in_(t_version_ids)).delete(synchronize_session=False)

                db.query(QuizAssignment).filter(QuizAssignment.quiz_id.in_(teacher_quiz_ids)).delete(synchronize_session=False)
                db.execute(update(Quiz).where(Quiz.id.in_(teacher_quiz_ids)).values(current_version_id=None))
                db.query(QuizVersion).filter(QuizVersion.quiz_id.in_(teacher_quiz_ids)).delete(synchronize_session=False)
                db.query(Quiz).filter(Quiz.id.in_(teacher_quiz_ids)).delete(synchronize_session=False)

            # Delete teacher question bank questions
            tb_questions = db.query(Question.id).filter(Question.created_by_id == target_user_id).all()
            if tb_questions:
                tb_q_ids = [q.id for q in tb_questions]
                db.query(QuestionOption).filter(QuestionOption.question_id.in_(tb_q_ids)).delete(synchronize_session=False)
                db.query(Question).filter(Question.id.in_(tb_q_ids)).delete(synchronize_session=False)

            db.query(ImportJob).filter(ImportJob.created_by_id == target_user_id).delete(synchronize_session=False)

        # 5. Nullify foreign key references in AuditEvent to preserve audit trail
        db.execute(update(AuditEvent).where(AuditEvent.user_id == target_user_id).values(user_id=None))

        # 6. Delete target User record
        db.delete(target_user)

        # 7. Record an authoritative audit event
        audit = AuditEvent(
            user_id=admin_user.id,
            action="admin.user_purged",
            entity_type="user",
            entity_id=str(target_user_id),
            details={
                "purged_email": target_email,
                "purged_name": target_user_name,
                "purged_role": target_user_role,
                "cleared_records": cleared_records,
                "executed_by": admin_user.email,
            },
        )
        db.add(audit)
        db.commit()

        # 8. Delete from Supabase Auth so re-enrollment is seamless
        _delete_supabase_auth_user(target_user_id)

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User purge failed and was rolled back cleanly: {str(exc)}",
        )

    return {
        "success": True,
        "message": f"User {target_email} and all dependent records were permanently removed.",
        "purged_user_id": str(target_user_id),
        "purged_email": target_email,
        "cleared_records": cleared_records,
        "executed_at": utc_now(),
    }


def execute_clean_teacher_workspace(
    db: Session,
    admin_user: User,
    confirmation_code: str,
) -> dict:
    """
    Cleans all rehearsal assessment records and all student accounts for teacher testing:
    - Clears all student attempt answers, telemetry, grade adjustments, and attempts.
    - Clears all student roster assignments.
    - Clears all StudentProfile records.
    - Clears all test quizzes, versions, and version-bound questions.
    - Strictly deletes all student users (role == UserRole.STUDENT) from DB and Supabase Auth.
    - Strictly preserves all TEACHER accounts and ADMIN accounts.
    - Logs an authoritative audit event.
    """
    env_normalized = (settings.ENVIRONMENT or "").strip().lower()
    if env_normalized == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clean workspace reset is strictly forbidden in production environment.",
        )

    if not settings.ALLOW_DESTRUCTIVE_RESET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clean workspace reset is disabled by system configuration (ALLOW_DESTRUCTIVE_RESET=false).",
        )

    if confirmation_code != "CONFIRM_CLEAN_TEACHER_WORKSPACE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation code. Must be strictly 'CONFIRM_CLEAN_TEACHER_WORKSPACE'.",
        )

    cleared_records: Dict[str, int] = {}

    try:
        # Collect all student user IDs before deletion
        student_rows = db.query(User.id).filter(User.role == UserRole.STUDENT).all()
        student_ids = [s.id for s in student_rows]

        # 1. Clear student attempt answers & telemetry
        cleared_records["attempt_answers"] = db.query(AttemptAnswer).delete(synchronize_session=False)
        cleared_records["attempt_telemetry_events"] = db.query(AttemptTelemetryEvent).delete(synchronize_session=False)

        # 2. Clear grade adjustments & quiz attempts
        cleared_records["grade_adjustments"] = db.query(GradeAdjustment).delete(synchronize_session=False)
        cleared_records["quiz_attempts"] = db.query(QuizAttempt).delete(synchronize_session=False)

        # 3. Clear quiz assignments
        cleared_records["quiz_assignments"] = db.query(QuizAssignment).delete(synchronize_session=False)

        # 4. Clear student profiles
        cleared_records["student_profiles"] = db.query(StudentProfile).delete(synchronize_session=False)

        # 5. Clear quizzes, versions, and questions to restore clean test workspace
        db.execute(update(Quiz).values(current_version_id=None))
        version_q_subquery = db.query(Question.id).filter(Question.quiz_version_id.isnot(None))
        cleared_records["quiz_question_options"] = db.query(QuestionOption).filter(
            QuestionOption.question_id.in_(version_q_subquery)
        ).delete(synchronize_session=False)
        cleared_records["quiz_questions"] = db.query(Question).filter(
            Question.quiz_version_id.isnot(None)
        ).delete(synchronize_session=False)
        cleared_records["quiz_versions"] = db.query(QuizVersion).delete(synchronize_session=False)
        cleared_records["quizzes"] = db.query(Quiz).delete(synchronize_session=False)
        cleared_records["import_jobs"] = db.query(ImportJob).delete(synchronize_session=False)

        # 6. Nullify student references in AuditEvent
        if student_ids:
            db.execute(
                update(AuditEvent).where(AuditEvent.user_id.in_(student_ids)).values(user_id=None)
            )

        # 7. Delete student User records (strictly role == STUDENT)
        cleared_records["student_users"] = (
            db.query(User).filter(User.role == UserRole.STUDENT).delete(synchronize_session=False)
        )

        teachers_count = db.query(func.count(User.id)).filter(User.role == UserRole.TEACHER).scalar() or 0
        admins_count = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar() or 0

        # 8. Record audit event
        audit = AuditEvent(
            user_id=admin_user.id,
            action="system.clean_teacher_workspace",
            entity_type="system",
            entity_id="teacher_workspace",
            details={
                "environment": settings.ENVIRONMENT,
                "cleared_records": cleared_records,
                "purged_students_count": len(student_ids),
                "preserved_teachers_count": teachers_count,
                "preserved_admins_count": admins_count,
                "executed_by": admin_user.email,
            },
        )
        db.add(audit)
        db.commit()

        # 9. Clean up Supabase Auth for deleted students
        for sid in student_ids:
            _delete_supabase_auth_user(sid)

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clean teacher workspace failed and was rolled back cleanly: {str(exc)}",
        )

    return {
        "success": True,
        "message": "Teacher workspace cleaned successfully. All students and test attempts cleared. Teacher and admin accounts preserved.",
        "cleared_records": cleared_records,
        "purged_students_count": len(student_ids),
        "preserved_teachers_count": teachers_count,
        "executed_at": utc_now(),
    }

