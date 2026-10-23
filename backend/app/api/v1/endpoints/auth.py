"""Student self-activation and onboarding endpoints (DEC-018)."""
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.roster import QuizAssignment
from app.models.user import User, StudentProfile, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class StudentActivateRequest(BaseModel):
    email: str
    prn: str


class StudentActivateResponse(BaseModel):
    status: str
    message: str
    user_id: str


def _sync_supabase_auth_user(email: str, password: str, name: str) -> Optional[uuid.UUID]:
    """
    Provision or update user credentials in Supabase Auth via Admin REST API.
    Returns the Supabase user UUID if successful, or None on failure/unconfigured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None

    admin_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "name": name,
            "role": "student",
        },
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(admin_url, headers=headers, json=payload)
            if resp.is_success:
                data = resp.json()
                return uuid.UUID(data["id"])

            # 422: User might already exist in Supabase auth; locate user and update password
            if resp.status_code == 422:
                get_resp = client.get(
                    f"{admin_url}?filter=email.eq.{email}",
                    headers=headers,
                )
                if get_resp.is_success:
                    users_data = get_resp.json()
                    users_list = (
                        users_data.get("users", [])
                        if isinstance(users_data, dict)
                        else users_data
                    )
                    for u in users_list:
                        if u.get("email", "").lower() == email.lower():
                            existing_id = uuid.UUID(u["id"])
                            # Update password so student can log in with their PRN
                            client.put(
                                f"{admin_url}/{existing_id}",
                                headers=headers,
                                json={"password": password},
                            )
                            return existing_id
    except Exception as exc:
        logger.warning(f"Failed to communicate with Supabase Admin API: {exc}")

    return None


@router.post(
    "/student-activate",
    response_model=StudentActivateResponse,
    summary="Activate student account using college email and enrolled PRN",
    description=(
        "Enables students enrolled via teacher roster CSV to activate their account on first login. "
        "Verifies that email and PRN exist in quiz_assignments, provisions their Supabase auth account "
        "with PRN as default password, and links all eligible quiz assignments."
    ),
)
async def activate_student(
    payload: StudentActivateRequest,
    db: Session = Depends(get_db),
) -> StudentActivateResponse:
    norm_email = payload.email.strip().lower()
    norm_prn = payload.prn.strip().upper()

    # 1. Verify that this student is enrolled in at least one active quiz roster
    assignment_stmt = select(QuizAssignment).where(
        QuizAssignment.student_email == norm_email,
        QuizAssignment.student_prn == norm_prn,
        QuizAssignment.is_active.is_(True),
    )
    assignment = db.scalar(assignment_stmt)

    if not assignment:
        # Fallback: check case-insensitive match on PRN
        fallback_stmt = select(QuizAssignment).where(
            QuizAssignment.student_email == norm_email,
            QuizAssignment.is_active.is_(True),
        )
        candidates = db.scalars(fallback_stmt).all()
        for cand in candidates:
            if cand.student_prn.strip().upper() == norm_prn:
                assignment = cand
                break

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No eligible student assignment found matching this college email and PRN. Please verify with your professor.",
        )

    # 2. Check if a local User record already exists
    user_stmt = (
        select(User)
        .options(joinedload(User.student_profile))
        .where(User.email == norm_email)
    )
    user = db.scalar(user_stmt)

    raw_password = payload.prn.strip()

    if user:
        # User already exists; ensure profile exists and sync password
        if not user.student_profile:
            profile = StudentProfile(
                id=uuid.uuid4(),
                user_id=user.id,
                prn=norm_prn,
                current_division=assignment.division or "General",
            )
            db.add(profile)

        # Sync Supabase password if configured
        _sync_supabase_auth_user(norm_email, raw_password, user.name)

        # Link all unlinked assignments for this student
        db.execute(
            update(QuizAssignment)
            .where(
                QuizAssignment.student_email == norm_email,
                QuizAssignment.assigned_student_id.is_(None),
            )
            .values(assigned_student_id=user.id)
        )
        db.commit()

        return StudentActivateResponse(
            status="activated",
            message="Student account verified and linked successfully.",
            user_id=str(user.id),
        )

    # 3. Create new user account
    supabase_user_id = _sync_supabase_auth_user(
        norm_email,
        raw_password,
        assignment.student_name,
    )

    user_id = supabase_user_id or uuid.uuid4()

    new_user = User(
        id=user_id,
        email=norm_email,
        name=assignment.student_name,
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    new_profile = StudentProfile(
        id=uuid.uuid4(),
        user_id=new_user.id,
        prn=norm_prn,
        current_division=assignment.division or "General",
    )
    db.add(new_profile)

    # Link all assignments for this student
    db.execute(
        update(QuizAssignment)
        .where(QuizAssignment.student_email == norm_email)
        .values(assigned_student_id=new_user.id)
    )
    db.commit()

    return StudentActivateResponse(
        status="activated",
        message="Student account activated with PRN as default password.",
        user_id=str(new_user.id),
    )
