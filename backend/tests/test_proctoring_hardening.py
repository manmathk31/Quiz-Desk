"""Comprehensive automated test suite for Phase 8A: Assessment Proctoring Hardening, Configurable Penalties, and Telemetry Idempotency."""
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
from app.models.attempt import QuizAttempt, AttemptStatus, GradingStatus, AttemptTelemetryEvent
from app.schemas.quiz import QuizCreateRequest

TEST_JWT_SECRET = "test-proctoring-secret-key-hs256-abcdef012345"

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
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def proctoring_setup(db_session: Session):
    """Seed teacher, students, quiz, questions, and roster assignments."""
    now = datetime.now(timezone.utc)

    # 1. Teacher
    teacher = User(
        id=uuid.uuid4(),
        email="instructor@college.edu",
        name="Prof. Integrity",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)

    # 2. Student A and Student B
    student_a = User(
        id=uuid.uuid4(),
        email="alice@college.edu",
        name="Alice Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_b = User(
        id=uuid.uuid4(),
        email="bob@college.edu",
        name="Bob Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([student_a, student_b])
    db_session.flush()

    prof_a = StudentProfile(
        id=uuid.uuid4(),
        user_id=student_a.id,
        prn="PRN-ALICE-001",
        current_division="A",
    )
    prof_b = StudentProfile(
        id=uuid.uuid4(),
        user_id=student_b.id,
        prn="PRN-BOB-002",
        current_division="A",
    )
    db_session.add_all([prof_a, prof_b])

    # 3. Quiz with Configurable Proctoring Policy
    quiz = Quiz(
        id=uuid.uuid4(),
        title="Network Security Examination",
        course_code="CS-401",
        created_by_id=teacher.id,
        status=QuizStatus.PUBLISHED,
        is_archived=False,
    )
    db_session.add(quiz)
    db_session.flush()

    version = QuizVersion(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        version_number=1,
        title="Network Security Examination - V1",
        is_published=True,
        opens_at=now - timedelta(hours=1),
        closes_at=now + timedelta(hours=4),
        duration_minutes=60,
        max_attempts=1,
        allow_backtracking=True,
        shuffle_questions=False,
        shuffle_options=False,
        multi_answer_policy=MultiAnswerPolicy.ALL_OR_NOTHING,
        # Proctoring configuration: Free=2, Deduction=1.0, Cap=3.0
        tab_switch_limit=2,
        tab_switch_penalty_marks=1.00,
        max_proctoring_deduction=3.00,
        enable_copy_paste_restriction=True,
        count_copy_paste_violations=True,
        require_fullscreen=True,
        count_fullscreen_exit_violations=True,
        count_tab_switch_violations=True,
        count_dev_tools_violations=True,
        enable_proctoring_warnings=True,
    )
    db_session.add(version)
    quiz.current_version_id = version.id
    db_session.flush()

    # Questions (Total possible = 5.0 marks)
    q1 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        created_by_id=teacher.id,
        question_type=QuestionType.SINGLE_CHOICE,
        prompt="What is the default port for HTTPS?",
        positive_marks=3.00,
        negative_marks=0.00,
        order_index=0,
    )
    db_session.add(q1)
    db_session.flush()

    o1 = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="443", is_correct=True, order_index=0)
    o2 = QuestionOption(id=uuid.uuid4(), question_id=q1.id, option_text="80", is_correct=False, order_index=1)
    db_session.add_all([o1, o2])

    q2 = Question(
        id=uuid.uuid4(),
        quiz_version_id=version.id,
        created_by_id=teacher.id,
        question_type=QuestionType.TRUE_FALSE,
        prompt="TLS operates above the transport layer.",
        positive_marks=2.00,
        negative_marks=0.00,
        order_index=1,
    )
    db_session.add(q2)
    db_session.flush()

    o3 = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="True", is_correct=True, order_index=0)
    o4 = QuestionOption(id=uuid.uuid4(), question_id=q2.id, option_text="False", is_correct=False, order_index=1)
    db_session.add_all([o3, o4])

    # 4. Assignments
    assign_a = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        assigned_student_id=student_a.id,
        student_prn=prof_a.prn,
        student_email=student_a.email,
        student_name=student_a.name,
        division="A",
        is_active=True,
    )
    assign_b = QuizAssignment(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        assigned_student_id=student_b.id,
        student_prn=prof_b.prn,
        student_email=student_b.email,
        student_name=student_b.name,
        division="A",
        is_active=True,
    )
    db_session.add_all([assign_a, assign_b])
    db_session.commit()

    return {
        "teacher": teacher,
        "student_a": student_a,
        "student_b": student_b,
        "quiz": quiz,
        "version": version,
        "q1": q1,
        "q1_correct": o1,
        "q2": q2,
        "q2_correct": o3,
    }


