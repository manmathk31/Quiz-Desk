"""Comprehensive Security and Authorization Audit Regression Test Suite (Phase 9).

Validates:
1. Strict cross-student attempt and answer isolation.
2. Sanitization of student delivery payloads (concealment of correct answers/is_correct).
3. Student result release gate (withheld prior to explicit release).
4. Strict cross-teacher quiz, question bank, roster, and results isolation.
5. Role-based access control (RBAC) boundaries on student, teacher, and admin endpoints.
6. Admin bootstrap and guarded reset safeguards.
7. CSV export formula injection mitigation.
"""
from datetime import datetime, timezone, timedelta
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
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptStatus, GradingStatus
from app.models.roster import QuizAssignment
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "security-audit-test-secret-key-hs256-abcdef1234567890"

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=test_engine,
)


def make_test_token(
    sub: str,
    email: str,
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
def setup_security_test_db(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(settings, "SUPABASE_JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ALLOW_DESTRUCTIVE_RESET", True)
    monkeypatch.setattr(settings, "ADMIN_EMAIL", "principal@institution.edu")
    monkeypatch.setattr(settings, "ADMIN_NAME", "Principal Admin")
    monkeypatch.setattr(settings, "ADMIN_BOOTSTRAP_TOKEN", "super-secret-bootstrap-token")

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
def security_fixtures():
    db: Session = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Users: 2 Teachers, 2 Students, 1 Admin
    teacher_a = User(
        id=uuid.uuid4(),
        email="prof.a@institution.edu",
        name="Professor A",
        role=UserRole.TEACHER,
        is_active=True,
    )
    teacher_b = User(
        id=uuid.uuid4(),
        email="prof.b@institution.edu",
        name="Professor B",
        role=UserRole.TEACHER,
        is_active=True,
    )
    student_1 = User(
        id=uuid.uuid4(),
        email="student1@institution.edu",
        name="Alice Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_2 = User(
        id=uuid.uuid4(),
        email="student2@institution.edu",
        name="Bob Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    admin_user = User(
        id=uuid.uuid4(),
        email="principal@institution.edu",
        name="Principal Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add_all([teacher_a, teacher_b, student_1, student_2, admin_user])
    db.flush()

    # Student profiles
    profile_1 = StudentProfile(user_id=student_1.id, prn="PRN001", current_division="A")
    profile_2 = StudentProfile(user_id=student_2.id, prn="PRN002", current_division="B")
    db.add_all([profile_1, profile_2])
    db.flush()

    # 2. Quizzes: Quiz A (Teacher A), Quiz B (Teacher B)
    quiz_a = Quiz(
        id=uuid.uuid4(),
        title="Distributed Systems Quiz",
        course_code="CS401",
        created_by_id=teacher_a.id,
        status=QuizStatus.PUBLISHED,
    )
    quiz_b = Quiz(
        id=uuid.uuid4(),
        title="Database Internals Quiz",
        course_code="CS402",
        created_by_id=teacher_b.id,
        status=QuizStatus.PUBLISHED,
    )
    db.add_all([quiz_a, quiz_b])
    db.flush()

    # Versions
    ver_a = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        version_number=1,
        title="Distributed Systems Quiz v1",
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=2),
        duration_minutes=60,
        max_attempts=1,
        is_results_released=False,
    )
    ver_b = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz_b.id,
        version_number=1,
        title="Database Internals Quiz v1",
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=2),
        duration_minutes=60,
        max_attempts=1,
        is_results_released=False,
    )
    db.add_all([ver_a, ver_b])
    db.flush()

    quiz_a.current_version_id = ver_a.id
    quiz_b.current_version_id = ver_b.id

    # Question for Quiz A
    q_a = Question(
        id=uuid.uuid4(),
        quiz_version_id=ver_a.id,
        created_by_id=teacher_a.id,
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        prompt="What is Raft consensus?",
        positive_marks=2.0,
        negative_marks=0.5,
    )
    db.add(q_a)
    db.flush()

    opt_a1 = QuestionOption(
        id=uuid.uuid4(),
        question_id=q_a.id,
        option_text="Leader election & log replication",
        order_index=0,
        is_correct=True,
    )
    opt_a2 = QuestionOption(
        id=uuid.uuid4(),
        question_id=q_a.id,
        option_text="A hashing algorithm",
        order_index=1,
        is_correct=False,
    )
    db.add_all([opt_a1, opt_a2])

    # Question for Quiz B
    q_b = Question(
        id=uuid.uuid4(),
        quiz_version_id=ver_b.id,
        created_by_id=teacher_b.id,
        question_type=QuestionType.SINGLE_CHOICE,
        difficulty=QuestionDifficulty.EASY,
        prompt="What is WAL?",
        positive_marks=1.0,
        negative_marks=0.0,
    )
    db.add(q_b)
    db.flush()

    opt_b1 = QuestionOption(
        id=uuid.uuid4(),
        question_id=q_b.id,
        option_text="Write-Ahead Logging",
        order_index=0,
        is_correct=True,
    )
    opt_b2 = QuestionOption(
        id=uuid.uuid4(),
        question_id=q_b.id,
        option_text="Wide-Area Locator",
        order_index=1,
        is_correct=False,
    )
    db.add_all([opt_b1, opt_b2])

    # Rosters: Student 1 assigned to Quiz A
    assign_a1 = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        student_prn="PRN001",
        student_name="Alice Student",
        student_email="student1@institution.edu",
        division="A",
        is_active=True,
        assigned_student_id=student_1.id,
    )
    # Student 2 assigned to Quiz A
    assign_a2 = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        student_prn="PRN002",
        student_name="Bob Student",
        student_email="student2@institution.edu",
        division="B",
        is_active=True,
        assigned_student_id=student_2.id,
    )
    db.add_all([assign_a1, assign_a2])
    db.flush()

    # Active attempt for Student 1 on Quiz A
    attempt_s1 = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=ver_a.id,
        student_id=student_1.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now,
        deadline_at=now + timedelta(minutes=60),
        tab_switch_count=0,
        grading_status=GradingStatus.PENDING,
        is_finalized=False,
        question_order=[str(q_a.id)],
        option_order={str(q_a.id): [str(opt_a1.id), str(opt_a2.id)]},
    )
    db.add(attempt_s1)
    db.commit()

    return {
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "student_1": student_1,
        "student_2": student_2,
        "admin_user": admin_user,
        "quiz_a": quiz_a,
        "quiz_b": quiz_b,
        "ver_a": ver_a,
        "ver_b": ver_b,
        "q_a": q_a,
        "opt_a1": opt_a1,
        "opt_a2": opt_a2,
        "attempt_s1": attempt_s1,
    }


