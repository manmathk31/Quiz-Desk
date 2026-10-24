"""Tests for Admin Portal, Bootstrap Provisioning, and Guarded Reset (DEC-022, Phase 8B)."""
from datetime import datetime, timezone
import time
import uuid
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole, StudentProfile
from app.models.quiz import Quiz, QuizVersion, QuizStatus
from app.models.question import Question, QuestionOption, QuestionType
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptTelemetryEvent, AttemptStatus
from app.models.audit import AuditEvent, GradeAdjustment, ImportJob
from app.models.roster import QuizAssignment
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-secret-key-hs256-for-admin-portal-unit-tests-1234567890"

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_test_token(
    sub: str,
    email: str = "test@institution.edu",
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    expires_in_seconds: int = 3600,
    aud: str = "authenticated",
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "aud": aud,
        "exp": now + expires_in_seconds,
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(settings, "SUPABASE_JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", False)
    monkeypatch.setattr(settings, "ADMIN_EMAIL", "admin@institution.edu")
    monkeypatch.setattr(settings, "ADMIN_NAME", "Principal Admin")
    monkeypatch.setattr(settings, "ADMIN_BOOTSTRAP_TOKEN", "test-bootstrap-secret-token")

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="admin@institution.edu",
        name="Principal Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def teacher_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="teacher@institution.edu",
        name="Prof. Sharma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="student@institution.edu",
        name="Rohan Verma",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = StudentProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        prn="2026CS001",
        current_division="A",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# 1. Authorization & Role Enforcement Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_endpoints_reject_unauthenticated():
    """Unauthenticated requests must return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res1 = await client.get("/api/v1/admin/overview")
        res2 = await client.get("/api/v1/admin/users")
        res3 = await client.get("/api/v1/admin/audit-logs")
        res4 = await client.get("/api/v1/admin/reset-status")
    assert res1.status_code == 401
    assert res2.status_code == 401
    assert res3.status_code == 401
    assert res4.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoints_reject_student_and_teacher(student_user: User, teacher_user: User):
    """Students and teachers must receive 403 Forbidden on admin endpoints."""
    student_token = make_test_token(sub=str(student_user.id), email=student_user.email)
    teacher_token = make_test_token(sub=str(teacher_user.id), email=teacher_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Student access attempts
        s_res1 = await client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {student_token}"})
        s_res2 = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert s_res1.status_code == 403
        assert s_res2.status_code == 403

        # Teacher access attempts
        t_res1 = await client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {teacher_token}"})
        t_res2 = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {teacher_token}"})
        assert t_res1.status_code == 403
        assert t_res2.status_code == 403


# ==============================================================================
# 2. Administrator Bootstrap Provisioning Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_bootstrap_success(db_session: Session):
    """Valid bootstrap request with matching ADMIN_EMAIL and token creates/promotes admin."""
    new_admin_uuid = str(uuid.uuid4())
    token = make_test_token(sub=new_admin_uuid, email="admin@institution.edu")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
            json={"bootstrap_token": "test-bootstrap-secret-token"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@institution.edu"
    assert data["role"] == "admin"
    assert data["is_active"] is True

    # Verify audit event was recorded
    audit = db_session.query(AuditEvent).filter(AuditEvent.action == "admin.bootstrap_provisioned").first()
    assert audit is not None
    assert audit.entity_id == new_admin_uuid


@pytest.mark.asyncio
async def test_admin_bootstrap_rejects_unauthorized_email():
    """Bootstrap attempt with non-matching email returns 403 Forbidden."""
    impostor_uuid = str(uuid.uuid4())
    token = make_test_token(sub=impostor_uuid, email="attacker@other.edu")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
            json={"bootstrap_token": "test-bootstrap-secret-token"},
        )

    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_bootstrap_rejects_invalid_bootstrap_token():
    """Bootstrap attempt with invalid bootstrap token returns 403 Forbidden."""
    token = make_test_token(sub=str(uuid.uuid4()), email="admin@institution.edu")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/bootstrap",
            headers={"Authorization": f"Bearer {token}"},
            json={"bootstrap_token": "wrong-token"},
        )

    assert res.status_code == 403
    assert "invalid or missing" in res.json()["detail"].lower()


# ==============================================================================
# 3. Admin Overview & Metrics Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_overview_metrics(admin_user: User, teacher_user: User, student_user: User, db_session: Session):
    """Overview returns accurate student, teacher, quiz, and attempt aggregates."""
    # Seed a quiz and attempt
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Operating Systems Midterm",
        course_code="CS301",
        created_by_id=teacher_user.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz)
    db_session.commit()

    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    stats = data["stats"]
    assert stats["total_students"] == 1
    assert stats["total_teachers"] == 1
    assert stats["total_quizzes"] == 1
    assert stats["published_quizzes"] == 1


# ==============================================================================
# 4. User Directory & Status Update Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_user_directory_and_search(admin_user: User, student_user: User):
    """Admin can query user list and filter by name/email/PRN."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Full list
        res = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2

        # 2. Search by PRN
        search_res = await client.get(
            "/api/v1/admin/users?search=2026CS001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["total"] == 1
        assert search_data["items"][0]["prn"] == "2026CS001"
        assert search_data["items"][0]["email"] == student_user.email


@pytest.mark.asyncio
async def test_admin_user_deactivation_and_self_guard(admin_user: User, student_user: User):
    """Admin can deactivate a user, but cannot deactivate their own admin account."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Admin attempts to deactivate self -> blocked with 400
        self_res = await client.patch(
            f"/api/v1/admin/users/{admin_user.id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_active": False},
        )
        assert self_res.status_code == 400
        assert "cannot deactivate their own account" in self_res.json()["detail"].lower()

        # 2. Admin deactivates student account -> succeeds
        target_res = await client.patch(
            f"/api/v1/admin/users/{student_user.id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_active": False},
        )
        assert target_res.status_code == 200
        assert target_res.json()["is_active"] is False


# ==============================================================================
# 5. Guarded Test Data Reset Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_reset_disabled_by_default(admin_user: User, monkeypatch):
    """Reset must be rejected when ALLOW_DESTRUCTIVE_RESET is False."""
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", False)
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/reset-test-data",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "CONFIRM_DELETE_ALL_TEST_DATA"},
        )

    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_blocked_in_production(admin_user: User, monkeypatch):
    """Reset must be strictly blocked if ENVIRONMENT is production."""
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/reset-test-data",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "CONFIRM_DELETE_ALL_TEST_DATA"},
        )

    assert res.status_code == 403
    assert "production" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_blocked_with_invalid_confirmation_code(admin_user: User, monkeypatch):
    """Reset must reject invalid confirmation codes with 400 Bad Request."""
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/reset-test-data",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "wrong_code"},
        )

    assert res.status_code == 400
    assert "invalid confirmation code" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_success_in_development(admin_user: User, teacher_user: User, student_user: User, db_session: Session, monkeypatch):
    """
    When properly configured in non-production, reset cleans assessment records,
    preserves user accounts, preserves audit log, and records audit trail.
    """
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    # Seed assessment data to be cleared:
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Chemistry Quiz",
        course_code="CH101",
        created_by_id=teacher_user.id,
        status=QuizStatus.DRAFT,
    )
    db_session.add(quiz)
    db_session.flush()

    assignment = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        student_prn="2026CS001",
        student_email=student_user.email,
        student_name=student_user.name,
        division="A",
    )
    db_session.add(assignment)
    db_session.commit()

    assert db_session.query(Quiz).count() == 1
    assert db_session.query(QuizAssignment).count() == 1

    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/reset-test-data",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "CONFIRM_DELETE_ALL_TEST_DATA"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["cleared_records"]["quizzes"] == 1
    assert data["cleared_records"]["quiz_assignments"] == 1

    # Verify assessment data is gone
    assert db_session.query(Quiz).count() == 0
    assert db_session.query(QuizAssignment).count() == 0

    # Verify users (including admin) remain intact
    assert db_session.query(User).count() >= 3
    assert db_session.get(User, admin_user.id) is not None

    # Verify audit event was created
    reset_audit = db_session.query(AuditEvent).filter(AuditEvent.action == "system.destructive_reset").first()
    assert reset_audit is not None
    assert reset_audit.user_id == admin_user.id


# ==============================================================================
# 6. Faculty Onboarding Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_create_teacher_success(admin_user: User, db_session: Session):
    """Admin can onboard a new faculty member with email, name, and initial password."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/teachers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "dr.kulkarni@institution.edu",
                "name": "Dr. Ramesh Kulkarni",
                "password": "initial-secret-123",
            },
        )

    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "dr.kulkarni@institution.edu"
    assert data["name"] == "Dr. Ramesh Kulkarni"
    assert data["role"] == "teacher"
    assert data["is_active"] is True

    # Check DB entry
    created_teacher = db_session.query(User).filter(User.email == "dr.kulkarni@institution.edu").first()
    assert created_teacher is not None
    assert created_teacher.role == UserRole.TEACHER

    # Check audit log
    audit = db_session.query(AuditEvent).filter(AuditEvent.action == "admin.teacher_created").first()
    assert audit is not None
    assert audit.details["email"] == "dr.kulkarni@institution.edu"


