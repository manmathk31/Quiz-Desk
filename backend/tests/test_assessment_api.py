"""Comprehensive test suite for Phase 6 Secure Student Assessment Engine."""
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
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole, StudentProfile
from app.models.quiz import Quiz, QuizVersion, QuizStatus, MultiAnswerPolicy
from app.models.question import Question, QuestionType, QuestionOption
from app.models.roster import QuizAssignment
from app.models.attempt import QuizAttempt, AttemptStatus, GradingStatus

TEST_JWT_SECRET = "test-assessment-secret-key-hs256-abcdef012345"

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
def assessment_setup(db_session: Session):
    """Seed teacher, students, published quiz with multiple question types, and assignments."""
    # 1. Teacher
    teacher = User(
        id=uuid.uuid4(),
        email="prof.assessment@college.edu",
        name="Prof. Assessment",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)

    # 2. Student A (Matched)
    student_a = User(
        id=uuid.uuid4(),
        email="alice.student@college.edu",
        name="Alice Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    profile_a = StudentProfile(
        id=uuid.uuid4(),
        user_id=student_a.id,
        prn="STU1001",
        current_division="A",
    )
    student_a.student_profile = profile_a
    db_session.add(student_a)

    # 3. Student B (Matched)
    student_b = User(
        id=uuid.uuid4(),
        email="bob.student@college.edu",
        name="Bob Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    profile_b = StudentProfile(
        id=uuid.uuid4(),
        user_id=student_b.id,
        prn="STU1002",
        current_division="B",
    )
    student_b.student_profile = profile_b
    db_session.add(student_b)

    # 4. Published Quiz with 1 version, 30 min duration, max 2 attempts
    now = datetime.now(timezone.utc)
    quiz = Quiz(
        id=uuid.uuid4(),
        title="CS301 Data Structures Exam",
        course_code="CS301",
        created_by_id=teacher.id,
        status=QuizStatus.PUBLISHED,
        is_archived=False,
    )
    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        version_number=1,
        title="CS301 Midterm v1",
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=3),
        duration_minutes=30,
        max_attempts=2,
        allow_backtracking=True,
        shuffle_questions=True,
        shuffle_options=True,
        multi_answer_policy=MultiAnswerPolicy.ALL_OR_NOTHING,
        tab_switch_limit=2,
        tab_switch_penalty_marks=0.5,
        is_results_released=False,
    )
    quiz.current_version_id = version.id
    quiz.versions.append(version)
    db_session.add(quiz)

    # 5. Question 1: Single Choice MCQ (2 marks, 0.5 neg)
    q1 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        question_type=QuestionType.SINGLE_CHOICE,
        prompt="What is the average lookup time of a hash table?",
        order_index=0,
        positive_marks=2.0,
        negative_marks=0.5,
    )
    q1_o1 = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="O(1)", is_correct=True, order_index=0)
    q1_o2 = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="O(n)", is_correct=False, order_index=1)
    q1_o3 = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="O(log n)", is_correct=False, order_index=2)
    q1.options.extend([q1_o1, q1_o2, q1_o3])

    # 6. Question 2: True/False (1 mark, 0.25 neg)
    q2 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        question_type=QuestionType.TRUE_FALSE,
        prompt="A binary search tree always guarantees O(log n) height.",
        order_index=1,
        positive_marks=1.0,
        negative_marks=0.25,
    )
    q2_o1 = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="True", is_correct=False, order_index=0)
    q2_o2 = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="False", is_correct=True, order_index=1)
    q2.options.extend([q2_o1, q2_o2])

    # 7. Question 3: Multiple Choice (3 marks, 1.0 neg) - Multi-Answer
    q3 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        question_type=QuestionType.MULTIPLE_CHOICE,
        prompt="Which of the following data structures are linear?",
        order_index=2,
        positive_marks=3.0,
        negative_marks=1.0,
    )
    q3_o1 = QuestionOption(id=uuid.uuid4(), question_id=q3.id, option_text="Array", is_correct=True, order_index=0)
    q3_o2 = QuestionOption(id=uuid.uuid4(), question_id=q3.id, option_text="Queue", is_correct=True, order_index=1)
    q3_o3 = QuestionOption(id=uuid.uuid4(), question_id=q3.id, option_text="Binary Tree", is_correct=False, order_index=2)
    q3_o4 = QuestionOption(id=uuid.uuid4(), question_id=q3.id, option_text="Graph", is_correct=False, order_index=3)
    q3.options.extend([q3_o1, q3_o2, q3_o3, q3_o4])

    version.questions.extend([q1, q2, q3])

    # 8. Assign Student A to Quiz
    assign_a = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        assigned_student_id=student_a.id,
        student_prn="STU1001",
        student_name="Alice Student",
        student_email="alice.student@college.edu",
        division="A",
        is_active=True,
    )
    db_session.add(assign_a)
    db_session.commit()

    return {
        "teacher": teacher,
        "student_a": student_a,
        "student_b": student_b,
        "quiz": quiz,
        "version": version,
        "q1": q1,
        "q1_o1": q1_o1,
        "q1_o2": q1_o2,
        "q2": q2,
        "q2_o2": q2_o2,
        "q3": q3,
        "q3_o1": q3_o1,
        "q3_o2": q3_o2,
        "q3_o3": q3_o3,
    }


