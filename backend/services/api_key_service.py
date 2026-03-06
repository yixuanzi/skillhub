"""API Key service for API key management operations.

This module provides the business logic layer for API key CRUD operations,
including creation, authentication, rotation, and revocation.
"""
import hashlib
import secrets
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from models.api_key import APIKey
from models.user import User
from schemas.api_key import APIKeyCreate, APIKeyUpdate
from core.exceptions import ValidationException, NotFoundException


class APIKeyService:
    """Service class for API key management operations."""

    # Maximum number of active API keys per user
    MAX_ACTIVE_KEYS = 100

    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """Generate a new API key.

        Returns:
            Tuple of (full_key, key_hash, key_prefix)

        Note:
            The full key is only returned once during creation.
            Only the hash is stored in the database.
        """
        key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:10]
        return key, key_hash, key_prefix

    @staticmethod
    def create(db: Session, user: User, data: APIKeyCreate) -> tuple[APIKey, str]:
        """Create a new API key for a user.

        Args:
            db: Database session
            user: User object
            data: API key creation data

        Returns:
            Tuple of (APIKey object, full_key)

        Raises:
            ValidationException: If validation fails (invalid scopes or max keys reached)
        """
        # Validate scopes
        try:
            data.validate_scopes()
        except ValueError as e:
            raise ValidationException(str(e))

        # Check max keys limit
        active_count = db.query(APIKey).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True
        ).count()
        if active_count >= APIKeyService.MAX_ACTIVE_KEYS:
            raise ValidationException(
                f"Maximum {APIKeyService.MAX_ACTIVE_KEYS} active API keys allowed"
            )

        # Generate key
        key, key_hash, key_prefix = APIKeyService.generate_api_key()

        api_key = APIKey(
            user_id=user.id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=data.scopes,
            expires_at=data.expires_at,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return api_key, key

    @staticmethod
    def list_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[APIKey]:
        """List all API keys for a user.

        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of API keys owned by the user
        """
        return db.query(APIKey).filter(
            APIKey.user_id == user_id
        ).order_by(APIKey.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, key_id: str, user_id: str) -> APIKey:
        """Get API key by ID (user must own it).

        Args:
            db: Database session
            key_id: API key UUID
            user_id: ID of the user

        Returns:
            APIKey object

        Raises:
            NotFoundException: If key not found or not owned by user
        """
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        if not api_key:
            raise NotFoundException("API key not found")
        return api_key

    @staticmethod
    def update(db: Session, key_id: str, user_id: str, data: APIKeyUpdate) -> APIKey:
        """Update API key metadata.

        Note: This does not regenerate the key. Use rotate() for that.

        Args:
            db: Database session
            key_id: API key UUID
            user_id: ID of the user who owns the key
            data: Update data

        Returns:
            Updated APIKey object

        Raises:
            NotFoundException: If key not found or not owned by user
            ValidationException: If scope validation fails
        """
        api_key = APIKeyService.get_by_id(db, key_id, user_id)

        # Validate scopes if provided
        try:
            data.validate_scopes()
        except ValueError as e:
            raise ValidationException(str(e))

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(api_key, field, value)

        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def revoke(db: Session, key_id: str, user_id: str) -> APIKey:
        """Revoke (deactivate) an API key.

        Args:
            db: Database session
            key_id: API key UUID
            user_id: ID of the user who owns the key

        Returns:
            Revoked APIKey object

        Raises:
            NotFoundException: If key not found or not owned by user
        """
        api_key = APIKeyService.get_by_id(db, key_id, user_id)
        api_key.is_active = False
        db.commit()
        return api_key

    @staticmethod
    def rotate(db: Session, key_id: str, user_id: str) -> tuple[APIKey, str]:
        """Rotate API key - generate new key, keep settings.

        Args:
            db: Database session
            key_id: API key UUID
            user_id: ID of the user who owns the key

        Returns:
            Tuple of (APIKey object, new_full_key)

        Raises:
            NotFoundException: If key not found or not owned by user
        """
        api_key = APIKeyService.get_by_id(db, key_id, user_id)

        # Generate new key
        key, key_hash, key_prefix = APIKeyService.generate_api_key()

        # Update but keep name, scopes, expires_at
        api_key.key_hash = key_hash
        api_key.key_prefix = key_prefix

        db.commit()
        db.refresh(api_key)

        return api_key, key

    @staticmethod
    def authenticate(db: Session, key: str) -> Optional[APIKey]:
        """Authenticate API key, return APIKey object if valid.

        Args:
            db: Database session
            key: Full API key string

        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()

        if not api_key:
            return None

        # Check expiration
        # Normalize both datetimes to naive for comparison (SQLite doesn't preserve timezone)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = api_key.expires_at.replace(tzinfo=None) if api_key.expires_at and api_key.expires_at.tzinfo else api_key.expires_at
        if expires_at and expires_at < now:
            return None

        # Update last_used_at (store as naive datetime)
        api_key.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        return api_key

    @staticmethod
    def has_scope(api_key: APIKey, required_scope: str) -> bool:
        """Check if API key has required scope.

        Args:
            api_key: APIKey object
            required_scope: Scope to check

        Returns:
            True if key has the required scope, False otherwise
        """
        return required_scope in api_key.scopes