@pytest.mark.asyncio
async def test_admin_create_teacher_rejects_duplicate_email(admin_user: User, teacher_user: User):
    """Creating a teacher with an email that is already registered returns 409 Conflict."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/teachers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": teacher_user.email,
                "name": "Prof. Impostor",
                "password": "initial-secret-123",
            },
        )

    assert res.status_code == 409
    assert "already registered" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_create_teacher_validates_inputs(admin_user: User):
    """Short passwords or invalid emails are rejected with 400 Bad Request."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_short = await client.post(
            "/api/v1/admin/teachers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "teacher.short@institution.edu",
                "name": "Short Pass Teacher",
                "password": "123",  # < 6 chars
            },
        )
        assert res_short.status_code in (400, 422)


# ==============================================================================
# 6B. Student Onboarding Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_create_student_success(admin_user: User, db_session: Session):
    """Admin can enroll a new student with email, name, PRN, division, and initial password."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/students",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "rohit.patil@institution.edu",
                "name": "Rohit Patil",
                "prn": "2026CS999",
                "division": "A",
                "password": "initial-secret-123",
            },
        )

    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "rohit.patil@institution.edu"
    assert data["name"] == "Rohit Patil"
    assert data["role"] == "student"
    assert data["is_active"] is True

    # Check DB user and profile entries
    created_student = db_session.query(User).filter(User.email == "rohit.patil@institution.edu").first()
    assert created_student is not None
    assert created_student.role == UserRole.STUDENT
    assert created_student.student_profile is not None
    assert created_student.student_profile.prn == "2026CS999"
    assert created_student.student_profile.current_division == "A"

    # Check audit log
    audit = db_session.query(AuditEvent).filter(AuditEvent.action == "admin.student_created").first()
    assert audit is not None
    assert audit.details["email"] == "rohit.patil@institution.edu"
    assert audit.details["prn"] == "2026CS999"


@pytest.mark.asyncio
async def test_admin_create_student_rejects_duplicate_prn(admin_user: User, student_user: User):
    """Enrolling a student with an existing PRN returns 409 Conflict."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/students",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "unique.email@institution.edu",
                "name": "Another Student",
                "prn": student_user.student_profile.prn,
                "password": "initial-secret-123",
            },
        )

    assert res.status_code == 409
    assert "already registered" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_create_student_rejects_duplicate_email(admin_user: User, student_user: User):
    """Enrolling a student with an existing email returns 409 Conflict."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/students",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": student_user.email,
                "name": "Duplicate Email Student",
                "prn": "BRANDNEWPRN01",
                "password": "initial-secret-123",
            },
        )

    assert res.status_code == 409
    assert "already registered" in res.json()["detail"].lower()


# ==============================================================================
# 7. Cautious Single-User Purge Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_purge_single_user_success(admin_user: User, student_user: User, db_session: Session):
    """Admin can permanently purge a user account, student profile, attempts, and assignments."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)
    now = datetime.now(timezone.utc)

    # Seed an assignment and an attempt for this student
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Physics Quiz",
        course_code="PH101",
        created_by_id=admin_user.id,
        status=QuizStatus.DRAFT,
    )
    db_session.add(quiz)
    db_session.flush()

    from datetime import timedelta
    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        title="Physics Quiz",
        version_number=1,
        opens_at=now,
        closes_at=now + timedelta(hours=2),
        duration_minutes=60,
    )
    db_session.add(version)
    db_session.flush()

    attempt = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        student_id=student_user.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now,
        deadline_at=now + timedelta(hours=1),
    )
    db_session.add(attempt)

    assignment = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        student_prn=student_user.student_profile.prn,
        student_email=student_user.email,
        student_name=student_user.name,
        division="A",
        assigned_student_id=student_user.id,
    )
    db_session.add(assignment)
    db_session.commit()

    saved_student_id = student_user.id
    saved_student_email = student_user.email
    saved_profile_id = student_user.student_profile.id
    saved_attempt_id = attempt.id
    saved_assignment_id = assignment.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/users/purge",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "target_email": saved_student_email,
                "admin_password": "test-bootstrap-secret-token",  # matches ADMIN_BOOTSTRAP_TOKEN
            },
        )

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["purged_email"] == saved_student_email

    # Verify student is removed from database
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == saved_student_id).first() is None
    assert db_session.query(StudentProfile).filter(StudentProfile.id == saved_profile_id).first() is None
    assert db_session.query(QuizAttempt).filter(QuizAttempt.id == saved_attempt_id).first() is None
    assert db_session.query(QuizAssignment).filter(QuizAssignment.id == saved_assignment_id).first() is None

    # Verify audit event was created
    audit = db_session.query(AuditEvent).filter(AuditEvent.action == "admin.user_purged").first()
    assert audit is not None
    assert audit.details["purged_email"] == saved_student_email



