"""Unit tests for student self-activation endpoint (DEC-018)."""
import time
import uuid
import jwt
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole, StudentProfile
from app.models.quiz import Quiz, QuizStatus
from app.models.roster import QuizAssignment
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-activate-secret-key-hs256-abcdef012345"

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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
def test_quiz_with_unregistered_student(db_session: Session) -> tuple[Quiz, QuizAssignment]:
    teacher = User(
        id=uuid.uuid4(),
        email="prof.test@college.edu",
        name="Prof Test",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)
    db_session.flush()

    quiz = Quiz(
        id=uuid.uuid4(),
        title="Operating Systems Lab Test",
        course_code="CS-301",
        created_by_id=teacher.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz)
    db_session.flush()

    assignment = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        student_prn="202401990001",
        student_email="newstudent@mitaoe.ac.in",
        student_name="New Student",
        division="A",
        assigned_student_id=None,
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    return quiz, assignment


@pytest.mark.asyncio
async def test_student_activate_success(
    test_quiz_with_unregistered_student: tuple[Quiz, QuizAssignment],
    db_session: Session,
):
    _, assignment = test_quiz_with_unregistered_student
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/student-activate",
            json={"email": "newstudent@mitaoe.ac.in", "prn": "202401990001"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "activated"
        user_id = uuid.UUID(data["user_id"])

        # Verify User was created in DB
        user = db_session.scalar(select(User).where(User.id == user_id))
        assert user is not None
        assert user.email == "newstudent@mitaoe.ac.in"
        assert user.name == "New Student"
        assert user.role == UserRole.STUDENT

        # Verify StudentProfile was created
        profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        assert profile is not None
        assert profile.prn == "202401990001"
        assert profile.current_division == "A"

        # Verify QuizAssignment was linked
        db_assignment = db_session.get(QuizAssignment, assignment.id)
        assert db_assignment.assigned_student_id == user.id


@pytest.mark.asyncio
async def test_student_activate_invalid_prn(
    test_quiz_with_unregistered_student: tuple[Quiz, QuizAssignment],
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/student-activate",
            json={"email": "newstudent@mitaoe.ac.in", "prn": "WRONG_PRN"},
        )
        assert res.status_code == 401
        assert "No eligible student assignment found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_student_activate_unregistered_email():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/student-activate",
            json={"email": "nobody@mitaoe.ac.in", "prn": "202401999999"},
        )
        assert res.status_code == 401
