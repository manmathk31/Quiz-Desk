"""Integration tests for Student Quiz Eligibility verification endpoints (DEC-005, DEC-007, Phase 5)."""
from datetime import datetime, timezone, timedelta
import time
import uuid
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, StudentProfile, UserRole
from app.models.quiz import Quiz, QuizVersion, QuizStatus
from app.models.roster import QuizAssignment
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-eligibility-secret-key-hs256-abcdef012345"

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_test_token(sub: str, expires_in_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "exp": now + expires_in_seconds,
        "iat": now,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(settings, "SUPABASE_JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated")

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
def test_teacher(db_session: Session) -> User:
    teacher = User(
        id=uuid.uuid4(),
        email="prof.sharma@college.edu",
        name="Prof. Sharma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher


@pytest.fixture
def test_student(db_session: Session) -> User:
    student = User(
        id=uuid.uuid4(),
        email="aarav.sharma@college.edu",
        name="Aarav Sharma",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(student)
    db_session.flush()

    profile = StudentProfile(
        id=uuid.uuid4(),
        user_id=student.id,
        prn="202401110001",
        current_division="A",
    )
    db_session.add(profile)
    db_session.commit()
    return student


@pytest.fixture
def published_quiz(db_session: Session, test_teacher: User) -> Quiz:
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Algorithms Final Exam",
        course_code="CS301",
        created_by_id=test_teacher.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz)
    db_session.flush()

    now = datetime.now(timezone.utc)
    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        version_number=1,
        title=quiz.title,
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=3),
        duration_minutes=90,
        max_attempts=1,
    )
    db_session.add(version)
    quiz.current_version_id = version.id
    db_session.commit()
    return quiz


@pytest.mark.asyncio
async def test_unauthenticated_eligibility_rejected(published_quiz: Quiz):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/student/quizzes/{published_quiz.id}/eligibility")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_teacher_denied_student_eligibility(published_quiz: Quiz, test_teacher: User):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_non_existent_quiz_returns_404(test_student: User):
    token = make_test_token(str(test_student.id))
    fake_id = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{fake_id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_unpublished_quiz_denied(test_teacher: User, test_student: User, db_session: Session):
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Unpublished Draft Quiz",
        course_code="CS101",
        created_by_id=test_teacher.id,
        status=QuizStatus.DRAFT,
    )
    db_session.add(quiz)
    db_session.flush()

    now = datetime.now(timezone.utc)
    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        version_number=1,
        title=quiz.title,
        is_published=False,  # Draft
        opens_at=now,
        closes_at=now + timedelta(hours=2),
        duration_minutes=60,
    )
    db_session.add(version)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "not currently published" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unassigned_student_denied(published_quiz: Quiz, test_student: User):
    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "not assigned" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoked_student_assignment_denied(
    published_quiz: Quiz,
    test_student: User,
    db_session: Session,
):
    assignment = QuizAssignment(
        quiz_id=published_quiz.id,
        student_prn="202401110001",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        assigned_student_id=test_student.id,
        is_active=False,  # Revoked!
        revoked_at=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "revoked" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_identity_mismatch_denied(
    published_quiz: Quiz,
    test_student: User,
    db_session: Session,
):
    # Assignment has test_student's email, but a DIFFERENT PRN
    assignment = QuizAssignment(
        quiz_id=published_quiz.id,
        student_prn="DIFFERENT_PRN_999",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "identity conflict" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_eligible_student_within_open_window(
    published_quiz: Quiz,
    test_student: User,
    db_session: Session,
):
    assignment = QuizAssignment(
        quiz_id=published_quiz.id,
        student_prn="202401110001",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        assigned_student_id=test_student.id,
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_eligible"] is True
        assert data["is_open"] is True
        assert data["student_prn"] == "202401110001"
        assert data["quiz_title"] == "Algorithms Final Exam"
        assert data["duration_minutes"] == 90
        assert data["status_message"] == "Assessment is currently open."


@pytest.mark.asyncio
async def test_eligible_student_outside_window(
    test_teacher: User,
    test_student: User,
    db_session: Session,
):
    # Scheduled for tomorrow
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Future Scheduled Quiz",
        course_code="CS401",
        created_by_id=test_teacher.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz)
    db_session.flush()

    now = datetime.now(timezone.utc)
    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        version_number=1,
        title=quiz.title,
        is_published=True,
        opens_at=now + timedelta(days=1),
        closes_at=now + timedelta(days=2),
        duration_minutes=45,
    )
    db_session.add(version)
    quiz.current_version_id = version.id

    assignment = QuizAssignment(
        quiz_id=quiz.id,
        student_prn="202401110001",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        assigned_student_id=test_student.id,
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["is_eligible"] is True
        assert data["is_open"] is False
        assert "scheduled to open" in data["status_message"].lower()


@pytest.mark.asyncio
async def test_auto_bind_unregistered_assignment_on_matching_profile(
    published_quiz: Quiz,
    test_student: User,
    db_session: Session,
):
    # Assignment originally created with assigned_student_id = None
    assignment = QuizAssignment(
        quiz_id=published_quiz.id,
        student_prn="202401110001",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        assigned_student_id=None,
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{published_quiz.id}/eligibility",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["is_eligible"] is True

        # Check DB was safely updated with assigned_student_id
        db_session.refresh(assignment)
        assert assignment.assigned_student_id == test_student.id
