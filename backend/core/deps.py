"""FastAPI dependency functions for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from core.security import verify_token
# from core.tmpkey_manager import get_user_id_by_tmpkey  # REMOVE THIS LINE
from services.api_key_service import APIKeyService  # ADD THIS LINE

security = HTTPBearer()


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
    """
    token = credentials.credentials
    user = None
    auth_type = "unknown"

    # 首先尝试 API Key 认证 (sk_ 开头)
    if token.startswith("sk_"):
        api_key = APIKeyService.authenticate(db, token)
        if api_key:
            user = db.query(User).filter(User.id == api_key.user_id).first()
            if user:
                auth_type = "api_key"
                # 设置 API key 相关属性
                setattr(user, "auth_type", auth_type)
                setattr(user, "api_key_id", api_key.id)
                setattr(user, "api_key_scopes", api_key.scopes)
                setattr(user, "access_token", token)

                # 检查用户是否激活
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Inactive user",
                    )
                return user

    # 然后尝试 JWT token 认证
    if user is None:
        payload = verify_token(token)
        if payload is not None:
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                auth_type = "jwt"
                setattr(user, "auth_type", auth_type)
                setattr(user, "access_token", token)

                # 检查用户是否激活
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Inactive user",
                    )
                return user

    # 两种验证都失败
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
