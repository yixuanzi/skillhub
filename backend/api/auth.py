"""Authentication API endpoints for user registration, login, and token management.

This module provides FastAPI endpoints for authentication operations including:
- User registration
- User login with JWT tokens
- Token refresh
- User logout
- Current user info retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.auth import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from services.auth_service import AuthService
from core.deps import get_current_active_user
from models.user import User
from core.exceptions import AuthException, ValidationException, NotFoundException

router = APIRouter(prefix="/auth", tags=["Authentication"])


# @router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register(
#     user_data: UserCreate,
#     db: Session = Depends(get_db)
# ):
#     """Register a new user.

#     Args:
#         user_data: User registration data (username, email, password)
#         db: Database session

#     Returns:
#         Created user information (without password)

#     Raises:
#         HTTPException 400: If username or email already exists
#     """
#     try:
#         user = AuthService.register(db, user_data)
#         return user
#     except ValidationException as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )


@router.post("/login/", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens.

    Args:
        login_data: Login credentials (username, password)
        db: Database session

    Returns:
        Token response with access_token, refresh_token, token_type, expires_in

    Raises:
        HTTPException 401: If credentials are invalid or user is inactive
    """
    try:
        # Authenticate user
        user = AuthService.authenticate(db, login_data.username, login_data.password)

        # Create tokens
        tokens = AuthService.create_tokens(db, user)
        return tokens

    except AuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh/", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token (last 32 chars)
        db: Database session

    Returns:
        New access token response

    Raises:
        HTTPException 401: If refresh token is invalid or expired
    """
    try:
        token_response = AuthService.refresh_token(db, refresh_data.refresh_token)
        return token_response

    except (AuthException, NotFoundException) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout/", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Invalidate refresh token (logout).

    Args:
        refresh_data: Refresh token to invalidate (last 32 chars)
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 401: If refresh token is invalid
    """
    try:
        AuthService.logout(db, refresh_data.refresh_token)
        return

    except AuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me/", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        Current user information

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    return current_user
