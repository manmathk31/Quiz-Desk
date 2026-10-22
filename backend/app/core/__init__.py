"""Core modules for configuration, security, and lifecycle."""
from app.core.config import settings
from app.core.database import get_db, SessionLocal, engine
from app.core.auth import (
    decode_supabase_jwt,
    get_current_user,
    get_current_active_user,
    require_roles,
    require_student,
    require_teacher,
    require_admin,
    require_faculty,
)

__all__ = [
    "settings",
    "get_db",
    "SessionLocal",
    "engine",
    "decode_supabase_jwt",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "require_student",
    "require_teacher",
    "require_admin",
    "require_faculty",
]

