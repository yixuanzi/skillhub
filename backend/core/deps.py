"""FastAPI dependency functions for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.user import User, Role
from core.security import verify_token
# from core.tmpkey_manager import get_user_id_by_tmpkey  # REMOVE THIS LINE
from services.api_key_service import APIKeyService  # ADD THIS LINE
from typing import Optional

security = HTTPBearer()


def _authenticate_user(db: Session, token: str) -> Optional[User]:
    """Authenticate user by API key or JWT token.

    This is a shared authentication function used by both required and optional
    authentication dependencies. It tries API Key authentication first (for tokens
    starting with 'sk_'), then falls back to JWT token authentication.

    支持两种认证方式:
    1. API Key (以 sk_ 开头)
    2. JWT token (标准Bearer token)

    Args:
        db: Database session
        token: The authentication token (API key or JWT)

    Returns:
        Authenticated user object with auth_type and other attributes set,
        or None if authentication fails
    """
    user = None

    # 首先尝试 API Key 认证 (sk_ 开头)
    if token.startswith("sk_"):
        api_key = APIKeyService.authenticate(db, token)
        if api_key:
            user = db.query(User).options(
                joinedload(User.roles).joinedload(Role.permissions)
            ).filter(User.id == api_key.user_id).first()
            if user and user.is_active:
                setattr(user, "auth_type", "api_key")
                setattr(user, "access_token", token)
                setattr(user, "api_key_id", api_key.id)
                setattr(user, "api_key_scopes", api_key.scopes)
                return user

    # 然后尝试 JWT token 认证
    if user is None:
        payload = verify_token(token)
        if payload is not None:
            user_id = payload.get("sub")
            user = db.query(User).options(
                joinedload(User.roles).joinedload(Role.permissions)
            ).filter(User.id == user_id).first()
            if user and user.is_active:
                setattr(user, "auth_type", "jwt")
                setattr(user, "access_token", token)
                return user

    return None




def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from API key or JWT token.

    支持两种认证方式:
    1. API Key (以 sk_ 开头)
    2. JWT token (标准Bearer token)

    Args:
        credentials: HTTP Bearer credentials (API key or JWT token)
        db: Database session

    Returns:
        Authenticated user object with auth_type attribute

    Raises:
        HTTPException 401: If token/api_key is invalid or user not found
        HTTPException 403: If user is inactive
    """
    token = credentials.credentials
    user = _authenticate_user(db, token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (verifies user is active).

    Args:
        current_user: Current user from JWT token

    Returns:
        Active user object

    Raises:
        HTTPException 400: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authentication is provided, otherwise return None.

    This is an optional authentication dependency that allows unauthenticated access.
    If valid credentials are provided, returns the user object. If not, returns None.

    支持两种认证方式:
    1. API Key (以 sk_ 开头)
    2. JWT token (标准Bearer token)

    Args:
        credentials: Optional HTTP Bearer credentials (API key or JWT token)
        db: Database session

    Returns:
        Authenticated user object if credentials are valid, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    return _authenticate_user(db, token)