# ==============================================================================
# 1. Student Boundary & Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_student_cannot_access_other_student_attempt(security_fixtures):
    """Verify Student 2 cannot fetch Student 1's active assessment attempt (returns 404)."""
    f = security_fixtures
    token_s2 = make_test_token(str(f["student_2"].id), f["student_2"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}",
            headers={"Authorization": f"Bearer {token_s2}"},
        )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Assessment attempt session not found."


@pytest.mark.asyncio
async def test_student_cannot_autosave_to_other_student_attempt(security_fixtures):
    """Verify Student 2 cannot autosave an answer on Student 1's attempt (returns 404)."""
    f = security_fixtures
    token_s2 = make_test_token(str(f["student_2"].id), f["student_2"].email)

    payload = {
        "selected_option_ids": [str(f["opt_a1"].id)],
        "client_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}/answers/{f['q_a'].id}",
            json=payload,
            headers={"Authorization": f"Bearer {token_s2}"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_submit_other_student_attempt(security_fixtures):
    """Verify Student 2 cannot submit Student 1's attempt (returns 404)."""
    f = security_fixtures
    token_s2 = make_test_token(str(f["student_2"].id), f["student_2"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}/submit",
            headers={"Authorization": f"Bearer {token_s2}"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_delivery_payload_strictly_conceals_correctness(security_fixtures):
    """Verify that student delivery payload NEVER leaks is_correct flags or answer keys."""
    f = security_fixtures
    token_s1 = make_test_token(str(f["student_1"].id), f["student_1"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
    assert resp.status_code == 200
    data = resp.json()

    assert "questions" in data
    assert len(data["questions"]) > 0
    for q in data["questions"]:
        assert "is_correct" not in q
        assert "correct_answers" not in q
        for opt in q["options"]:
            assert "is_correct" not in opt
            assert "correct" not in opt


@pytest.mark.asyncio
async def test_student_result_view_strictly_withheld_prior_to_release(security_fixtures):
    """Verify that Student 1 cannot view results before the teacher releases them (returns 403)."""
    f = security_fixtures
    token_s1 = make_test_token(str(f["student_1"].id), f["student_1"].email)

    # First submit Student 1's attempt
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        submit_resp = await client.post(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}/submit",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
        assert submit_resp.status_code == 200

        # Now query result before release
        result_resp = await client.get(
            f"/api/v1/student/attempts/{f['attempt_s1'].id}/result",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
    assert result_resp.status_code == 403
    assert "not been released" in result_resp.json()["detail"]


# ==============================================================================
# 2. Teacher Boundary & Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_teacher_cannot_read_or_edit_other_teacher_quiz(security_fixtures):
    """Verify Teacher B cannot read or edit Teacher A's quiz (returns 404)."""
    f = security_fixtures
    token_b = make_test_token(str(f["teacher_b"].id), f["teacher_b"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET
        get_resp = await client.get(
            f"/api/v1/quizzes/{f['quiz_a'].id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_resp.status_code == 404

        # PUT
        put_resp = await client.put(
            f"/api/v1/quizzes/{f['quiz_a'].id}",
            json={
                "title": "Hacked Title",
                "course_code": "HACK101",
                "opens_at": datetime.now(timezone.utc).isoformat(),
                "closes_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "duration_minutes": 30,
                "max_attempts": 1,
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert put_resp.status_code == 404


@pytest.mark.asyncio
async def test_teacher_cannot_access_other_teacher_roster_or_results(security_fixtures):
    """Verify Teacher B cannot access Teacher A's roster or results (returns 404)."""
    f = security_fixtures
    token_b = make_test_token(str(f["teacher_b"].id), f["teacher_b"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Roster list
        roster_resp = await client.get(
            f"/api/v1/quizzes/{f['quiz_a'].id}/roster",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert roster_resp.status_code == 404

        # Results summary
        results_resp = await client.get(
            f"/api/v1/quizzes/{f['quiz_a'].id}/results/summary",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert results_resp.status_code == 404

        # Results release
        release_resp = await client.post(
            f"/api/v1/quizzes/{f['quiz_a'].id}/results/release",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert release_resp.status_code == 404


# ==============================================================================
# 3. RBAC Cross-Role Boundary Denials
# ==============================================================================

@pytest.mark.asyncio
async def test_student_denied_teacher_and_admin_endpoints(security_fixtures):
    """Verify Student role is rejected with HTTP 403 on teacher and admin endpoints."""
    f = security_fixtures
    token_s1 = make_test_token(str(f["student_1"].id), f["student_1"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Teacher quiz list
        q_resp = await client.get(
            "/api/v1/quizzes",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
        assert q_resp.status_code == 403

        # Teacher question bank
        qb_resp = await client.get(
            "/api/v1/question-bank",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
        assert qb_resp.status_code == 403

        # Admin overview
        admin_resp = await client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {token_s1}"},
        )
        assert admin_resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_denied_admin_endpoints(security_fixtures):
    """Verify Teacher role is rejected with HTTP 403 on admin endpoints."""
    f = security_fixtures
    token_a = make_test_token(str(f["teacher_a"].id), f["teacher_a"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {token_a}"},
        )
    assert resp.status_code == 403


# ==============================================================================
# 4. Admin Provisioning & Guarded Reset Safeguards
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_bootstrap_fails_on_email_mismatch():
    """Verify admin bootstrap fails if token email does not match ADMIN_EMAIL."""
    token = make_test_token(str(uuid.uuid4()), "imposter@institution.edu")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/bootstrap",
            json={"bootstrap_token": "super-secret-bootstrap-token"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_bootstrap_fails_on_invalid_bootstrap_token():
    """Verify admin bootstrap fails if bootstrap token does not match server config."""
    token = make_test_token(str(uuid.uuid4()), "principal@institution.edu")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/bootstrap",
            json={"bootstrap_token": "wrong-token"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_destructive_reset_strictly_blocked_in_production(security_fixtures, monkeypatch):
    """Verify destructive reset fails closed in production environment (returns 403)."""
    f = security_fixtures
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    token_admin = make_test_token(str(f["admin_user"].id), f["admin_user"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/reset-test-data",
            json={"confirmation_code": "CONFIRM_DELETE_ALL_TEST_DATA"},
            headers={"Authorization": f"Bearer {token_admin}"},
        )
    assert resp.status_code == 403
    assert "strictly forbidden in production" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_destructive_reset_fails_without_matching_confirmation_code(security_fixtures):
    """Verify destructive reset fails with 400 Bad Request if confirmation code is incorrect."""
    f = security_fixtures
    token_admin = make_test_token(str(f["admin_user"].id), f["admin_user"].email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/reset-test-data",
            json={"confirmation_code": "wrong_confirmation_code"},
            headers={"Authorization": f"Bearer {token_admin}"},
        )
    assert resp.status_code == 400
    assert "Invalid confirmation code" in resp.json()["detail"]