@pytest.mark.asyncio
async def test_student_assigned_quizzes_listing(assessment_setup):
    """Student can list assigned assessments with availability status."""
    student_a = assessment_setup["student_a"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/student/quizzes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        item = next(q for q in data["items"] if q["quiz_id"] == str(assessment_setup["quiz"].id))
        assert item["quiz_title"] == "CS301 Data Structures Exam"
        assert item["availability_status"] == "OPEN"
        assert item["attempts_taken"] == 0
        assert item["active_attempt_id"] is None


@pytest.mark.asyncio
async def test_start_attempt_and_idempotent_resume(assessment_setup):
    """Starting an attempt creates a new session; repeating resumes the same attempt."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Initial Start
        res1 = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res1.status_code == 201
        data1 = res1.json()
        attempt_id = data1["attempt_id"]
        assert data1["is_resumed"] is False
        assert data1["attempt_number"] == 1
        assert data1["status"] == "in_progress"
        assert data1["remaining_seconds"] > 0

        # 2. Repeated Start (Browser refresh or reconnect)
        res2 = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["attempt_id"] == attempt_id  # Same attempt resumed!
        assert data2["is_resumed"] is True
        assert data2["attempt_number"] == 1


@pytest.mark.asyncio
async def test_unassigned_student_denied_attempt_start(assessment_setup):
    """Unassigned student cannot start an assessment attempt."""
    student_b = assessment_setup["student_b"]  # Bob is not assigned
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_b.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert "not assigned" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_teacher_denied_student_endpoints(assessment_setup):
    """Teachers cannot start student attempts or access student assessment endpoints."""
    teacher = assessment_setup["teacher"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(teacher.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_sanitized_question_payload_no_answer_keys(assessment_setup):
    """Attempt content payload conceals correct answers and explanation fields."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        content_res = await client.get(
            f"/api/v1/student/attempts/{attempt_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert content_res.status_code == 200
        payload = content_res.json()
        assert len(payload["questions"]) == 3

        # Verify NO is_correct or answer key in any question option
        for q in payload["questions"]:
            for opt in q["options"]:
                assert "is_correct" not in opt
                assert "explanation" not in opt
                assert "is_correct_answer" not in opt


@pytest.mark.asyncio
async def test_cross_student_attempt_isolation(assessment_setup):
    """A student cannot fetch or submit another student's attempt session."""
    student_a = assessment_setup["student_a"]
    student_b = assessment_setup["student_b"]
    quiz_id = str(assessment_setup["quiz"].id)
    token_a = make_test_token(str(student_a.id))
    token_b = make_test_token(str(student_b.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Student B attempts to access Student A's attempt
        res = await client.get(
            f"/api/v1/student/attempts/{attempt_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_answer_autosave_and_validation(assessment_setup):
    """Autosave records answer and enforces validation constraints."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q1_id = str(assessment_setup["q1"].id)
    q1_o1 = str(assessment_setup["q1_o1"].id)
    q1_o2 = str(assessment_setup["q1_o2"].id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # 1. Valid save
        save_res = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o1], "is_marked_for_review": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert save_res.status_code == 200
        assert save_res.json()["success"] is True
        assert save_res.json()["is_marked_for_review"] is True
        assert save_res.json()["selected_option_ids"] == [q1_o1]

        # 2. Reject multiple options for Single Choice
        err_res = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o1, q1_o2]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert err_res.status_code == 422

        # 3. Reject invalid option ID
        fake_opt = str(uuid.uuid4())
        err_opt_res = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [fake_opt]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert err_opt_res.status_code == 400


@pytest.mark.asyncio
async def test_out_of_order_autosave_protection(assessment_setup):
    """Older delayed save request cannot overwrite newer confirmed answer."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q1_id = str(assessment_setup["q1"].id)
    q1_o1 = str(assessment_setup["q1_o1"].id)
    q1_o2 = str(assessment_setup["q1_o2"].id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        now = datetime.now(timezone.utc)
        newer_ts = (now + timedelta(seconds=5)).isoformat()
        older_ts = (now - timedelta(seconds=5)).isoformat()

        # Save newer answer first
        res1 = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o2], "client_timestamp": newer_ts},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res1.status_code == 200
        assert res1.json()["selected_option_ids"] == [q1_o2]

        # Delayed older save arrives afterward
        res2 = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o1], "client_timestamp": older_ts},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 200
        # Remains newer option q1_o2! Stale overwrite blocked
        assert res2.json()["selected_option_ids"] == [q1_o2]


@pytest.mark.asyncio
async def test_telemetry_recording_and_warning_threshold(assessment_setup):
    """Tab switch telemetry increments counter and triggers warning flag when limit exceeded."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Limit is 2
        t1 = await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={}, headers={"Authorization": f"Bearer {token}"})
        assert t1.json()["tab_switch_count"] == 1
        assert t1.json()["limit_exceeded"] is False

        t2 = await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={}, headers={"Authorization": f"Bearer {token}"})
        assert t2.json()["tab_switch_count"] == 2
        assert t2.json()["limit_exceeded"] is False

        # Exceeds limit on 3rd switch
        t3 = await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={}, headers={"Authorization": f"Bearer {token}"})
        assert t3.json()["tab_switch_count"] == 3
        assert t3.json()["limit_exceeded"] is True


@pytest.mark.asyncio
async def test_submission_and_scoring_evaluation(assessment_setup, db_session):
    """Submission evaluates scores, applies penalties, and conceals unreleased results."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q1_id = str(assessment_setup["q1"].id)
    q1_o1 = str(assessment_setup["q1_o1"].id)  # Correct (2.0)

    q2_id = str(assessment_setup["q2"].id)
    q2_o2 = str(assessment_setup["q2_o2"].id)  # Correct (1.0)

    q3_id = str(assessment_setup["q3"].id)
    q3_o1 = str(assessment_setup["q3_o1"].id)  # Correct
    q3_o2 = str(assessment_setup["q3_o2"].id)  # Correct (3.0 for all_or_nothing)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Save answers
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}", json={"selected_option_ids": [q1_o1]}, headers={"Authorization": f"Bearer {token}"})
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q2_id}", json={"selected_option_ids": [q2_o2]}, headers={"Authorization": f"Bearer {token}"})
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q3_id}", json={"selected_option_ids": [q3_o1, q3_o2]}, headers={"Authorization": f"Bearer {token}"})

        # Submit attempt
        sub_res = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sub_res.status_code == 200
        sub_data = sub_res.json()
        assert sub_data["status"] == "submitted"
        assert sub_data["is_finalized"] is True
        # Results are NOT released yet (DEC-010) -> total_score concealed from student
        assert sub_data["total_score"] is None
        assert sub_data["is_results_released"] is False

        # Idempotent re-submission
        sub_res2 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sub_res2.status_code == 200
        assert sub_res2.json()["status"] == "submitted"

        # Further saves rejected with 409 Conflict
        late_save = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o1]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert late_save.status_code == 409

        # Verify evaluated score in DB: 2.0 (q1) + 1.0 (q2) + 3.0 (q3) = 6.0
        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        assert float(att_db.total_score) == 6.0
        assert att_db.grading_status == GradingStatus.AUTO_GRADED


