"""Supabase JWT authentication and role-based authorization dependencies (DEC-001, DEC-013)."""
from typing import Optional, Sequence
import uuid
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole

# HTTP Bearer scheme with auto_error=False to provide tailored RFC 6750 401 responses
bearer_scheme = HTTPBearer(auto_error=False)


def decode_supabase_jwt(
    token: str,
    secret: Optional[str] = None,
    audience: Optional[str] = None,
) -> dict:
    """
    Cryptographically verify and decode a Supabase-issued JWT.

    Validates:
    - Signature integrity using HMAC-SHA256 (HS256) and the Supabase JWT secret.
    - Expiration timestamp (exp).
    - Expected audience (aud, default: 'authenticated').
    - Presence of subject identifier (sub).

    Rejects arbitrary algorithms and unauthorized or malformed tokens.
    """
    signing_key = secret or settings.SUPABASE_JWT_PUBLIC_KEY or settings.SUPABASE_JWT_SECRET
    if not signing_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service misconfigured: SUPABASE_JWT_SECRET is missing",
        )

    expected_audience = audience if audience is not None else settings.SUPABASE_JWT_AUDIENCE

    decode_options = {
        "verify_signature": True,
        "verify_exp": True,
        "require": ["exp", "sub"],
    }
    if expected_audience:
        decode_options["verify_aud"] = True
    else:
        decode_options["verify_aud"] = False

    kwargs = {
        "algorithms": [settings.SUPABASE_JWT_ALGORITHM],
        "options": decode_options,
    }
    if expected_audience:
        kwargs["audience"] = expected_audience
    if settings.SUPABASE_JWT_ISSUER:
        kwargs["issuer"] = settings.SUPABASE_JWT_ISSUER
        decode_options["verify_iss"] = True

    try:
        payload = jwt.decode(
            token,
            key=signing_key,
            **kwargs,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token has expired"'},
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token signature is invalid"'},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid audience"'},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid issuer"'},
        )
    except jwt.MissingRequiredClaimError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token missing required claim: {e.claim}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed or unreadable token",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )


def get_current_user(
    request: Request,
    _credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency: Extract Bearer token, verify Supabase JWT signature and claims,
    and resolve the authenticated subject (sub) to the database User record.

    Enforces:
    - Token presence and valid Bearer scheme.
    - Cryptographic signature and claim verification.
    - Matching user profile exists in application database.
    - User account is active (is_active=True).

    Note on Role Authority:
    User roles are strictly resolved from the authoritative application database ('users.role').
    Roles supplied in JWT claims or request bodies are never trusted for authorization.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, sep, token = auth_header.strip().partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme; Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = token.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty or whitespace bearer token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_supabase_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub) claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not registered in the system",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Convenience dependency returning the authenticated active user."""
    return current_user


def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory returning a callable dependency that checks if the
    authenticated user possesses one of the required authoritative system roles.

    Raises HTTP 403 Forbidden if user role is not permitted.
    """
    def role_verifier(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {role_names}",
            )
        return current_user

    return role_verifier


# Reusable role dependencies
require_student = require_roles(UserRole.STUDENT)
require_teacher = require_roles(UserRole.TEACHER)
require_admin = require_roles(UserRole.ADMIN)
require_faculty = require_roles(UserRole.TEACHER, UserRole.ADMIN)
