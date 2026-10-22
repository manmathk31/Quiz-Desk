"""Comprehensive API test suite for Teacher Question Bank & CSV Import (Milestone 4A)."""
import time
import uuid
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.question import Question, QuestionOption, QuestionType
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-question-bank-secret-key-hs256-12345678"

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
def teacher_a(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="teacher.a@college.edu",
        name="Prof. Amit Sharma",
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
        name="Dr. Sneha Patel",
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
        email="student.test@college.edu",
        name="Rahul Verma",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_teacher_can_create_and_retrieve_manual_question(teacher_a: User):
    """Teacher can manually create a single-choice question with options."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "question_type": "single_choice",
        "prompt": "What is the capital of India?",
        "positive_marks": 2.0,
        "negative_marks": 0.5,
        "options": [
            {"option_text": "Mumbai", "is_correct": False, "order_index": 0},
            {"option_text": "New Delhi", "is_correct": True, "order_index": 1},
            {"option_text": "Kolkata", "is_correct": False, "order_index": 2},
            {"option_text": "Chennai", "is_correct": False, "order_index": 3},
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_res = await client.post("/api/v1/question-bank", json=payload, headers=headers)
        assert create_res.status_code == 201
        created_data = create_res.json()
        question_id = created_data["id"]
        assert created_data["prompt"] == "What is the capital of India?"
        assert created_data["positive_marks"] == 2.0
        assert len(created_data["options"]) == 4

        # Retrieve single question by ID
        get_res = await client.get(f"/api/v1/question-bank/{question_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == question_id


@pytest.mark.asyncio
async def test_question_creation_validation_errors(teacher_a: User):
    """Validation errors on bad options or marks."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Single choice with 2 correct options
        bad_single = {
            "question_type": "single_choice",
            "prompt": "Invalid single choice",
            "positive_marks": 1.0,
            "negative_marks": 0.0,
            "options": [
                {"option_text": "A", "is_correct": True},
                {"option_text": "B", "is_correct": True},
            ],
        }
        res1 = await client.post("/api/v1/question-bank", json=bad_single, headers=headers)
        assert res1.status_code == 422

        # True/False with 3 options
        bad_tf = {
            "question_type": "true_false",
            "prompt": "Invalid TF",
            "positive_marks": 1.0,
            "negative_marks": 0.0,
            "options": [
                {"option_text": "True", "is_correct": True},
                {"option_text": "False", "is_correct": False},
                {"option_text": "Maybe", "is_correct": False},
            ],
        }
        res2 = await client.post("/api/v1/question-bank", json=bad_tf, headers=headers)
        assert res2.status_code == 422


@pytest.mark.asyncio
async def test_cross_teacher_isolation(teacher_a: User, teacher_b: User):
    """Teacher B cannot view, update, or delete Teacher A's questions."""
    token_a = make_test_token(str(teacher_a.id))
    token_b = make_test_token(str(teacher_b.id))

    payload = {
        "question_type": "single_choice",
        "prompt": "Teacher A's Private Question",
        "positive_marks": 1.0,
        "negative_marks": 0.0,
        "options": [
            {"option_text": "Opt 1", "is_correct": True},
            {"option_text": "Opt 2", "is_correct": False},
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Teacher A creates question
        res_create = await client.post(
            "/api/v1/question-bank", json=payload, headers={"Authorization": f"Bearer {token_a}"}
        )
        q_id = res_create.json()["id"]

        # Teacher B tries to GET Teacher A's question
        res_get_b = await client.get(
            f"/api/v1/question-bank/{q_id}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_get_b.status_code == 404

        # Teacher B tries to PUT
        res_put_b = await client.put(
            f"/api/v1/question-bank/{q_id}",
            json={
                "question_type": "single_choice",
                "prompt": "Hacked Prompt",
                "positive_marks": 1.0,
                "negative_marks": 0.0,
                "options": [
                    {"option_text": "Hacked 1", "is_correct": True},
                    {"option_text": "Hacked 2", "is_correct": False},
                ],
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_put_b.status_code == 404

        # Teacher B tries to DELETE
        res_del_b = await client.delete(
            f"/api/v1/question-bank/{q_id}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_del_b.status_code == 404


@pytest.mark.asyncio
async def test_update_and_delete_question(teacher_a: User):
    """Teacher can update and delete their own questions."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        res = await client.post(
            "/api/v1/question-bank",
            json={
                "question_type": "single_choice",
                "prompt": "Original Prompt",
                "positive_marks": 1.0,
                "negative_marks": 0.0,
                "options": [
                    {"option_text": "Opt 1", "is_correct": True},
                    {"option_text": "Opt 2", "is_correct": False},
                ],
            },
            headers=headers,
        )
        q_id = res.json()["id"]

        # Update
        update_res = await client.put(
            f"/api/v1/question-bank/{q_id}",
            json={
                "question_type": "single_choice",
                "prompt": "Updated Prompt",
                "positive_marks": 5.0,
                "negative_marks": 1.0,
                "options": [
                    {"option_text": "New Opt 1", "is_correct": False},
                    {"option_text": "New Opt 2", "is_correct": True},
                ],
            },
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["prompt"] == "Updated Prompt"
        assert update_res.json()["positive_marks"] == 5.0

        # Delete
        del_res = await client.delete(f"/api/v1/question-bank/{q_id}", headers=headers)
        assert del_res.status_code == 204

        # Subsequent GET should return 404
        get_res = await client.get(f"/api/v1/question-bank/{q_id}", headers=headers)
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_pagination_and_search(teacher_a: User):
    """Verify paginated listing and prompt substring search."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i in range(5):
            prompt = f"Algorithm Question {i}" if i % 2 == 0 else f"Database Question {i}"
            await client.post(
                "/api/v1/question-bank",
                json={
                    "question_type": "single_choice",
                    "prompt": prompt,
                    "positive_marks": 1.0,
                    "negative_marks": 0.0,
                    "options": [
                        {"option_text": "A", "is_correct": True},
                        {"option_text": "B", "is_correct": False},
                    ],
                },
                headers=headers,
            )

        # List all page 1 with page_size 2
        res_page1 = await client.get("/api/v1/question-bank?page=1&page_size=2", headers=headers)
        assert res_page1.status_code == 200
        data1 = res_page1.json()
        assert data1["total"] == 5
        assert len(data1["items"]) == 2
        assert data1["total_pages"] == 3

        # Search for "Algorithm"
        res_search = await client.get("/api/v1/question-bank?search=Algorithm", headers=headers)
        assert res_search.status_code == 200
        assert res_search.json()["total"] == 3


@pytest.mark.asyncio
async def test_student_role_denial(student_user: User):
    """Students receive 403 Forbidden on all teacher question-bank endpoints."""
    token = make_test_token(str(student_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/question-bank", headers=headers)).status_code == 403
        assert (
            await client.post(
                "/api/v1/question-bank",
                json={
                    "question_type": "single_choice",
                    "prompt": "Test",
                    "positive_marks": 1.0,
                    "negative_marks": 0.0,
                    "options": [
                        {"option_text": "A", "is_correct": True},
                        {"option_text": "B", "is_correct": False},
                    ],
                },
                headers=headers,
            )
        ).status_code == 403
        assert (
            await client.get(
                f"/api/v1/question-bank/{uuid.uuid4()}", headers=headers
            )
        ).status_code == 403


@pytest.mark.asyncio
async def test_csv_template_download(teacher_a: User):
    """Template download returns CSV format."""
    token = make_test_token(str(teacher_a.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/question-bank/csv/template",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "question_type" in res.text


@pytest.mark.asyncio
async def test_csv_preview_endpoint(teacher_a: User, db_session: Session):
    """CSV preview parses without persisting records."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    csv_data = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Binary search complexity?",O(1),O(n),O(log n),O(n^2),C,2.0,0.5\n'
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/question-bank/csv/preview",
            files={"file": ("questions.csv", csv_data.encode("utf-8"), "text/csv")},
            headers=headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["valid_count"] == 1
    assert data["error_count"] == 0

    # Ensure zero questions persisted during preview
    count = db_session.scalar(select(func.count()).select_from(Question))
    assert count == 0


@pytest.mark.asyncio
async def test_csv_import_all_or_nothing_transaction(teacher_a: User, db_session: Session):
    """Valid CSV commits transactionally; malformed CSV rolls back completely."""
    token = make_test_token(str(teacher_a.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Malformed CSV with an invalid row: must reject with 422 and persist 0 questions
    bad_csv = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Valid Question",A,B,,,A,1.0,0.0\n'
        'single_choice,"Bad Question",A,B,,,D,1.0,0.0\n'  # D is empty
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        bad_res = await client.post(
            "/api/v1/question-bank/csv/import",
            files={"file": ("bad.csv", bad_csv.encode("utf-8"), "text/csv")},
            headers=headers,
        )
        assert bad_res.status_code == 422

        count = db_session.scalar(select(func.count()).select_from(Question))
        assert count == 0

        # 2. Valid CSV: imports successfully
        good_csv = (
            "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
            'single_choice,"Question 1",A,B,,,A,1.0,0.0\n'
            'true_false,"Question 2",True,False,,,B,2.0,0.0\n'
        )

        good_res = await client.post(
            "/api/v1/question-bank/csv/import",
            files={"file": ("good.csv", good_csv.encode("utf-8"), "text/csv")},
            headers=headers,
        )
        assert good_res.status_code == 201
        assert good_res.json()["imported_count"] == 2

        count_after = db_session.scalar(select(func.count()).select_from(Question))
        assert count_after == 2
