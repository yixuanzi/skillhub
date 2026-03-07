"""MToken API endpoints for token management operations.

This module provides FastAPI endpoints for token CRUD operations including:
- Create token
- List tokens (with pagination and filtering)
- Get token by ID
- Update token
- Delete token
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.mtoken import (
    MTokenCreate,
    MTokenUpdate,
    MTokenResponse,
    MTokenListResponse
)
from services.mtoken_service import MTokenService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/mtokens", tags=["MTokens"])


@router.post("/", response_model=MTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_mtoken(
    token_data: MTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new token.

    Args:
        token_data: Token creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created token response

    Raises:
        HTTPException 400: If validation fails
    """
    from core.exceptions import ValidationException

    try:
        return MTokenService.create(db, token_data, str(current_user.id))
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=MTokenListResponse)
async def list_mtokens(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    app_name: str | None = Query(None, description="Filter by app name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all tokens for the current user with optional filtering.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        app_name: Optional app name filter
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of tokens owned by the current user
    """
    skip = (page - 1) * size

    # Apply filters based on provided parameters
    if app_name:
        mtokens = MTokenService.list_by_app(db, str(current_user.id), app_name, skip, size)
        total = MTokenService.count_by_app(db, str(current_user.id), app_name)
    else:
        mtokens = MTokenService.list_all(db, str(current_user.id), skip, size)
        total = MTokenService.count_all(db, str(current_user.id))

    return MTokenListResponse(
        items=[MTokenResponse.model_validate(m) for m in mtokens],
        total=total,
        page=page,
        size=size
    )


@router.get("/{token_id}/", response_model=MTokenResponse)
async def get_mtoken(
    token_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific token by ID.

    Args:
        token_id: Token UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Token response

    Raises:
        HTTPException 404: If token is not found or not owned by user
    """
    mtoken = MTokenService.get_by_id(db, token_id, str(current_user.id))
    if not mtoken:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token with id '{token_id}' not found"
        )
    return MTokenResponse.model_validate(mtoken)


@router.put("/{token_id}/", response_model=MTokenResponse)
async def update_mtoken(
    token_id: str,
    token_data: MTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a token.

    Args:
        token_id: Token UUID
        token_data: Token update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated token response

    Raises:
        HTTPException 404: If token is not found or not owned by user
    """
    from core.exceptions import NotFoundException

    try:
        return MTokenService.update(db, token_id, str(current_user.id), token_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{token_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mtoken(
    token_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a token.

    Args:
        token_id: Token UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If token is not found or not owned by user
    """
    from core.exceptions import NotFoundException

    try:
        MTokenService.delete(db, token_id, str(current_user.id))
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return None
