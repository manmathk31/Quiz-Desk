"""Roster and cross-teacher assignment integrity verification tests (DEC-007, Phase 8B)."""
import time
import uuid
import jwt
import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole, StudentProfile
from app.models.quiz import Quiz, QuizStatus
from app.models.roster import QuizAssignment
from app.models.audit import AuditEvent
from app.core.config import settings
from app.core.database import get_db
from app.services.roster_parser import parse_and_validate_roster_file, ParsedRosterRow
from app.services.roster_service import evaluate_roster_candidates, commit_roster_import

TEST_JWT_SECRET = "test-secret-key-hs256-for-roster-integrity-tests-1234567890"

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_test_token(sub: str, email: str = "teacher@college.edu") -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "exp": now + 3600,
        "iat": now,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
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
def teacher_a(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="teacher.a@college.edu",
        name="Prof. Alice",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def teacher_b(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="teacher.b@college.edu",
        name="Prof. Bob",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_x(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="student.x@college.edu",
        name="Student X",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = StudentProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        prn="00123",  # Leading zero string
        current_division="A",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def quiz_a(db_session: Session, teacher_a: User) -> Quiz:
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Physics Quiz A",
        course_code="PHY101",
        created_by_id=teacher_a.id,
        status=QuizStatus.DRAFT,
    )
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)
    return quiz


@pytest.fixture
def quiz_b(db_session: Session, teacher_b: User) -> Quiz:
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Chemistry Quiz B",
        course_code="CH101",
        created_by_id=teacher_b.id,
        status=QuizStatus.DRAFT,
    )
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)
    return quiz


# ==============================================================================
# Roster & Cross-Teacher Enrollment Behavior Tests
# ==============================================================================

def test_cross_teacher_enrollment_success(
    db_session: Session,
    teacher_a: User,
    teacher_b: User,
    quiz_a: Quiz,
    quiz_b: Quiz,
    student_x: User,
):
    """
    Teacher A assigns Student X to Quiz A.
    Teacher B assigns Student X to Quiz B.
    Both assignments must succeed without global enrollment conflict.
    """
    row = ParsedRosterRow(
        row_number=2,
        prn="00123",
        name="Student X",
        email="student.x@college.edu",
        division="A",
    )

    # 1. Teacher A imports student into Quiz A
    res_a = commit_roster_import(
        db=db_session,
        quiz=quiz_a,
        current_user_id=teacher_a.id,
        parsed_rows=[row],
    )
    assert res_a["imported_count"] == 1

    # 2. Teacher B imports same student into Quiz B
    res_b = commit_roster_import(
        db=db_session,
        quiz=quiz_b,
        current_user_id=teacher_b.id,
        parsed_rows=[row],
    )
    assert res_b["imported_count"] == 1

    # Verify both assignments exist independently
    assign_a = db_session.query(QuizAssignment).filter(QuizAssignment.quiz_id == quiz_a.id).first()
    assign_b = db_session.query(QuizAssignment).filter(QuizAssignment.quiz_id == quiz_b.id).first()

    assert assign_a is not None
    assert assign_b is not None
    assert assign_a.student_prn == "00123"
    assert assign_b.student_prn == "00123"
    assert assign_a.id != assign_b.id


def test_reimport_same_roster_is_idempotent(
    db_session: Session,
    teacher_a: User,
    quiz_a: Quiz,
    student_x: User,
):
    """
    Re-importing the same student roster for the same quiz must be idempotent
    and not produce duplicate assignment records.
    """
    row = ParsedRosterRow(
        row_number=2,
        prn="00123",
        name="Student X",
        email="student.x@college.edu",
        division="A",
    )

    # First import
    res1 = commit_roster_import(
        db=db_session,
        quiz=quiz_a,
        current_user_id=teacher_a.id,
        parsed_rows=[row],
    )
    assert res1["imported_count"] == 1
    assert db_session.query(QuizAssignment).filter(QuizAssignment.quiz_id == quiz_a.id).count() == 1

    # Second import with updated division
    row_updated = ParsedRosterRow(
        row_number=2,
        prn="00123",
        name="Student X Updated",
        email="student.x@college.edu",
        division="B",
    )
    res2 = commit_roster_import(
        db=db_session,
        quiz=quiz_a,
        current_user_id=teacher_a.id,
        parsed_rows=[row_updated],
    )
    assert res2["imported_count"] == 0
    assert res2["already_assigned_count"] == 1

    # Still only 1 assignment, with updated metadata
    assignments = db_session.query(QuizAssignment).filter(QuizAssignment.quiz_id == quiz_a.id).all()
    assert len(assignments) == 1
    assert assignments[0].division == "B"
    assert assignments[0].student_name == "Student X Updated"


def test_prn_string_leading_zero_preservation():
    """Verify that PRN with leading zeros is parsed as string and preserved."""
    csv_content = b"prn,name,email,division\n00042,Rohan,rohan@college.edu,A\n"
    val_result = parse_and_validate_roster_file(csv_content, "roster.csv")

    assert val_result.is_valid is True
    assert len(val_result.rows) == 1
    assert val_result.rows[0].prn == "00042"
    assert isinstance(val_result.rows[0].prn, str)


def test_identity_conflict_detection_rejects_mismatch(
    db_session: Session,
    teacher_a: User,
    quiz_a: Quiz,
    student_x: User,
):
    """
    If account is registered with PRN '00123', but roster uploads email with PRN '99999',
    it must be flagged as an identity conflict and rejected with 422.
    """
    conflicting_row = ParsedRosterRow(
        row_number=2,
        prn="99999",  # Wrong PRN for student.x@college.edu
        name="Impostor",
        email="student.x@college.edu",
        division="A",
    )

    eval_result = evaluate_roster_candidates(db_session, quiz_a.id, [conflicting_row])
    assert eval_result.conflicts_count == 1
    assert eval_result.can_confirm is False
    assert "Identity conflict" in eval_result.items[0].conflict_reason

    # Commit must raise 422
    with pytest.raises(Exception) as exc_info:
        commit_roster_import(db_session, quiz_a, teacher_a.id, [conflicting_row])
    assert "422" in str(exc_info.value)


@pytest.mark.asyncio
async def test_teacher_cannot_access_other_teacher_roster(
    teacher_a: User,
    teacher_b: User,
    quiz_a: Quiz,
):
    """Teacher B cannot access or modify Teacher A's quiz roster."""
    token_b = make_test_token(sub=str(teacher_b.id), email=teacher_b.email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Teacher B attempts to get Teacher A's quiz roster
        res = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/roster",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
