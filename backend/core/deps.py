"""FastAPI dependency functions for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from core.security import verify_token
from core.tmpkey_manager import get_user_id_by_tmpkey

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token or tmpkey.

    支持两种认证方式:
    1. JWT token (标准Bearer token)
    2. tmpkey (32字符的临时密钥)

    Args:
        credentials: HTTP Bearer credentials (JWT token or tmpkey)
        db: Database session

    Returns:
        Authenticated user object

    Raises:
        HTTPException 401: If token/tmpkey is invalid or user not found
    """
    token = credentials.credentials
    user_id = None
    auth_type = "unknown"

    # 尝试作为 JWT token 验证
    payload = verify_token(token)
    if payload is not None:
        user_id = payload.get("sub")
        auth_type = "jwt"

    # 如果 JWT 验证失败，尝试作为 tmpkey 验证
    if user_id is None:
        user_id = get_user_id_by_tmpkey(token)
        if user_id is not None:
            auth_type = "tmpkey"

    # 如果两种验证都失败
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # 设置认证类型和token
    setattr(user, "auth_type", auth_type)
    setattr(user, "access_token", token)
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
