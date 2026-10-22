"""Focused API tests for GET /api/v1/users/me endpoint (TASK-302, DEC-001, DEC-013)."""
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
from app.models.user import User, UserRole
from app.core.config import settings
from app.core.database import get_db

TEST_JWT_SECRET = "test-secret-key-for-profile-endpoint-testing-hs256-12345"

# SQLite in-memory test database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_test_token(
    sub: str,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    expires_in_seconds: int = 3600,
    aud: str = "authenticated",
    issuer: str = None,
    extra_claims: dict = None,
) -> str:
    """Generate a test JWT with controlled claims."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": aud,
        "exp": now + expires_in_seconds,
        "iat": now,
    }
    if issuer:
        payload["iss"] = issuer
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, algorithm=algorithm)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Configure test environment and in-memory database."""
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
    """Yield a database session for test seeding."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def student_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="student.test@college.edu",
        name="Ananya Sharma",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def teacher_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="teacher.test@college.edu",
        name="Prof. Rajesh Verma",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="admin.test@college.edu",
        name="Dean Academic",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def deactivated_user(db_session: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        email="inactive.user@college.edu",
        name="Deactivated Account",
        role=UserRole.STUDENT,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_profile_authenticated_student_success(student_user: User):
    """Authenticated student should receive 200 OK with matching profile data."""
    token = make_test_token(sub=str(student_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_user.id)
    assert data["email"] == student_user.email
    assert data["name"] == student_user.name
    assert data["role"] == "student"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_profile_authenticated_teacher_and_admin(
    teacher_user: User, admin_user: User
):
    """Teacher and Admin should receive their respective authoritative roles."""
    teacher_token = make_test_token(sub=str(teacher_user.id))
    admin_token = make_test_token(sub=str(admin_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        t_res = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {teacher_token}"}
        )
        a_res = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"}
        )

    assert t_res.status_code == 200
    assert t_res.json()["role"] == "teacher"
    assert t_res.json()["name"] == teacher_user.name

    assert a_res.status_code == 200
    assert a_res.json()["role"] == "admin"
    assert a_res.json()["name"] == admin_user.name


@pytest.mark.asyncio
async def test_profile_response_field_allowlist_strictness(student_user: User):
    """
    Ensure the profile endpoint response contains strictly allowed fields.
    Passwords, tokens, internal timestamps, and ORM metadata must never be exposed.
    """
    token = make_test_token(sub=str(student_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Exact expected fields only
    expected_fields = {"id", "email", "name", "role", "is_active"}
    assert set(data.keys()) == expected_fields

    # Explicit check for forbidden/sensitive fields
    forbidden_fields = {
        "password",
        "hashed_password",
        "token",
        "access_token",
        "created_at",
        "updated_at",
        "_sa_instance_state",
    }
    for field in forbidden_fields:
        assert field not in data, f"Sensitive field '{field}' leaked in profile response"


@pytest.mark.asyncio
async def test_profile_rejects_missing_credentials():
    """Request without Authorization header must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_profile_rejects_invalid_scheme():
    """Request with non-Bearer scheme must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )

    assert response.status_code == 401
    assert "Bearer" in response.headers.get("WWW-Authenticate", "")


@pytest.mark.asyncio
async def test_profile_rejects_empty_token():
    """Bearer token with empty value must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer   "}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_rejects_malformed_token():
    """Malformed token string must return 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not-a-valid-jwt-token"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_rejects_invalid_signature(student_user: User):
    """Token signed with wrong key must return 401."""
    tampered_token = make_test_token(
        sub=str(student_user.id),
        secret="completely-different-wrong-secret-key-12345",
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {tampered_token}"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_rejects_expired_token(student_user: User):
    """Expired token must return 401."""
    expired_token = make_test_token(
        sub=str(student_user.id),
        expires_in_seconds=-60,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_profile_rejects_unregistered_user():
    """Valid JWT for subject not registered in database must return 401."""
    unregistered_uuid = str(uuid.uuid4())
    token = make_test_token(sub=unregistered_uuid)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401
    assert "not registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_profile_rejects_deactivated_user(deactivated_user: User):
    """Registered but deactivated user account must return 401."""
    token = make_test_token(sub=str(deactivated_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401
    assert "deactivated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_profile_ignores_client_role_tampering(student_user: User):
    """
    Ensure the endpoint NEVER accepts role overrides from query parameters
    or arbitrary client headers; role must always match the database record.
    """
    token = make_test_token(sub=str(student_user.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-Role": "admin",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Pass attempted role spoof via query parameter
        response = await client.get(
            "/api/v1/users/me?role=admin&is_admin=true",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    # The role must still be the student's authoritative role from DB
    assert data["role"] == "student"
    assert data["role"] != "admin"


@pytest.mark.asyncio
async def test_health_check_endpoint_unaffected():
    """Verify that root /health endpoint remains functional and unchanged."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