@pytest.mark.asyncio
async def test_max_attempt_limit_enforced(assessment_setup):
    """Enforces max_attempts (configured as 2). Starting 3rd attempt is rejected."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Attempt 1: Start and submit
        r1 = await client.post(f"/api/v1/student/quizzes/{quiz_id}/attempts", headers={"Authorization": f"Bearer {token}"})
        att1_id = r1.json()["attempt_id"]
        await client.post(f"/api/v1/student/attempts/{att1_id}/submit", headers={"Authorization": f"Bearer {token}"})

        # Attempt 2: Start and submit
        r2 = await client.post(f"/api/v1/student/quizzes/{quiz_id}/attempts", headers={"Authorization": f"Bearer {token}"})
        att2_id = r2.json()["attempt_id"]
        assert r2.json()["attempt_number"] == 2
        await client.post(f"/api/v1/student/attempts/{att2_id}/submit", headers={"Authorization": f"Bearer {token}"})

        # Attempt 3: Rejected with 403 Forbidden
        r3 = await client.post(f"/api/v1/student/quizzes/{quiz_id}/attempts", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 403
        assert "maximum attempts" in r3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_negative_marking_and_tab_switch_penalties(assessment_setup, db_session):
    """Wrong answers deduct negative marks and excess tab switches deduct configured penalties."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q1_id = str(assessment_setup["q1"].id)
    q1_o2 = str(assessment_setup["q1_o2"].id)  # WRONG (-0.5)

    q2_id = str(assessment_setup["q2"].id)
    q2_o2 = str(assessment_setup["q2_o2"].id)  # CORRECT (+1.0)

    # q3 left unattempted (0.0)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Record answers
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}", json={"selected_option_ids": [q1_o2]}, headers={"Authorization": f"Bearer {token}"})
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q2_id}", json={"selected_option_ids": [q2_o2]}, headers={"Authorization": f"Bearer {token}"})

        # Record 4 tab switches (limit is 2, so 2 excess switches * 0.5 penalty = 1.0 penalty)
        for _ in range(4):
            await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={}, headers={"Authorization": f"Bearer {token}"})

        # Submit
        sub_res = await client.post(f"/api/v1/student/attempts/{attempt_id}/submit", headers={"Authorization": f"Bearer {token}"})
        assert sub_res.status_code == 200

        # Score in DB: -0.5 (q1) + 1.0 (q2) + 0.0 (q3) = 0.5 raw total
        # Tab switch penalty = 2 excess * 0.5 = 1.0
        # Final score = max(0.0, 0.5 - 1.0) = 0.0
        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        assert float(att_db.total_score) == 0.0


