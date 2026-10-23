import uuid
from pydantic import BaseModel, ConfigDict
from app.models.user import UserRole


class UserResponse(BaseModel):
    """
    Public user profile response schema.
    Strict allowlist: id, email, name, role, is_active.
    Excludes any sensitive, internal, or ORM attributes.
    """
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
