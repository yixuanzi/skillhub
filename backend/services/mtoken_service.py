"""MToken service for token management operations.

This module provides the business logic layer for token CRUD operations,
including creation, retrieval, update, and deletion of stored tokens.
"""
from sqlalchemy.orm import Session
from models.mtoken import MToken
from schemas.mtoken import MTokenCreate, MTokenUpdate, MTokenResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List


class MTokenService:
    """Service class for token management operations."""

    @staticmethod
    def create(db: Session, token_data: MTokenCreate, user_id: str) -> MTokenResponse:
        """Create a new token for the user.

        Args:
            db: Database session
            token_data: Token creation data
            user_id: ID of the user creating the token

        Returns:
            Created token response

        Raises:
            ValidationException: If validation fails
        """
        # Create token
        new_token = MToken(
            app_name=token_data.app_name,
            key_name=token_data.key_name,
            value=token_data.value,
            desc=token_data.desc,
            created_by=user_id
        )

        db.add(new_token)
        db.commit()
        db.refresh(new_token)

        return MTokenResponse.model_validate(new_token)

    @staticmethod
    def get_by_id(db: Session, token_id: str, user_id: str) -> Optional[MToken]:
        """Get token by ID (only if owned by the user).

        Args:
            db: Database session
            token_id: Token UUID
            user_id: ID of the user requesting the token

        Returns:
            MToken object or None if not found or not owned by user
        """
        return db.query(MToken).filter(
            MToken.id == token_id,
            MToken.created_by == user_id
        ).first()

    @staticmethod
    def list_all(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[MToken]:
        """List all tokens for the user with pagination.

        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of tokens owned by the user
        """
        return db.query(MToken).filter(
            MToken.created_by == user_id
        ).order_by(MToken.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_app(db: Session, user_id: str, app_name: str, skip: int = 0, limit: int = 100) -> List[MToken]:
        """List tokens by app name for the user.

        Args:
            db: Database session
            user_id: ID of the user
            app_name: App name to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of filtered tokens owned by the user
        """
        return db.query(MToken).filter(
            MToken.created_by == user_id,
            MToken.app_name == app_name
        ).order_by(MToken.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count_all(db: Session, user_id: str) -> int:
        """Count total tokens for the user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            Total count of tokens owned by the user
        """
        return db.query(MToken).filter(MToken.created_by == user_id).count()

    @staticmethod
    def count_by_app(db: Session, user_id: str, app_name: str) -> int:
        """Count tokens by app name for the user.

        Args:
            db: Database session
            user_id: ID of the user
            app_name: App name to filter by

        Returns:
            Count of filtered tokens owned by the user
        """
        return db.query(MToken).filter(
            MToken.created_by == user_id,
            MToken.app_name == app_name
        ).count()

    @staticmethod
    def update(db: Session, token_id: str, user_id: str, token_data: MTokenUpdate) -> MTokenResponse:
        """Update an existing token.

        Args:
            db: Database session
            token_id: Token UUID
            user_id: ID of the user who owns the token
            token_data: Token update data

        Returns:
            Updated token response

        Raises:
            NotFoundException: If token is not found or not owned by user
        """
        token = db.query(MToken).filter(
            MToken.id == token_id,
            MToken.created_by == user_id
        ).first()

        if not token:
            raise NotFoundException(f"Token with id '{token_id}' not found")

        # Update fields
        if token_data.app_name is not None:
            token.app_name = token_data.app_name
        if token_data.key_name is not None:
            token.key_name = token_data.key_name
        if token_data.value is not None:
            token.value = token_data.value
        if token_data.desc is not None:
            token.desc = token_data.desc

        db.commit()
        db.refresh(token)

        return MTokenResponse.model_validate(token)

    @staticmethod
    def delete(db: Session, token_id: str, user_id: str) -> bool:
        """Delete a token.

        Args:
            db: Database session
            token_id: Token UUID
            user_id: ID of the user who owns the token

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If token is not found or not owned by user
        """
        token = db.query(MToken).filter(
            MToken.id == token_id,
            MToken.created_by == user_id
        ).first()

        if not token:
            raise NotFoundException(f"Token with id '{token_id}' not found")

        db.delete(token)
        db.commit()

        return True
