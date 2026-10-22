"""Comprehensive unit test suite for Supabase JWT authentication and role-based authorization."""
import time
import uuid
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole
from app.core.config import settings
from app.core.database import get_db
from app.core.auth import (
    decode_supabase_jwt,
    get_current_user,
    get_current_active_user,
    require_student,
    require_teacher,
    require_admin,
    require_faculty,
)

# Controlled test signing secret (never used in production)
TEST_JWT_SECRET = "test-supabase-jwt-secret-for-offline-testing-only-12345678"

# Test SQLite in-memory database setup
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Helper router with test endpoints protected by our dependencies
auth_test_router = APIRouter(prefix="/auth-test", tags=["AuthTest"])


@auth_test_router.get("/me")
async def handle_me_endpoint(current_user: User = Depends(get_current_user)):
    return {"id": str(current_user.id), "email": current_user.email, "role": current_user.role.value}


@auth_test_router.get("/student-only")
async def handle_student_endpoint(current_user: User = Depends(require_student)):
    return {"status": "success", "role": current_user.role.value}


@auth_test_router.get("/teacher-only")
async def handle_teacher_endpoint(current_user: User = Depends(require_teacher)):
    return {"status": "success", "role": current_user.role.value}


@auth_test_router.get("/admin-only")
async def handle_admin_endpoint(current_user: User = Depends(require_admin)):
    return {"status": "success", "role": current_user.role.value}


@auth_test_router.get("/faculty-only")
async def handle_faculty_endpoint(current_user: User = Depends(require_faculty)):
    return {"status": "success", "role": current_user.role.value}


# Include test router on app
app.include_router(auth_test_router)