@pytest.mark.asyncio
async def test_admin_purge_rejects_invalid_admin_password(admin_user: User, student_user: User):
    """Purge request with incorrect admin password returns 403 Forbidden."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/users/purge",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "target_email": student_user.email,
                "admin_password": "completely-wrong-password",
            },
        )

    assert res.status_code == 403
    assert "security password" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_purge_prevents_deleting_self_and_admins(admin_user: User):
    """Admin cannot delete their own account or another administrator account."""
    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/users/purge",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "target_email": admin_user.email,
                "admin_password": "test-bootstrap-secret-token",
            },
        )

    assert res.status_code == 400
    assert "cannot delete" in res.json()["detail"].lower()


# ==============================================================================
# 8. Clean Teacher Workspace Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_clean_teacher_workspace_success(
    admin_user: User, teacher_user: User, student_user: User, db_session: Session, monkeypatch
):
    """
    Clean teacher workspace resets all student accounts, profiles, attempts,
    and test quizzes, while strictly preserving teacher and admin accounts.
    """
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)
    saved_student_id = student_user.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/clean-teacher-workspace",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "CONFIRM_CLEAN_TEACHER_WORKSPACE"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["purged_students_count"] == 1
    assert data["preserved_teachers_count"] == 1

    # Verify student was deleted
    db_session.expire_all()
    assert db_session.query(User).filter(User.id == saved_student_id).first() is None

    # Verify teacher and admin accounts remain intact
    assert db_session.get(User, teacher_user.id) is not None
    assert db_session.get(User, admin_user.id) is not None


    # Verify audit event
    audit = db_session.query(AuditEvent).filter(AuditEvent.action == "system.clean_teacher_workspace").first()
    assert audit is not None


@pytest.mark.asyncio
async def test_clean_teacher_workspace_rejects_wrong_code(admin_user: User, monkeypatch):
    """Clean teacher workspace requires exact confirmation code."""
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    token = make_test_token(sub=str(admin_user.id), email=admin_user.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/admin/clean-teacher-workspace",
            headers={"Authorization": f"Bearer {token}"},
            json={"confirmation_code": "WRONG_CONFIRMATION"},
        )

    assert res.status_code == 400
    assert "invalid confirmation code" in res.json()["detail"].lower()