def test_proctoring_schema_validation_and_bounds():
    """Verify backend Pydantic validation rejects negative or out-of-bound proctoring policies."""
    now = datetime.now(timezone.utc)
    closes = now + timedelta(hours=2)

    # Valid settings with zero free violations, half-mark deduction, and custom cap
    req = QuizCreateRequest(
        title="Proctored Quiz",
        course_code="CS-101",
        opens_at=now,
        closes_at=closes,
        duration_minutes=30,
        max_attempts=1,
        tab_switch_limit=0,  # Penalties start immediately
        tab_switch_penalty_marks=0.5,  # Supports half-marks
        max_proctoring_deduction=10.0,
        enable_copy_paste_restriction=True,
        count_copy_paste_violations=True,
        require_fullscreen=True,
        count_fullscreen_exit_violations=True,
        count_tab_switch_violations=True,
        count_dev_tools_violations=True,
        enable_proctoring_warnings=True,
    )
    assert req.tab_switch_limit == 0
    assert req.tab_switch_penalty_marks == 0.5
    assert req.max_proctoring_deduction == 10.0

    # Negative free violation allowance rejected
    with pytest.raises(Exception):
        QuizCreateRequest(
            title="Invalid",
            course_code="CS-101",
            opens_at=now,
            closes_at=closes,
            duration_minutes=30,
            tab_switch_limit=-1,
        )

    # Negative penalty deduction rejected
    with pytest.raises(Exception):
        QuizCreateRequest(
            title="Invalid",
            course_code="CS-101",
            opens_at=now,
            closes_at=closes,
            duration_minutes=30,
            tab_switch_penalty_marks=-0.5,
        )


@pytest.mark.asyncio
async def test_configurable_penalty_boundaries_and_cap(proctoring_setup, db_session: Session):
    """
    Test penalty formula:
    Free = 2, Deduction = 1.0, Cap = 3.0, Raw Score = 5.0 (answering both questions correctly).
    - 0 violations -> 0 deduction, final 5.0
    - 1 violation  -> 0 deduction, final 5.0
    - 2 violations -> 0 deduction, final 5.0 (at boundary)
    - 3 violations -> 1.0 deduction, final 4.0 (first chargeable)
    - 4 violations -> 2.0 deduction, final 3.0
    - 5 violations -> 3.0 deduction, final 2.0 (cap reached)
    - 6 violations -> 3.0 deduction, final 2.0 (remains capped at 3.0)
    """
    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Start attempt
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Answer both correctly for 5.0 raw marks
        q1_id = str(proctoring_setup["q1"].id)
        q1_ans = str(proctoring_setup["q1_correct"].id)
        q2_id = str(proctoring_setup["q2"].id)
        q2_ans = str(proctoring_setup["q2_correct"].id)

        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}", json={"selected_option_ids": [q1_ans]}, headers={"Authorization": f"Bearer {token}"})
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q2_id}", json={"selected_option_ids": [q2_ans]}, headers={"Authorization": f"Bearer {token}"})

        # Send 6 fullscreen exit violations
        for i in range(1, 7):
            res = await client.post(
                f"/api/v1/student/attempts/{attempt_id}/telemetry",
                json={"event_type": "fullscreen_exit", "client_event_id": f"fs-{i}"},
                headers={"Authorization": f"Bearer {token}"},
            )
            data = res.json()
            assert data["violation_count"] == i
            if i <= 2:
                assert data["remaining_free_violations"] == (2 - i)
                assert data["chargeable_violations"] == 0
                assert data["current_deduction"] == 0.0
                assert data["limit_exceeded"] is False
            elif i == 3:
                assert data["chargeable_violations"] == 1
                assert data["current_deduction"] == 1.0
                assert data["limit_exceeded"] is True
            elif i == 4:
                assert data["chargeable_violations"] == 2
                assert data["current_deduction"] == 2.0
            elif i >= 5:
                # Capped at 3.0
                assert data["current_deduction"] == 3.0

        # Submit attempt
        sub_res = await client.post(f"/api/v1/student/attempts/{attempt_id}/submit", headers={"Authorization": f"Bearer {token}"})
        assert sub_res.status_code == 200

        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        # Raw = 5.0, deduction = min(4 * 1.0, 3.0, 5.0) = 3.0, Final = 2.0
        assert float(att_db.proctoring_deduction) == 3.0
        assert float(att_db.total_score) == 2.0
        assert att_db.violation_count == 6


