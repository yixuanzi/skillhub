"""Authentication service for user registration, login, and token management.

This service provides the business logic layer for authentication operations,
including user registration, credential authentication, token creation/refresh,
and logout functionality.
"""
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from models.user import User, RefreshToken
from schemas.auth import UserCreate, UserResponse, TokenResponse, RefreshTokenResponse
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_token_last32
)
#from core.tmpkey_manager import generate_tmpkey, store_tmpkey
from core.exceptions import AuthException, ValidationException, NotFoundException
from config import settings


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def register(db: Session, user_data: UserCreate) -> UserResponse:
        """Register a new user with validation.

        Args:
            db: Database session
            user_data: User registration data (username, email, password)

        Returns:
            Created user response (without password)

        Raises:
            ValidationException: If username or email already exists
            ValidationException: If password doesn't meet requirements
        """
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise ValidationException(f"Username '{user_data.username}' already exists")

        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise ValidationException(f"Email '{user_data.email}' already exists")

        # Note: Password length validation is handled by the UserCreate schema
        # (min_length=8 in Field definition), so we don't need to duplicate it here

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Return user response (Pydantic model handles UUID conversion)
        return UserResponse.model_validate(new_user)

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> User:
        """Authenticate user with credentials.

        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password to verify

        Returns:
            Authenticated user object

        Raises:
            AuthException: If credentials are invalid
            AuthException: If user is inactive
        """
        # Find user by username
        user = db.query(User).filter(User.username == username).first()

        # Check if user exists
        if not user:
            raise AuthException("Invalid username or password")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise AuthException("Invalid username or password")

        # Check if user is active
        if not user.is_active:
            raise AuthException("User account is inactive")

        return user

    @staticmethod
    def create_tokens(db: Session, user: User) -> TokenResponse:
        """Create access and refresh tokens for authenticated user.

        Args:
            db: Database session
            user: Authenticated user object

        Returns:
            Token response with access_token, refresh_token, token_type, expires_in

        Raises:
            AuthException: If token creation fails
        """
        try:
            # Generate a unique token ID (jti - JWT ID)
            import uuid
            jti = str(uuid.uuid4())

            # Create JWT tokens
            access_token = create_access_token({
                "sub": str(user.id),  # Standard JWT claim for subject
                "username": user.username
            })

            refresh_token = create_refresh_token({
                "sub": str(user.id),  # Standard JWT claim for subject
                "username": user.username,
                "jti": jti  # JWT ID for database lookup
            })

            # Calculate refresh token expiration
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # Store refresh token in database using jti (JWT ID)
            db_token = RefreshToken(
                id=jti,  # Use jti as the primary key
                user_id=str(user.id),
                token_hash=refresh_token,  # Store full token for reference (or could store just jti)
                expires_at=expires_at
            )

            db.add(db_token)
            db.commit()

            # Generate and store tmpkey
            # tmpkey = generate_tmpkey()
            # store_tmpkey(tmpkey, str(user.id))

            # Return full tokens (standard JWT practice)
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                #tmpkey=tmpkey,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        except Exception as e:
            db.rollback()
            raise AuthException(f"Failed to create tokens: {str(e)}")

    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> RefreshTokenResponse:
        """Refresh access token using refresh token.

        Args:
            db: Database session
            refresh_token: Full refresh token (not truncated)

        Returns:
            New access token response

        Raises:
            AuthException: If refresh token is invalid or expired
            NotFoundException: If refresh token not found in database
        """
        from core.security import get_password_hash, verify_token

        # Verify the refresh token JWT
        payload = verify_token(refresh_token)
        if payload is None:
            raise AuthException("Invalid refresh token")

        user_id = payload.get("sub")  # Standard JWT claim
        jti = payload.get("jti")  # JWT ID

        if not user_id or not jti:
            raise AuthException("Invalid refresh token payload")

        # Find token in database by jti
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.id == jti
        ).first()

        if not refresh_token_record:
            raise NotFoundException("Refresh token not found")

        # Check expiration
        now = datetime.now(timezone.utc)
        token_expires = refresh_token_record.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)

        if token_expires < now:
            raise AuthException("Refresh token expired")

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise AuthException("User not found or inactive")

        # Create new access token
        new_access_token = create_access_token({
            "sub": str(user.id),  # Standard JWT claim
            "username": user.username
        })

        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    @staticmethod
    def logout(db: Session, refresh_token: str) -> None:
        """Invalidate refresh token (logout).

        Args:
            db: Database session
            refresh_token: Full refresh token to invalidate

        Raises:
            AuthException: If refresh token is invalid
        """
        # Decode token to get jti
        from core.security import verify_token
        payload = verify_token(refresh_token)
        if payload is None:
            raise AuthException("Invalid refresh token")

        jti = payload.get("jti")
        if not jti:
            raise AuthException("Invalid refresh token payload")

        # Find token in database by jti
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.id == jti
        ).first()

        if not refresh_token_record:
            raise AuthException("Invalid refresh token")

        # Delete the token
        db.delete(refresh_token_record)
        db.commit()
