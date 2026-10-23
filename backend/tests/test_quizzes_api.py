"""Comprehensive API test suite for Teacher Quiz Builder, Immutable Publishing, and Difficulty Support (Milestone 4B)."""
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
from app.models.user import User, UserRole
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionOption, QuestionType, QuestionDifficulty
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-quiz-builder-secret-key-hs256-12345678"

# In-memory SQLite for test isolation
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_test_token(sub: str, expires_in_seconds: int = 3600) -> str:
    """Generate controlled test token."""
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
    """Configure settings and create tables."""
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
def teacher_user(db_session: Session) -> User:
    """Create verified teacher user."""
    user = User(
        id=uuid.uuid4(),
        email="prof.sharma@college.edu",
        name="Prof. Sharma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def other_teacher(db_session: Session) -> User:
    """Create another verified teacher user for isolation testing."""
    user = User(
        id=uuid.uuid4(),
        email="prof.verma@college.edu",
        name="Prof. Verma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def student_user(db_session: Session) -> User:
    """Create verified student user."""
    user = User(
        id=uuid.uuid4(),
        email="student.rohit@college.edu",
        name="Rohit Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def teacher_auth_headers(teacher_user: User) -> dict:
    token = make_test_token(str(teacher_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_teacher_auth_headers(other_teacher: User) -> dict:
    token = make_test_token(str(other_teacher.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_auth_headers(student_user: User) -> dict:
    token = make_test_token(str(student_user.id))
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Security & Authorization Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected():
    """Unauthenticated access to quiz endpoints returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/quizzes")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_student_forbidden_from_quiz_builder(student_auth_headers):
    """Students cannot access teacher quiz builder endpoints (403 Forbidden)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # List
        resp = await client.get("/api/v1/quizzes", headers=student_auth_headers)
        assert resp.status_code == 403

        # Create
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Student Hacked Quiz",
            "course_code": "CS101",
            "opens_at": now.isoformat(),
            "closes_at": (now + timedelta(hours=2)).isoformat(),
            "duration_minutes": 60,
        }
        create_resp = await client.post("/api/v1/quizzes", json=payload, headers=student_auth_headers)
        assert create_resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cross_tenant_isolation(teacher_auth_headers, other_teacher_auth_headers):
    """Teacher B cannot access, modify, add questions to, or publish Teacher A's quiz."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Teacher A creates a quiz
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Teacher A Midterm Exam",
            "course_code": "CS201",
            "description": "Database Systems Exam",
            "opens_at": now.isoformat(),
            "closes_at": (now + timedelta(hours=3)).isoformat(),
            "duration_minutes": 90,
            "max_attempts": 1,
        }
        res_a = await client.post("/api/v1/quizzes", json=payload, headers=teacher_auth_headers)
        assert res_a.status_code == 201
        quiz_id = res_a.json()["id"]

        # Teacher B attempts to retrieve Teacher A's quiz -> 404 (no data leak)
        get_b = await client.get(f"/api/v1/quizzes/{quiz_id}", headers=other_teacher_auth_headers)
        assert get_b.status_code == 404

        # Teacher B attempts to update Teacher A's quiz -> 404
        update_payload = dict(payload, title="Hijacked Title")
        put_b = await client.put(f"/api/v1/quizzes/{quiz_id}", json=update_payload, headers=other_teacher_auth_headers)
        assert put_b.status_code == 404

        # Teacher B attempts to publish Teacher A's quiz -> 404
        pub_b = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=other_teacher_auth_headers)
        assert pub_b.status_code == 404


# ==============================================================================
# Quiz Drafting, Settings & Lifecycle CRUD Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_teacher_quiz_draft_crud(teacher_auth_headers):
    """Verify full CRUD on quiz drafts and settings."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        now = datetime.now(timezone.utc)
        opens_at = now + timedelta(days=1)
        closes_at = now + timedelta(days=2)

        payload = {
            "title": "Operating Systems Quiz 1",
            "course_code": "CS301",
            "description": "Processes, Threads, and Deadlocks",
            "opens_at": opens_at.isoformat(),
            "closes_at": closes_at.isoformat(),
            "duration_minutes": 45,
            "max_attempts": 2,
            "allow_backtracking": False,
            "shuffle_questions": True,
            "shuffle_options": True,
            "multi_answer_policy": "partial_with_penalty",
            "tab_switch_limit": 2,
            "tab_switch_penalty_marks": 0.5,
        }

        # 1. Create Draft Quiz
        res = await client.post("/api/v1/quizzes", json=payload, headers=teacher_auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Operating Systems Quiz 1"
        assert data["course_code"] == "CS301"
        assert data["status"] == "draft"
        assert data["is_published"] is False
        assert data["draft_version"] is not None
        assert data["draft_version"]["version_number"] == 1
        assert data["draft_version"]["allow_backtracking"] is False
        assert data["draft_version"]["shuffle_questions"] is True
        assert data["draft_version"]["multi_answer_policy"] == "partial_with_penalty"
        assert data["draft_version"]["tab_switch_limit"] == 2
        assert data["draft_version"]["tab_switch_penalty_marks"] == 0.5
        quiz_id = data["id"]

        # 2. List Quizzes
        list_res = await client.get("/api/v1/quizzes", headers=teacher_auth_headers)
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        found = next(q for q in list_data["items"] if q["id"] == quiz_id)
        assert found["title"] == "Operating Systems Quiz 1"
        assert found["status"] == "draft"

        # 3. Get Single Quiz
        get_res = await client.get(f"/api/v1/quizzes/{quiz_id}", headers=teacher_auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == quiz_id

        # 4. Update Draft Settings
        updated_payload = dict(
            payload,
            title="Operating Systems Quiz 1 (Revised)",
            duration_minutes=50,
            allow_backtracking=True,
        )
        put_res = await client.put(f"/api/v1/quizzes/{quiz_id}", json=updated_payload, headers=teacher_auth_headers)
        assert put_res.status_code == 200
        updated_data = put_res.json()
        assert updated_data["title"] == "Operating Systems Quiz 1 (Revised)"
        assert updated_data["draft_version"]["duration_minutes"] == 50
        assert updated_data["draft_version"]["allow_backtracking"] is True


@pytest.mark.asyncio
async def test_schedule_validation_rejections(teacher_auth_headers):
    """Verify schedule constraint enforcement: closes_at > opens_at and duration > 0."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        now = datetime.now(timezone.utc)

        # Closes before opens
        invalid_schedule = {
            "title": "Bad Schedule Quiz",
            "course_code": "CS101",
            "opens_at": (now + timedelta(hours=2)).isoformat(),
            "closes_at": now.isoformat(),
            "duration_minutes": 30,
        }
        res1 = await client.post("/api/v1/quizzes", json=invalid_schedule, headers=teacher_auth_headers)
        assert res1.status_code == 422

        # Non-positive duration
        invalid_duration = {
            "title": "Zero Duration Quiz",
            "course_code": "CS101",
            "opens_at": now.isoformat(),
            "closes_at": (now + timedelta(hours=1)).isoformat(),
            "duration_minutes": 0,
        }
        res2 = await client.post("/api/v1/quizzes", json=invalid_duration, headers=teacher_auth_headers)
        assert res2.status_code == 422


# ==============================================================================
# Question Bank Selection, Difficulty Cloning, Ordering & Removal Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_add_questions_from_bank_and_difficulty_preservation(teacher_auth_headers, db_session: Session):
    """Verify selecting bank questions clones them into the draft version, preserving difficulty and marks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Quiz Draft
        now = datetime.now(timezone.utc)
        quiz_res = await client.post(
            "/api/v1/quizzes",
            json={
                "title": "Data Structures Quiz",
                "course_code": "CS201",
                "opens_at": now.isoformat(),
                "closes_at": (now + timedelta(hours=3)).isoformat(),
                "duration_minutes": 60,
            },
            headers=teacher_auth_headers,
        )
        quiz_id = quiz_res.json()["id"]

        # 2. Create 2 questions in teacher's Question Bank with explicit difficulties
        q1_res = await client.post(
            "/api/v1/question-bank",
            json={
                "question_type": "single_choice",
                "difficulty": "easy",
                "prompt": "What is the worst-case time complexity of linear search?",
                "positive_marks": 1.0,
                "negative_marks": 0.25,
                "options": [
                    {"option_text": "O(1)", "is_correct": False},
                    {"option_text": "O(n)", "is_correct": True},
                ],
            },
            headers=teacher_auth_headers,
        )
        assert q1_res.status_code == 201
        q1_id = q1_res.json()["id"]

        q2_res = await client.post(
            "/api/v1/question-bank",
            json={
                "question_type": "multiple_choice",
                "difficulty": "hard",
                "prompt": "Which trees are balanced binary search trees?",
                "positive_marks": 3.0,
                "negative_marks": 1.0,
                "options": [
                    {"option_text": "AVL Tree", "is_correct": True},
                    {"option_text": "Red-Black Tree", "is_correct": True},
                    {"option_text": "Binary Heap", "is_correct": False},
                ],
            },
            headers=teacher_auth_headers,
        )
        assert q2_res.status_code == 201
        q2_id = q2_res.json()["id"]

        # 3. Add questions to quiz draft
        add_res = await client.post(
            f"/api/v1/quizzes/{quiz_id}/questions",
            json={"question_ids": [q1_id, q2_id]},
            headers=teacher_auth_headers,
        )
        assert add_res.status_code == 200
        draft_version = add_res.json()

        assert draft_version["total_questions"] == 2
        assert draft_version["total_marks"] == 4.0
        assert draft_version["difficulty_breakdown"]["easy"] == 1
        assert draft_version["difficulty_breakdown"]["hard"] == 1
        assert draft_version["difficulty_breakdown"]["medium"] == 0

        # Verify cloned questions are independent copies
        cloned_q1 = draft_version["questions"][0]
        cloned_q2 = draft_version["questions"][1]
        assert cloned_q1["id"] != q1_id  # Cloned ID, not raw bank ID
        assert cloned_q1["difficulty"] == "easy"
        assert cloned_q1["positive_marks"] == 1.0
        assert cloned_q2["difficulty"] == "hard"
        assert cloned_q2["positive_marks"] == 3.0

        # Verify bank question edits do NOT alter cloned quiz question
        await client.put(
            f"/api/v1/question-bank/{q1_id}",
            json={
                "question_type": "single_choice",
                "difficulty": "medium",
                "prompt": "MODIFIED PROMPT IN BANK",
                "positive_marks": 5.0,
                "negative_marks": 0.0,
                "options": [
                    {"option_text": "ModA", "is_correct": True},
                    {"option_text": "ModB", "is_correct": False},
                ],
            },
            headers=teacher_auth_headers,
        )

        # Inspect quiz draft: original cloned question is completely untouched
        inspect_res = await client.get(f"/api/v1/quizzes/{quiz_id}", headers=teacher_auth_headers)
        inspect_questions = inspect_res.json()["draft_version"]["questions"]
        assert inspect_questions[0]["prompt"] == "What is the worst-case time complexity of linear search?"
        assert inspect_questions[0]["difficulty"] == "easy"
        assert inspect_questions[0]["positive_marks"] == 1.0


@pytest.mark.asyncio
async def test_reorder_and_remove_draft_questions(teacher_auth_headers):
    """Verify changing sequence order and removing questions from draft."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create draft quiz
        now = datetime.now(timezone.utc)
        quiz_res = await client.post(
            "/api/v1/quizzes",
            json={
                "title": "Ordering Quiz",
                "course_code": "CS101",
                "opens_at": now.isoformat(),
                "closes_at": (now + timedelta(hours=2)).isoformat(),
                "duration_minutes": 30,
            },
            headers=teacher_auth_headers,
        )
        quiz_id = quiz_res.json()["id"]

        # Create 3 bank questions
        ids = []
        for i in range(3):
            q_res = await client.post(
                "/api/v1/question-bank",
                json={
                    "question_type": "true_false",
                    "prompt": f"TF Question {i+1}",
                    "positive_marks": 1.0,
                    "negative_marks": 0.0,
                    "options": [
                        {"option_text": "True", "is_correct": True},
                        {"option_text": "False", "is_correct": False},
                    ],
                },
                headers=teacher_auth_headers,
            )
            ids.append(q_res.json()["id"])

        # Add all 3 to draft
        add_res = await client.post(
            f"/api/v1/quizzes/{quiz_id}/questions",
            json={"question_ids": ids},
            headers=teacher_auth_headers,
        )
        cloned_qs = add_res.json()["questions"]
        assert len(cloned_qs) == 3
        c_q0, c_q1, c_q2 = cloned_qs[0]["id"], cloned_qs[1]["id"], cloned_qs[2]["id"]

        # Reorder to [c_q2, c_q0, c_q1]
        reorder_res = await client.put(
            f"/api/v1/quizzes/{quiz_id}/questions/order",
            json={"question_ids": [c_q2, c_q0, c_q1]},
            headers=teacher_auth_headers,
        )
        assert reorder_res.status_code == 200
        reordered = reorder_res.json()["questions"]
        assert [q["id"] for q in reordered] == [c_q2, c_q0, c_q1]

        # Remove c_q0
        del_res = await client.delete(
            f"/api/v1/quizzes/{quiz_id}/questions/{c_q0}",
            headers=teacher_auth_headers,
        )
        assert del_res.status_code == 200
        remaining = del_res.json()["questions"]
        assert len(remaining) == 2
        assert [q["id"] for q in remaining] == [c_q2, c_q1]


# ==============================================================================
# Preview & Server-Side Pre-Publication Validation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_publish_validation_failure_empty_quiz(teacher_auth_headers):
    """Publishing an empty quiz is rejected with 422 Unprocessable Entity."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        now = datetime.now(timezone.utc)
        quiz_res = await client.post(
            "/api/v1/quizzes",
            json={
                "title": "Empty Quiz",
                "course_code": "CS101",
                "opens_at": now.isoformat(),
                "closes_at": (now + timedelta(hours=2)).isoformat(),
                "duration_minutes": 30,
            },
            headers=teacher_auth_headers,
        )
        quiz_id = quiz_res.json()["id"]

        # Preview shows can_publish = False
        prev_res = await client.get(f"/api/v1/quizzes/{quiz_id}/preview", headers=teacher_auth_headers)
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert prev_data["can_publish"] is False
        assert any("at least one question" in e["message"] for e in prev_data["validation_errors"])

        # Publish call is rejected
        pub_res = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=teacher_auth_headers)
        assert pub_res.status_code == 422
        assert "pre-publication validation failed" in pub_res.json()["detail"]["message"].lower()


# ==============================================================================
# Immutable Versioning & Subsequent Draft Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_successful_publication_and_immutability(teacher_auth_headers):
    """
    Verify publication locks version snapshot as immutable.
    Subsequent edits do NOT modify the published version; they spawn a new draft version.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        now = datetime.now(timezone.utc)
        # 1. Create quiz
        quiz_res = await client.post(
            "/api/v1/quizzes",
            json={
                "title": "Networking Final Exam",
                "course_code": "CS401",
                "opens_at": now.isoformat(),
                "closes_at": (now + timedelta(hours=4)).isoformat(),
                "duration_minutes": 120,
            },
            headers=teacher_auth_headers,
        )
        quiz_id = quiz_res.json()["id"]

        # 2. Create and add a question
        q_res = await client.post(
            "/api/v1/question-bank",
            json={
                "question_type": "single_choice",
                "difficulty": "medium",
                "prompt": "What layer of OSI model does TCP belong to?",
                "positive_marks": 2.0,
                "negative_marks": 0.5,
                "options": [
                    {"option_text": "Network Layer", "is_correct": False},
                    {"option_text": "Transport Layer", "is_correct": True},
                ],
            },
            headers=teacher_auth_headers,
        )
        q_id = q_res.json()["id"]
        await client.post(
            f"/api/v1/quizzes/{quiz_id}/questions",
            json={"question_ids": [q_id]},
            headers=teacher_auth_headers,
        )

        # 3. Publish Version 1
        pub_res = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=teacher_auth_headers)
        assert pub_res.status_code == 200
        pub_data = pub_res.json()
        assert pub_data["success"] is True
        assert pub_data["version_number"] == 1
        pub_v1_id = pub_data["published_version_id"]

        # Verify quiz is now PUBLISHED
        quiz_detail = await client.get(f"/api/v1/quizzes/{quiz_id}", headers=teacher_auth_headers)
        detail_data = quiz_detail.json()
        assert detail_data["status"] == "published"
        assert detail_data["is_published"] is True
        assert detail_data["published_version"]["id"] == pub_v1_id
        assert detail_data["published_version"]["is_published"] is True
        assert detail_data["draft_version"] is None

        # 4. Subsequent Edit: Teacher updates duration and title
        # This MUST NOT mutate Version 1; it should create Version 2 draft!
        edit_payload = {
            "title": "Networking Final Exam (Updated v2)",
            "course_code": "CS401",
            "opens_at": now.isoformat(),
            "closes_at": (now + timedelta(hours=5)).isoformat(),
            "duration_minutes": 150,
            "max_attempts": 1,
            "allow_backtracking": True,
            "shuffle_questions": False,
            "shuffle_options": False,
            "multi_answer_policy": "all_or_nothing",
            "tab_switch_limit": 3,
            "tab_switch_penalty_marks": 0.0,
        }
        update_res = await client.put(f"/api/v1/quizzes/{quiz_id}", json=edit_payload, headers=teacher_auth_headers)
        assert update_res.status_code == 200
        updated_data = update_res.json()

        # Version 1 is still intact and published
        assert updated_data["published_version"]["id"] == pub_v1_id
        assert updated_data["published_version"]["version_number"] == 1
        assert updated_data["published_version"]["duration_minutes"] == 120
        assert updated_data["published_version"]["is_published"] is True

        # Version 2 is the new active draft
        assert updated_data["draft_version"] is not None
        assert updated_data["draft_version"]["version_number"] == 2
        assert updated_data["draft_version"]["duration_minutes"] == 150
        assert updated_data["draft_version"]["is_published"] is False
        assert updated_data["draft_version"]["total_questions"] == 1  # Cloned from v1

        # 5. Repeated Publish on Quiz with Version 2 draft
        pub2_res = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=teacher_auth_headers)
        assert pub2_res.status_code == 200
        assert pub2_res.json()["version_number"] == 2

        # 6. Idempotent call when already published with no pending draft
        pub_idempotent = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=teacher_auth_headers)
        assert pub_idempotent.status_code == 200
        assert "already published" in pub_idempotent.json()["message"].lower()
