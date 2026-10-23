"""Integration tests for Phase 7: Teacher Results, Grading Adjustments, Release, and CSV Export."""
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
from app.models.attempt import QuizAttempt, AttemptAnswer, AttemptStatus, GradingStatus, AttemptTelemetryEvent
from app.models.audit import GradeAdjustment, AuditEvent

TEST_JWT_SECRET = "test-teacher-results-secret-hs256-abcdef012345"

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
def db_session() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def seed_data(db_session: Session):
    """Seed teachers, students, quizzes with versions, questions, assignments, and attempts."""
    now = datetime.now(timezone.utc)

    # 1. Teachers
    teacher_a = User(
        id=uuid.uuid4(),
        email="prof.sharma@college.edu",
        name="Prof. Sharma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    teacher_b = User(
        id=uuid.uuid4(),
        email="prof.patil@college.edu",
        name="Prof. Patil",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add_all([teacher_a, teacher_b])

    # 2. Students
    student_1 = User(
        id=uuid.uuid4(),
        email="aarav.patel@student.college.edu",
        name="Aarav Patel",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_2 = User(
        id=uuid.uuid4(),
        email="diya.deshmukh@student.college.edu",
        name="Diya Deshmukh",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_3 = User(
        id=uuid.uuid4(),
        email="formula.inject@student.college.edu",
        name="=SUM(A1:A10)",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([student_1, student_2, student_3])
    db_session.flush()

    prof_1 = StudentProfile(id=uuid.uuid4(), user_id=student_1.id, prn="PRN2026CS101", current_division="A")
    prof_2 = StudentProfile(id=uuid.uuid4(), user_id=student_2.id, prn="PRN2026CS102", current_division="B")
    prof_3 = StudentProfile(id=uuid.uuid4(), user_id=student_3.id, prn="@PRN2026CS999", current_division="-DIV_C")
    db_session.add_all([prof_1, prof_2, prof_3])

    # 3. Quiz owned by Teacher A
    quiz_a = Quiz(
        id=uuid.uuid4(),
        title="Data Structures Midterm",
        course_code="CS301",
        created_by_id=teacher_a.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz_a)
    db_session.flush()

    # QuizVersion for Quiz A
    version_a = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        version_number=1,
        title="Data Structures Midterm v1",
        is_published=True,
        opens_at=now - timedelta(hours=2),
        closes_at=now + timedelta(hours=5),
        duration_minutes=60,
        max_attempts=1,
        tab_switch_limit=2,
        tab_switch_penalty_marks=1.0,
        is_results_released=False,
    )
    db_session.add(version_a)
    db_session.flush()

    # Questions for Version A
    q1 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version_a.id,
        prompt="Time complexity of binary search?",
        question_type=QuestionType.SINGLE_CHOICE,
        positive_marks=5.0,
        negative_marks=1.0,
        order_index=0,
    )
    db_session.add(q1)
    db_session.flush()

    opt1_a = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="O(log n)", is_correct=True, order_index=0)
    opt1_b = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="O(n)", is_correct=False, order_index=1)
    db_session.add_all([opt1_a, opt1_b])

    q2 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version_a.id,
        prompt="Which are linear data structures?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        positive_marks=5.0,
        negative_marks=1.0,
        order_index=1,
    )
    db_session.add(q2)
    db_session.flush()

    opt2_a = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="Array", is_correct=True, order_index=0)
    opt2_b = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="Queue", is_correct=True, order_index=1)
    opt2_c = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="Graph", is_correct=False, order_index=2)
    db_session.add_all([opt2_a, opt2_b, opt2_c])

    # Assignments for Quiz A
    assign_1 = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        student_prn=prof_1.prn,
        student_email=student_1.email,
        student_name=student_1.name,
        division="A",
        assigned_student_id=student_1.id,
        is_active=True,
    )
    assign_2 = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        student_prn=prof_2.prn,
        student_email=student_2.email,
        student_name=student_2.name,
        division="B",
        assigned_student_id=student_2.id,
        is_active=True,
    )
    assign_3 = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz_a.id,
        student_prn=prof_3.prn,
        student_email=student_3.email,
        student_name=student_3.name,
        division="-DIV_C",
        assigned_student_id=student_3.id,
        is_active=True,
    )
    db_session.add_all([assign_1, assign_2, assign_3])

    # Attempts:
    # Attempt 1 (Student 1) - Submitted, Score = 10.0
    att_1 = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=version_a.id,
        student_id=student_1.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now - timedelta(minutes=50),
        deadline_at=now + timedelta(minutes=10),
        submitted_at=now - timedelta(minutes=10),
        total_score=10.0,
        grading_status=GradingStatus.AUTO_GRADED,
        is_finalized=True,
        tab_switch_count=1,
    )
    db_session.add(att_1)
    db_session.flush()

    ans1_1 = AttemptAnswer(
        id=uuid.uuid4(),
        attempt_id=att_1.id,
        question_id=q1.id,
        selected_option_ids=[str(opt1_a.id)],
        awarded_marks=5.0,
        client_timestamp=now - timedelta(minutes=45),
    )
    ans1_2 = AttemptAnswer(
        id=uuid.uuid4(),
        attempt_id=att_1.id,
        question_id=q2.id,
        selected_option_ids=[str(opt2_a.id), str(opt2_b.id)],
        awarded_marks=5.0,
        client_timestamp=now - timedelta(minutes=40),
    )
    db_session.add_all([ans1_1, ans1_2])

    # Telemetry for Attempt 1
    telem_1 = AttemptTelemetryEvent(
        id=uuid.uuid4(),
        attempt_id=att_1.id,
        event_type="window_blur",
        event_timestamp=now - timedelta(minutes=30),
        event_data={"reason": "tab_switch"},
    )
    db_session.add(telem_1)

    # Attempt 2 (Student 2) - Submitted, Score = 4.0
    att_2 = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=version_a.id,
        student_id=student_2.id,
        attempt_number=1,
        status=AttemptStatus.SUBMITTED,
        started_at=now - timedelta(minutes=40),
        deadline_at=now + timedelta(minutes=20),
        submitted_at=now - timedelta(minutes=5),
        total_score=4.0,
        grading_status=GradingStatus.AUTO_GRADED,
        is_finalized=True,
        tab_switch_count=0,
    )
    db_session.add(att_2)

    # Attempt 3 (Student 3) - In Progress
    att_3 = QuizAttempt(
        id=uuid.uuid4(),
        quiz_version_id=version_a.id,
        student_id=student_3.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS,
        started_at=now - timedelta(minutes=15),
        deadline_at=now + timedelta(minutes=45),
        total_score=None,
        grading_status=GradingStatus.PENDING,
        is_finalized=False,
        tab_switch_count=3,
    )
    db_session.add(att_3)

    # 4. Quiz B owned by Teacher B (to test isolation)
    quiz_b = Quiz(
        id=uuid.uuid4(),
        title="Algorithms Final Exam",
        course_code="CS302",
        created_by_id=teacher_b.id,
        status=QuizStatus.PUBLISHED,
    )
    db_session.add(quiz_b)
    db_session.flush()

    version_b = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz_b.id,
        version_number=1,
        title="Algorithms Final v1",
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=3),
        duration_minutes=45,
        max_attempts=1,
    )
    db_session.add(version_b)

    db_session.commit()

    return {
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "student_1": student_1,
        "student_2": student_2,
        "student_3": student_3,
        "quiz_a": quiz_a,
        "quiz_b": quiz_b,
        "version_a": version_a,
        "att_1": att_1,
        "att_2": att_2,
        "att_3": att_3,
    }