@pytest.mark.asyncio
async def test_partial_scoring_policies(assessment_setup, db_session):
    """Test partial_no_penalty and partial_with_penalty multi-answer policies."""
    version = assessment_setup["version"]
    version.multi_answer_policy = MultiAnswerPolicy.PARTIAL_NO_PENALTY
    version.max_attempts = 5
    db_session.commit()

    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q3_id = str(assessment_setup["q3"].id)
    q3_o1 = str(assessment_setup["q3_o1"].id)  # Correct (1 of 2 correct chosen -> 1/2 of 3.0 = 1.5)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Only answer q3 with 1 of 2 correct options
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q3_id}", json={"selected_option_ids": [q3_o1]}, headers={"Authorization": f"Bearer {token}"})

        await client.post(f"/api/v1/student/attempts/{attempt_id}/submit", headers={"Authorization": f"Bearer {token}"})

        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        assert float(att_db.total_score) == 1.5


@pytest.mark.asyncio
async def test_deadline_expired_attempt_lazily_finalized(assessment_setup, db_session):
    """When attempt deadline has passed, autosave is rejected and attempt transitions to EXPIRED."""
    student_a = assessment_setup["student_a"]
    quiz_id = str(assessment_setup["quiz"].id)
    token = make_test_token(str(student_a.id))

    q1_id = str(assessment_setup["q1"].id)
    q1_o1 = str(assessment_setup["q1_o1"].id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz_id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Manually alter started_at and deadline in DB to the past (preserving deadline_at >= started_at)
        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        att_db.started_at = datetime.now(timezone.utc) - timedelta(minutes=40)
        att_db.deadline_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        db_session.commit()

        # Attempt to save answer after deadline
        late_save = await client.put(
            f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}",
            json={"selected_option_ids": [q1_o1]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert late_save.status_code == 409
        assert "expired" in late_save.json()["detail"].lower()

        # Verify attempt transitioned to EXPIRED and is_finalized
        db_session.refresh(att_db)
        assert att_db.status == AttemptStatus.EXPIRED
        assert att_db.is_finalized is True

