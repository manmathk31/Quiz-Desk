"""Integration tests for Teacher Student Roster and Assignment endpoints (Phase 5)."""
from datetime import datetime, timezone, timedelta
import io
import time
import uuid
import openpyxl
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
from app.models.attempt import QuizAttempt
from app.models.audit import AuditEvent
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-roster-secret-key-hs256-abcdef012345"

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
def other_teacher(db_session: Session) -> User:
    teacher = User(
        id=uuid.uuid4(),
        email="prof.gupta@college.edu",
        name="Prof. Gupta",
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
def test_quiz(db_session: Session, test_teacher: User) -> Quiz:
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Data Structures Midterm",
        course_code="CS201",
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
        is_published=False,
        opens_at=now + timedelta(hours=2),
        closes_at=now + timedelta(days=2),
        duration_minutes=60,
        max_attempts=1,
    )
    db_session.add(version)
    quiz.current_version_id = version.id
    db_session.commit()
    return quiz



@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(test_quiz: Quiz):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/quizzes/{test_quiz.id}/assignments")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_student_denied_teacher_roster_endpoints(test_quiz: Quiz, test_student: User):
    token = make_test_token(str(test_student.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/assignments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_cross_teacher_isolation(test_quiz: Quiz, other_teacher: User):
    token = make_test_token(str(other_teacher.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/assignments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_template_download(test_quiz: Quiz, test_teacher: User):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # CSV template
        res_csv = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/roster/template?format=csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "prn,name,email,division" in res_csv.text

        # XLSX template
        res_xlsx = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/roster/template?format=xlsx",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_xlsx.status_code == 200
        assert "spreadsheetml" in res_xlsx.headers["content-type"]
        assert len(res_xlsx.content) > 100


@pytest.mark.asyncio
async def test_roster_dry_run_preview(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
    db_session: Session,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    # 1 registered matched student, 1 unregistered student, 1 lead zero student
    csv_data = (
        "prn,name,email,division\n"
        "202401110001,Aarav Sharma,aarav.sharma@college.edu,A\n"
        "202401110002,Unregistered Student,unregistered@college.edu,A\n"
        "00123,Lead Zero,lead@college.edu,B\n"
    ).encode("utf-8")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/roster/preview",
            files={"file": ("roster.csv", csv_data, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_rows"] == 3
        assert data["valid_rows"] == 3
        assert data["new_assignments_count"] == 3
        assert data["matched_count"] == 1
        assert data["unregistered_count"] == 2
        assert data["can_confirm"] is True
        assert len(data["items"]) == 3

        # Matched student check
        item0 = data["items"][0]
        assert item0["prn"] == "202401110001"
        assert item0["match_status"] == "matched"
        assert item0["matched_user_id"] == str(test_student.id)

        # Lead zero PRN preserved
        item2 = data["items"][2]
        assert item2["prn"] == "00123"

        # Verify zero DB rows were written by preview
        assignments_count = db_session.scalar(
            select(QuizAssignment).where(QuizAssignment.quiz_id == test_quiz.id)
        )
        assert assignments_count is None


@pytest.mark.asyncio
async def test_confirm_roster_import_transactional(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
    db_session: Session,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    csv_data = (
        "prn,name,email,division\n"
        "202401110001,Aarav Sharma,aarav.sharma@college.edu,A\n"
        "202401110002,Unregistered Student,unreg@college.edu,B\n"
    ).encode("utf-8")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/roster/import",
            files={"file": ("roster.csv", csv_data, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["imported_count"] == 2
        assert data["matched_accounts_count"] == 1
        assert data["unregistered_count"] == 1

        # Check DB records
        assignments = db_session.scalars(
            select(QuizAssignment).where(QuizAssignment.quiz_id == test_quiz.id)
        ).all()
        assert len(assignments) == 2

        matched_a = [a for a in assignments if a.student_prn == "202401110001"][0]
        assert matched_a.assigned_student_id == test_student.id
        assert matched_a.is_active is True

        unreg_a = [a for a in assignments if a.student_prn == "202401110002"][0]
        assert unreg_a.assigned_student_id is None
        assert unreg_a.is_active is True

        # Check AuditEvent was created
        audit = db_session.scalar(
            select(AuditEvent).where(
                AuditEvent.action == "roster_imported",
                AuditEvent.entity_id == str(test_quiz.id),
            )
        )
        assert audit is not None
        assert audit.user_id == test_teacher.id


@pytest.mark.asyncio
async def test_repeated_import_idempotent(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    csv_data = (
        "prn,name,email,division\n"
        "202401110001,Aarav Sharma,aarav.sharma@college.edu,A\n"
    ).encode("utf-8")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First import
        res1 = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/roster/import",
            files={"file": ("roster.csv", csv_data, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res1.status_code == 200
        assert res1.json()["imported_count"] == 1

        # Second import of exact same roster
        res2 = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/roster/import",
            files={"file": ("roster.csv", csv_data, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 200
        assert res2.json()["imported_count"] == 0
        assert res2.json()["already_assigned_count"] == 1


@pytest.mark.asyncio
async def test_confirm_roster_import_rejects_conflicts(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    # test_student has PRN 202401110001. Roster below specifies wrong PRN for that email!
    csv_conflict = (
        "prn,name,email,division\n"
        "WRONG_PRN_999,Aarav Sharma,aarav.sharma@college.edu,A\n"
    ).encode("utf-8")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/roster/import",
            files={"file": ("roster.csv", csv_conflict, "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422
        assert "conflict" in str(res.json()).lower()


@pytest.mark.asyncio
async def test_manual_single_student_assignment_and_conflict(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create single assignment
        res = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/assignments",
            json={
                "prn": "202401110001",
                "name": "Aarav Sharma",
                "email": "aarav.sharma@college.edu",
                "division": "A",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["student_prn"] == "202401110001"
        assert data["is_active"] is True
        assert data["match_status"] == "matched"
        assert data["assigned_student_id"] == str(test_student.id)

        # Duplicate assignment returns 409 Conflict
        res_dup = await client.post(
            f"/api/v1/quizzes/{test_quiz.id}/assignments",
            json={
                "prn": "202401110001",
                "name": "Aarav Sharma",
                "email": "aarav.sharma@college.edu",
                "division": "A",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_dup.status_code == 409


@pytest.mark.asyncio
async def test_assignment_status_revocation_and_reactivation(
    test_quiz: Quiz,
    test_teacher: User,
    db_session: Session,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    # Insert test assignment
    assignment = QuizAssignment(
        quiz_id=test_quiz.id,
        student_prn="PRN100",
        student_name="Test Student",
        student_email="student@college.edu",
        division="A",
        is_active=True,
    )
    db_session.add(assignment)
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Revoke
        res_revoke = await client.patch(
            f"/api/v1/quizzes/{test_quiz.id}/assignments/{assignment.id}/status",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_revoke.status_code == 200
        assert res_revoke.json()["is_active"] is False
        assert res_revoke.json()["revoked_at"] is not None

        # Reactivate
        res_reactivate = await client.patch(
            f"/api/v1/quizzes/{test_quiz.id}/assignments/{assignment.id}/status",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_reactivate.status_code == 200
        assert res_reactivate.json()["is_active"] is True
        assert res_reactivate.json()["revoked_at"] is None


@pytest.mark.asyncio
async def test_assignment_deletion_and_attempt_protection(
    test_quiz: Quiz,
    test_teacher: User,
    test_student: User,
    db_session: Session,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    # Assignment without attempts
    assignment1 = QuizAssignment(
        quiz_id=test_quiz.id,
        student_prn="PRN_NO_ATTEMPT",
        student_name="No Attempt",
        student_email="noattempt@college.edu",
        division="A",
        is_active=True,
    )
    db_session.add(assignment1)

    # Assignment with attempt
    assignment2 = QuizAssignment(
        quiz_id=test_quiz.id,
        student_prn="202401110001",
        student_name="Aarav Sharma",
        student_email="aarav.sharma@college.edu",
        division="A",
        assigned_student_id=test_student.id,
        is_active=True,
    )
    db_session.add(assignment2)
    db_session.flush()

    # Add an attempt for student2
    attempt = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=test_quiz.current_version_id,
        student_id=test_student.id,
        attempt_number=1,
        started_at=datetime.now(timezone.utc),
        deadline_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    db_session.add(attempt)
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Deleting assignment1 (no attempts) succeeds with 204
        res_del1 = await client.delete(
            f"/api/v1/quizzes/{test_quiz.id}/assignments/{assignment1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_del1.status_code == 204

        # Deleting assignment2 (has attempts) rejected with 400 Bad Request
        res_del2 = await client.delete(
            f"/api/v1/quizzes/{test_quiz.id}/assignments/{assignment2.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_del2.status_code == 400
        assert "existing assessment attempts" in res_del2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_and_filter_assignments(
    test_quiz: Quiz,
    test_teacher: User,
    db_session: Session,
):
    token = make_test_token(str(test_teacher.id))
    transport = ASGITransport(app=app)

    db_session.add_all([
        QuizAssignment(quiz_id=test_quiz.id, student_prn="PRN01", student_name="Alice Brown", student_email="alice@c.edu", division="A", is_active=True),
        QuizAssignment(quiz_id=test_quiz.id, student_prn="PRN02", student_name="Bob Clark", student_email="bob@c.edu", division="B", is_active=False),
        QuizAssignment(quiz_id=test_quiz.id, student_prn="PRN03", student_name="Charlie Davis", student_email="charlie@c.edu", division="A", is_active=True),
    ])
    db_session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter by division A
        res_div = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/assignments?division=A",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_div.status_code == 200
        data = res_div.json()
        assert data["total_count"] == 2
        assert all(it["division"] == "A" for it in data["items"])

        # Filter by is_active=False
        res_revoked = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/assignments?is_active=false",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_revoked.status_code == 200
        assert res_revoked.json()["total_count"] == 1
        assert res_revoked.json()["items"][0]["student_prn"] == "PRN02"

        # Search term "Alice"
        res_search = await client.get(
            f"/api/v1/quizzes/{test_quiz.id}/assignments?search=Alice",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_search.status_code == 200
        assert res_search.json()["total_count"] == 1
        assert res_search.json()["items"][0]["student_name"] == "Alice Brown"
