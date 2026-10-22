"""User profile API endpoints (DEC-001, DEC-013)."""
from fastapi import APIRouter, Depends

from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile and authoritative database role.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Return the authenticated user's profile.

    Security & Authorization:
    - Reuses the existing get_current_active_user dependency.
    - Authoritative role is strictly resolved from the database.
    - Serialized through UserResponse allowlist (id, email, name, role, is_active).
    - Read-only: never accepts client role overrides.
    """
    return current_user