@pytest.mark.asyncio
async def test_half_mark_deduction_and_zero_floor(proctoring_setup, db_session: Session):
    """Verify half-mark rate (0.5) works without floating point distortion and score is bounded below by 0.0."""
    version = proctoring_setup["version"]
    version.tab_switch_limit = 1
    version.tab_switch_penalty_marks = 0.50
    version.max_proctoring_deduction = 5.00
    db_session.commit()

    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Only answer q2 for 2.0 marks
        q2_id = str(proctoring_setup["q2"].id)
        q2_ans = str(proctoring_setup["q2_correct"].id)
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q2_id}", json={"selected_option_ids": [q2_ans]}, headers={"Authorization": f"Bearer {token}"})

        # Free = 1. Send 6 violations -> 5 chargeable * 0.5 = 2.5 deduction.
        for i in range(6):
            await client.post(
                f"/api/v1/student/attempts/{attempt_id}/telemetry",
                json={"event_type": "copy_paste_attempt", "client_event_id": f"cp-{i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        await client.post(f"/api/v1/student/attempts/{attempt_id}/submit", headers={"Authorization": f"Bearer {token}"})

        att_db = db_session.get(QuizAttempt, uuid.UUID(attempt_id))
        # Raw = 2.0. Calculated deduction = 5 * 0.5 = 2.5.
        # But proctoring_deduction cannot exceed raw score max(0, S) = 2.0!
        assert float(att_db.proctoring_deduction) == 2.0
        assert float(att_db.total_score) == 0.0


@pytest.mark.asyncio
async def test_telemetry_idempotency_via_client_event_id(proctoring_setup, db_session: Session):
    """Network retries with identical client_event_id must not duplicate events or double-count violations."""
    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        same_event_id = "retry-uuid-12345"
        payload = {"event_type": "dev_tools_shortcut", "client_event_id": same_event_id}

        res1 = await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res1.status_code == 200
        assert res1.json()["violation_count"] == 1

        # Resend exact same client_event_id (simulating client retry)
        res2 = await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 200
        assert res2.json()["violation_count"] == 1  # Not incremented!

        # Check DB rows
        events = db_session.scalars(
            select(AttemptTelemetryEvent).where(
                AttemptTelemetryEvent.attempt_id == uuid.UUID(attempt_id),
                AttemptTelemetryEvent.client_event_id == same_event_id,
            )
        ).all()
        assert len(events) == 1


@pytest.mark.asyncio
async def test_paired_window_blur_and_tab_switch_deduplication(proctoring_setup, db_session: Session):
    """
    Alt-Tab fires window_blur followed immediately by visibilitychange (tab_switch).
    These paired events within 1000ms must be coalesced into a single violation incident.
    """
    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # 1. Fire window_blur
        r1 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "window_blur"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.json()["violation_count"] == 1
        assert r1.json()["tab_switch_count"] == 1

        # 2. Fire tab_switch immediately (< 1000ms)
        r2 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "tab_switch"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should be deduplicated as part of the same physical Alt-Tab action
        assert r2.json()["violation_count"] == 1
        assert r2.json()["tab_switch_count"] == 1

        # Both events are still logged in audit telemetry for full contextual history
        events = db_session.scalars(
            select(AttemptTelemetryEvent).where(AttemptTelemetryEvent.attempt_id == uuid.UUID(attempt_id))
        ).all()
        assert len(events) == 2


@pytest.mark.asyncio
async def test_policy_toggles_filter_uncounted_event_categories(proctoring_setup, db_session: Session):
    """Events disabled in teacher policy must be logged in telemetry audit, but NOT contribute to violations."""
    version = proctoring_setup["version"]
    version.count_dev_tools_violations = False
    version.count_copy_paste_violations = False
    db_session.commit()

    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        # Report dev_tools_shortcut (policy disabled for counting)
        r1 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "dev_tools_shortcut"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.json()["violation_count"] == 0

        # Report copy_paste_attempt (policy disabled for counting)
        r2 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "copy_paste_attempt"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.json()["violation_count"] == 0

        # Report fullscreen_exit (policy enabled for counting)
        r3 = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "fullscreen_exit"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r3.json()["violation_count"] == 1


@pytest.mark.asyncio
async def test_invalid_event_types_rejected(proctoring_setup):
    """Unsupported or forged event types like 'os_screenshot_detected' must be rejected with 400 Bad Request."""
    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        res = await client.post(
            f"/api/v1/student/attempts/{attempt_id}/telemetry",
            json={"event_type": "os_screenshot_detected"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "Unsupported telemetry event type" in res.json()["detail"]


@pytest.mark.asyncio
async def test_cross_student_telemetry_isolation(proctoring_setup):
    """Student B cannot post telemetry to Student A's attempt session."""
    student_a = proctoring_setup["student_a"]
    student_b = proctoring_setup["student_b"]
    quiz = proctoring_setup["quiz"]

    token_a = make_test_token(str(student_a.id))
    token_b = make_test_token(str(student_b.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # A starts attempt
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        attempt_a_id = start_res.json()["attempt_id"]

        # B tries to report telemetry for A
        res = await client.post(
            f"/api/v1/student/attempts/{attempt_a_id}/telemetry",
            json={"event_type": "tab_switch"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_pre_quiz_readiness_screen(proctoring_setup):
    """Readiness endpoint returns complete proctoring policy and rules before student starts or consumes attempt."""
    student_a = proctoring_setup["student_a"]
    quiz = proctoring_setup["quiz"]
    token = make_test_token(str(student_a.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/student/quizzes/{quiz.id}/readiness",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["quiz_id"] == str(quiz.id)
        assert data["require_fullscreen"] is True
        assert data["enable_copy_paste_restriction"] is True
        assert data["free_violation_allowance"] == 2
        assert data["violation_penalty_marks"] == 1.00
        assert data["max_proctoring_deduction"] == 3.00
        assert data["can_start"] is True
        assert data["has_active_attempt"] is False
        assert data["attempts_taken"] == 0


@pytest.mark.asyncio
async def test_teacher_results_diagnostics_and_policy_breakdown(proctoring_setup):
    """Teacher attempt detail view includes violation breakdown, proctoring deduction, and effective policy."""
    student_a = proctoring_setup["student_a"]
    teacher = proctoring_setup["teacher"]
    quiz = proctoring_setup["quiz"]

    student_token = make_test_token(str(student_a.id))
    teacher_token = make_test_token(str(teacher.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Student creates attempt and generates 3 violations
        start_res = await client.post(
            f"/api/v1/student/quizzes/{quiz.id}/attempts",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        attempt_id = start_res.json()["attempt_id"]

        q1_id = str(proctoring_setup["q1"].id)
        q1_ans = str(proctoring_setup["q1_correct"].id)
        await client.put(f"/api/v1/student/attempts/{attempt_id}/answers/{q1_id}", json={"selected_option_ids": [q1_ans]}, headers={"Authorization": f"Bearer {student_token}"})

        await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={"event_type": "fullscreen_exit", "client_event_id": "fe1"}, headers={"Authorization": f"Bearer {student_token}"})
        await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={"event_type": "copy_paste_attempt", "client_event_id": "cp1"}, headers={"Authorization": f"Bearer {student_token}"})
        await client.post(f"/api/v1/student/attempts/{attempt_id}/telemetry", json={"event_type": "dev_tools_shortcut", "client_event_id": "dt1"}, headers={"Authorization": f"Bearer {student_token}"})
        await client.post(f"/api/v1/student/attempts/{attempt_id}/submit", headers={"Authorization": f"Bearer {student_token}"})

        # Teacher inspects attempt detail
        res = await client.get(
            f"/api/v1/quizzes/{quiz.id}/results/attempts/{attempt_id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert res.status_code == 200
        detail = res.json()
        assert detail["violation_count"] == 3
        # Free = 2, Chargeable = 1 * 1.0 = 1.0 deduction
        assert detail["proctoring_deduction"] == 1.0
        assert detail["effective_policy"]["free_violation_allowance"] == 2
        assert detail["effective_policy"]["max_proctoring_deduction"] == 3.0
        assert detail["violation_breakdown"] == {
            "fullscreen_exit": 1,
            "copy_paste_attempt": 1,
            "dev_tools_shortcut": 1,
        }
        assert len(detail["telemetry_events"]) == 3