def create_token(
    sub: str,
    secret: str = TEST_JWT_SECRET,
    algorithm: str = "HS256",
    expires_in_seconds: int = 3600,
    aud: str = "authenticated",
    issuer: str = None,
    extra_claims: dict = None,
) -> str:
    """Helper to generate JWT tokens with controlled test signatures and claims."""
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
def setup_test_environment(monkeypatch):
    """Set test JWT secret and configure in-memory database."""
    # Set controlled test secret in settings
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr(settings, "SUPABASE_JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated")

    # Create tables in memory
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
    """Provide a direct database session for populating test fixtures."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_student(db_session: Session) -> User:
    student = User(
        id=uuid.uuid4(),
        email="student@college.edu",
        name="Alice Student",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


@pytest.fixture
def sample_teacher(db_session: Session) -> User:
    teacher = User(
        id=uuid.uuid4(),
        email="teacher@college.edu",
        name="Prof. Bob",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def sample_admin(db_session: Session) -> User:
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@college.edu",
        name="System Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def sample_inactive_student(db_session: Session) -> User:
    inactive = User(
        id=uuid.uuid4(),
        email="inactive@college.edu",
        name="Suspended Student",
        role=UserRole.STUDENT,
        is_active=False,
    )
    db_session.add(inactive)
    db_session.commit()
    db_session.refresh(inactive)
    return inactive


@pytest.mark.asyncio
async def test_health_check_remains_intact():
    """Verify health endpoint continues to return 200 without authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_missing_authorization_header():
    """Reject request with 401 when Authorization header is omitted."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth-test/me")
    assert response.status_code == 401
    assert "credentials were not provided" in response.json()["detail"]
    assert "Bearer" in response.headers.get("WWW-Authenticate", "")


@pytest.mark.asyncio
async def test_invalid_authorization_scheme():
    """Reject request with 401 when scheme is Basic instead of Bearer."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ="},
        )
    assert response.status_code == 401
    assert "Bearer token required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_empty_bearer_token():
    """Reject request with 401 when token string is empty or blank."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": "Bearer    "},
        )
    assert response.status_code == 401
    assert "Empty or whitespace" in response.json()["detail"]


@pytest.mark.asyncio
async def test_malformed_token():
    """Reject request with 401 when token cannot be parsed as a JWT."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": "Bearer this-is-not-a-valid-jwt-token"},
        )
    assert response.status_code == 401
    assert "Malformed or unreadable token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_token_signature(sample_student):
    """Reject request with 401 when token is signed with a different key."""
    tampered_token = create_token(
        sub=str(sample_student.id),
        secret="completely-different-wrong-key-9999",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
    assert response.status_code == 401
    assert "Invalid token signature" in response.json()["detail"]


@pytest.mark.asyncio
async def test_expired_token(sample_student):
    """Reject request with 401 when token expiration is in the past."""
    expired_token = create_token(
        sub=str(sample_student.id),
        expires_in_seconds=-3600,
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_audience(sample_student):
    """Reject request with 401 when audience does not match configured audience."""
    bad_aud_token = create_token(
        sub=str(sample_student.id),
        aud="wrong_audience_service",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {bad_aud_token}"},
        )
    assert response.status_code == 401
    assert "Invalid token audience" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_missing_sub_claim():
    """Reject request with 401 when token lacks sub claim."""
    now = int(time.time())
    no_sub_token = jwt.encode(
        {"aud": "authenticated", "exp": now + 3600},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {no_sub_token}"},
        )
    assert response.status_code == 401
    assert "missing required claim: sub" in response.json()["detail"]


@pytest.mark.asyncio
async def test_token_invalid_uuid_sub():
    """Reject request with 401 when sub is not a valid UUID."""
    bad_uuid_token = create_token(sub="not-a-valid-uuid-value")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {bad_uuid_token}"},
        )
    assert response.status_code == 401
    assert "Invalid user ID format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unregistered_user():
    """Reject request with 401 when valid JWT subject does not exist in application database."""
    unregistered_uuid = str(uuid.uuid4())
    token = create_token(sub=unregistered_uuid)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401
    assert "User not registered in the system" in response.json()["detail"]


@pytest.mark.asyncio
async def test_deactivated_user(sample_inactive_student):
    """Reject request with 401 when user account is marked is_active=False."""
    token = create_token(sub=str(sample_inactive_student.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 401
    assert "User account is deactivated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_valid_student_access(sample_student):
    """Allow valid student access to general authenticated and student-only endpoints."""
    token = create_token(sub=str(sample_student.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # /me endpoint
        me_resp = await client.get("/auth-test/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == sample_student.email
        assert me_resp.json()["role"] == "student"

        # student-only endpoint
        student_resp = await client.get("/auth-test/student-only", headers={"Authorization": f"Bearer {token}"})
        assert student_resp.status_code == 200
        assert student_resp.json() == {"status": "success", "role": "student"}


@pytest.mark.asyncio
async def test_role_denial_for_student(sample_student):
    """Reject student attempting to access teacher-only or admin-only endpoints with 403 Forbidden."""
    token = create_token(sub=str(sample_student.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        teacher_resp = await client.get("/auth-test/teacher-only", headers={"Authorization": f"Bearer {token}"})
        assert teacher_resp.status_code == 403
        assert "Operation not permitted. Required role: teacher" in teacher_resp.json()["detail"]

        admin_resp = await client.get("/auth-test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert admin_resp.status_code == 403
        assert "Operation not permitted. Required role: admin" in admin_resp.json()["detail"]


@pytest.mark.asyncio
async def test_teacher_role_permissions(sample_teacher):
    """Allow teacher access to teacher and faculty endpoints; reject admin-only with 403."""
    token = create_token(sub=str(sample_teacher.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        teacher_resp = await client.get("/auth-test/teacher-only", headers={"Authorization": f"Bearer {token}"})
        assert teacher_resp.status_code == 200

        faculty_resp = await client.get("/auth-test/faculty-only", headers={"Authorization": f"Bearer {token}"})
        assert faculty_resp.status_code == 200

        admin_resp = await client.get("/auth-test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert admin_resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_role_permissions(sample_admin):
    """Allow admin access to admin and faculty endpoints."""
    token = create_token(sub=str(sample_admin.id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_resp = await client.get("/auth-test/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert admin_resp.status_code == 200

        faculty_resp = await client.get("/auth-test/faculty-only", headers={"Authorization": f"Bearer {token}"})
        assert faculty_resp.status_code == 200


@pytest.mark.asyncio
async def test_token_role_spoofing_defense(sample_student):
    """
    CRITICAL SECURITY CHECK:
    Verify that injected roles in the JWT payload (e.g. role: 'admin') are strictly ignored.
    The system must check the authoritative database role, denying admin access to a student.
    """
    spoofed_token = create_token(
        sub=str(sample_student.id),
        extra_claims={
            "role": "admin",
            "app_metadata": {"role": "admin"},
            "user_metadata": {"role": "admin"},
        },
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Access admin endpoint with spoofed token
        response = await client.get("/auth-test/admin-only", headers={"Authorization": f"Bearer {spoofed_token}"})

    assert response.status_code == 403
    assert "Operation not permitted. Required role: admin" in response.json()["detail"]


@pytest.mark.asyncio
async def test_missing_jwt_secret_misconfiguration(monkeypatch, sample_student):
    """Verify that a missing SUPABASE_JWT_SECRET in production settings yields HTTP 500."""
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/auth-test/me",
            headers={"Authorization": "Bearer dummy-token"},
        )
    assert response.status_code == 500
    assert "misconfigured: SUPABASE_JWT_SECRET is missing" in response.json()["detail"]
