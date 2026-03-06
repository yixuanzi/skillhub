"""API Key endpoints for API key management operations.

This module provides FastAPI endpoints for API key CRUD operations including:
- Create API key
- List API keys
- Get API key by ID
- Update API key
- Revoke API key
- Rotate API key
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.api_key import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyUpdate,
    APIKeyListResponse
)
from services.api_key_service import APIKeyService
from core.deps import get_current_active_user
from models.user import User
from core.exceptions import ValidationException, NotFoundException

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new API key.

    The full API key is only returned once during creation.
    Store it securely - you won't be able to retrieve it again.

    Args:
        data: API key creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created API key response with full key

    Raises:
        HTTPException 400: If validation fails
    """
    try:
        api_key, full_key = APIKeyService.create(db, current_user, data)
        return APIKeyCreateResponse(
            key=full_key,
            api_key=APIKeyResponse.model_validate(api_key)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all API keys for the current user.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of API keys owned by the current user
    """
    api_keys = APIKeyService.list_by_user(db, str(current_user.id), skip, limit)
    return [APIKeyResponse.model_validate(key) for key in api_keys]


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get API key details by ID.

    Note: This does not include the full API key (only the prefix).

    Args:
        key_id: API key UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        API key response

    Raises:
        HTTPException 404: If key not found or not owned by user
    """
    try:
        api_key = APIKeyService.get_by_id(db, key_id, str(current_user.id))
        return APIKeyResponse.model_validate(api_key)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    data: APIKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update API key metadata.

    This does not regenerate the key. Use the rotate endpoint for that.

    Args:
        key_id: API key UUID
        data: Update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated API key response

    Raises:
        HTTPException 404: If key not found
        HTTPException 400: If validation fails
    """
    try:
        api_key = APIKeyService.update(db, key_id, str(current_user.id), data)
        return APIKeyResponse.model_validate(api_key)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{key_id}", response_model=APIKeyResponse)
async def revoke_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Revoke (deactivate) an API key.

    The key is marked as inactive but not deleted.

    Args:
        key_id: API key UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Revoked API key response

    Raises:
        HTTPException 404: If key not found
    """
    try:
        api_key = APIKeyService.revoke(db, key_id, str(current_user.id))
        return APIKeyResponse.model_validate(api_key)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
async def rotate_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Rotate API key - generate new key, keep settings.

    Invalidates the old key and returns a new one.
    The full new key is only returned once.

    Args:
        key_id: API key UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        New API key with full key

    Raises:
        HTTPException 404: If key not found
    """
    try:
        api_key, full_key = APIKeyService.rotate(db, key_id, str(current_user.id))
        return APIKeyCreateResponse(
            key=full_key,
            api_key=APIKeyResponse.model_validate(api_key)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