@pytest.mark.asyncio
async def test_student_denied_teacher_results_endpoints(seed_data):
    """Students calling teacher result management endpoints must receive HTTP 403 Forbidden."""
    student = seed_data["student_1"]
    quiz_a = seed_data["quiz_a"]
    token = make_test_token(str(student.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Summary
        r1 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 403

        # Attempts
        r2 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 403

        # Export
        r3 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 403

        # Release
        r4 = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/release",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r4.status_code == 403


@pytest.mark.asyncio
async def test_cross_teacher_isolation(seed_data):
    """Teacher B attempting to access Teacher A's quiz results must receive HTTP 404 Not Found."""
    teacher_b = seed_data["teacher_b"]
    quiz_a = seed_data["quiz_a"]
    att_1 = seed_data["att_1"]
    token = make_test_token(str(teacher_b.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Summary
        r1 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 404

        # Attempts
        r2 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 404

        # Detail
        r3 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 404

        # Adjust
        r4 = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 8.0, "reason": "Unauthorized teacher adjustment"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r4.status_code == 404

        # Release
        r5 = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/release",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r5.status_code == 404

        # Export
        r6 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r6.status_code == 404


@pytest.mark.asyncio
async def test_quiz_results_summary_metrics(seed_data):
    """Verify server-side KPI metric calculations for Teacher A."""
    teacher_a = seed_data["teacher_a"]
    quiz_a = seed_data["quiz_a"]
    token = make_test_token(str(teacher_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()

        assert data["quiz_id"] == str(quiz_a.id)
        assert data["course_code"] == "CS301"
        assert data["total_enrolled"] == 3
        assert data["total_attempts"] == 3
        assert data["submitted_count"] == 2
        assert data["in_progress_count"] == 1
        assert data["average_score"] == 7.0  # (10.0 + 4.0) / 2 = 7.0
        assert data["highest_score"] == 10.0
        assert data["lowest_score"] == 4.0
        assert data["total_possible_marks"] == 10.0
        assert data["is_results_released"] is False
        assert data["results_released_at"] is None


@pytest.mark.asyncio
async def test_paginated_attempts_filtering_and_search(seed_data):
    """Verify pagination, status filtering, and search functionality."""
    teacher_a = seed_data["teacher_a"]
    quiz_a = seed_data["quiz_a"]
    token = make_test_token(str(teacher_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Default listing: 3 attempts
        r1 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["total"] == 3
        assert len(data1["items"]) == 3

        # 2. Filter by status: submitted (2 attempts)
        r2 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts?status=submitted",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["total"] == 2
        assert all(item["status"] == "submitted" for item in data2["items"])

        # 3. Filter by status: in_progress (1 attempt)
        r3 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts?status=in_progress",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.status_code == 200
        data3 = r3.json()
        assert data3["total"] == 1
        assert data3["items"][0]["status"] == "in_progress"

        # 4. Search by PRN: PRN2026CS101
        r4 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts?search=PRN2026CS101",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r4.status_code == 200
        data4 = r4.json()
        assert data4["total"] == 1
        assert data4["items"][0]["student_prn"] == "PRN2026CS101"
        assert data4["items"][0]["student_name"] == "Aarav Patel"

        # 5. Pagination: limit=1
        r5 = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts?limit=1&page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r5.status_code == 200
        data5 = r5.json()
        assert data5["total"] == 3
        assert data5["limit"] == 1
        assert data5["page"] == 2
        assert data5["total_pages"] == 3
        assert len(data5["items"]) == 1


@pytest.mark.asyncio
async def test_attempt_detail_diagnostic_view(seed_data):
    """Verify teacher can inspect question responses, answer keys, awarded marks, and telemetry."""
    teacher_a = seed_data["teacher_a"]
    quiz_a = seed_data["quiz_a"]
    att_1 = seed_data["att_1"]
    token = make_test_token(str(teacher_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()

        assert data["attempt_id"] == str(att_1.id)
        assert data["student_name"] == "Aarav Patel"
        assert data["student_prn"] == "PRN2026CS101"
        assert data["total_score"] == 10.0
        assert data["max_possible_marks"] == 10.0
        assert data["tab_switch_count"] == 1

        # Questions check
        assert len(data["questions"]) == 2
        q1_data = data["questions"][0]
        assert q1_data["awarded_marks"] == 5.0
        # Teacher view includes option correctness!
        assert any(opt["is_correct"] is True for opt in q1_data["options"])

        # Telemetry events check
        assert len(data["telemetry_events"]) == 1
        assert data["telemetry_events"][0]["event_type"] == "window_blur"


@pytest.mark.asyncio
async def test_manual_grade_adjustment_lifecycle_and_audit(seed_data):
    """Verify score adjustment validation, score preservation, and immutable audit logging."""
    teacher_a = seed_data["teacher_a"]
    quiz_a = seed_data["quiz_a"]
    att_1 = seed_data["att_1"]
    att_3 = seed_data["att_3"]  # in_progress
    token = make_test_token(str(teacher_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Reject adjustment on in-progress attempt
        r_inprog = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_3.id}/adjust",
            json={"new_score": 5.0, "reason": "Attempt still ongoing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_inprog.status_code == 400
        assert "must be submitted or expired" in r_inprog.json()["detail"]

        # 2. Reject negative score
        r_neg = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": -2.0, "reason": "Mistake penalty"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_neg.status_code == 422

        # 3. Reject score exceeding maximum marks (max marks = 10.0)
        r_over = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 15.0, "reason": "Bonus marks for clean code"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_over.status_code == 400
        assert "cannot exceed maximum possible marks" in r_over.json()["detail"]

        # 4. Reject empty or whitespace-only reason
        r_blank = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 9.0, "reason": "   "},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_blank.status_code == 422

        # 5. Successful adjustment: 10.0 -> 8.5
        r_valid = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 8.5, "reason": "Deduction for suboptimal algorithm approach"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_valid.status_code == 200
        data_valid = r_valid.json()
        assert data_valid["total_score"] == 8.5
        assert data_valid["grading_status"] == "manually_adjusted"
        assert len(data_valid["adjustments"]) == 1
        adj = data_valid["adjustments"][0]
        assert adj["previous_score"] == 10.0
        assert adj["new_score"] == 8.5
        assert "suboptimal algorithm" in adj["reason"]
        assert adj["adjusted_by_name"] == "Prof. Sharma"

        # 6. Second adjustment: 8.5 -> 9.0
        r_second = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 9.0, "reason": "Partial credit restored after review"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_second.status_code == 200
        data_second = r_second.json()
        assert data_second["total_score"] == 9.0
        assert len(data_second["adjustments"]) == 2
        assert data_second["adjustments"][0]["previous_score"] == 8.5
        assert data_second["adjustments"][0]["new_score"] == 9.0
        assert data_second["adjustments"][1]["previous_score"] == 10.0
        assert data_second["adjustments"][1]["new_score"] == 8.5

        # 7. Safe retry with identical score does not create duplicate adjustment
        r_retry = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/attempts/{att_1.id}/adjust",
            json={"new_score": 9.0, "reason": "Duplicate click"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_retry.status_code == 200
        assert len(r_retry.json()["adjustments"]) == 2


@pytest.mark.asyncio
async def test_result_release_workflow_and_student_visibility(seed_data):
    """Verify result withholding before release, idempotent release, and student access after release."""
    teacher_a = seed_data["teacher_a"]
    student_1 = seed_data["student_1"]
    student_2 = seed_data["student_2"]
    quiz_a = seed_data["quiz_a"]
    att_1 = seed_data["att_1"]

    teacher_token = make_test_token(str(teacher_a.id))
    student_1_token = make_test_token(str(student_1.id))
    student_2_token = make_test_token(str(student_2.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Student requests score before release -> HTTP 403 Forbidden
        r_before = await client.get(
            f"/api/v1/student/attempts/{att_1.id}/result",
            headers={"Authorization": f"Bearer {student_1_token}"},
        )
        assert r_before.status_code == 403
        assert "not been released" in r_before.json()["detail"]

        # 2. Teacher releases results
        r_rel = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/release",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert r_rel.status_code == 200
        data_rel = r_rel.json()
        assert data_rel["is_results_released"] is True
        assert data_rel["results_released_at"] is not None

        # 3. Repeated release is idempotent
        r_rel_retry = await client.post(
            f"/api/v1/quizzes/{quiz_a.id}/results/release",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert r_rel_retry.status_code == 200
        assert r_rel_retry.json()["is_results_released"] is True

        # 4. Student 1 requests score after release -> HTTP 200 OK
        r_after = await client.get(
            f"/api/v1/student/attempts/{att_1.id}/result",
            headers={"Authorization": f"Bearer {student_1_token}"},
        )
        assert r_after.status_code == 200
        data_after = r_after.json()
        assert data_after["attempt_id"] == str(att_1.id)
        assert data_after["total_score"] == 10.0
        assert data_after["max_possible_score"] == 10.0
        assert data_after["is_results_released"] is True
        assert data_after["status"] == "submitted"

        # 5. Cross-student isolation: Student 2 cannot query Student 1's result
        r_cross = await client.get(
            f"/api/v1/student/attempts/{att_1.id}/result",
            headers={"Authorization": f"Bearer {student_2_token}"},
        )
        assert r_cross.status_code == 404


@pytest.mark.asyncio
async def test_csv_export_mitigates_formula_injection_and_escapes(seed_data):
    """Verify CSV export formatting, 12-column header, and spreadsheet formula injection sanitization."""
    teacher_a = seed_data["teacher_a"]
    quiz_a = seed_data["quiz_a"]
    token = make_test_token(str(teacher_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{quiz_a.id}/results/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/csv")
        assert f"quiz_{quiz_a.id}_results.csv" in res.headers["content-disposition"]

        csv_text = res.text
        lines = [line.strip() for line in csv_text.strip().split("\n") if line.strip()]
        assert len(lines) >= 4  # Header + 3 attempts

        # Header check
        header_cols = lines[0].split(",")
        assert header_cols == [
            "PRN",
            "Student Name",
            "Student Email",
            "Division",
            "Attempt Number",
            "Status",
            "Started At (UTC)",
            "Submitted At (UTC)",
            "Score",
            "Max Marks",
            "Grading Status",
            "Tab Switches",
        ]

        # Check Student 3 formula injection defense:
        # student_3 has name="=SUM(A1:A10)", PRN="@PRN2026CS999", division="-DIV_C"
        # Each must be prefixed with a single quote "'"
        student_3_line = [l for l in lines if "formula.inject" in l][0]
        assert "'=SUM(A1:A10)" in student_3_line
        assert "'@PRN2026CS999" in student_3_line
        assert "'-DIV_C" in student_3_line


@pytest.mark.asyncio
async def test_empty_quiz_csv_export_returns_headers_cleanly(seed_data):
    """Verify an empty quiz with 0 attempts produces valid CSV headers without crashing."""
    teacher_b = seed_data["teacher_b"]
    quiz_b = seed_data["quiz_b"]
    token = make_test_token(str(teacher_b.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/quizzes/{quiz_b.id}/results/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        csv_text = res.text.strip()
        lines = csv_text.split("\n")
        assert len(lines) == 1
        assert "PRN,Student Name,Student Email" in lines[0]
