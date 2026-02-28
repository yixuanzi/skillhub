"""Resource API endpoints for resource management operations.

This module provides FastAPI endpoints for resource CRUD operations including:
- Create resource
- List resources (with pagination and type filtering)
- Get resource by ID
- Update resource
- Delete resource
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse
)
from services.resource_service import ResourceService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new resource.

    Args:
        resource_data: Resource creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created resource response

    Raises:
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import ValidationException

    try:
        return ResourceService.create(db, resource_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ResourceListResponse)
async def list_resources(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all resources with optional filtering by type.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        resource_type: Optional resource type filter (build, gateway, third)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of resources
    """
    skip = (page - 1) * size

    if resource_type:
        resources = ResourceService.list_by_type(db, resource_type, skip, size)
        total = ResourceService.count_by_type(db, resource_type)
    else:
        resources = ResourceService.list_all(db, skip, size)
        total = ResourceService.count_all(db)

    return ResourceListResponse(
        items=[ResourceResponse.model_validate(r) for r in resources],
        total=total,
        page=page,
        size=size
    )


@router.get("/{resource_id}/", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific resource by ID.

    Args:
        resource_id: Resource UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Resource response

    Raises:
        HTTPException 404: If resource is not found
    """
    resource = ResourceService.get_by_id(db, resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id '{resource_id}' not found"
        )
    return ResourceResponse.model_validate(resource)


@router.put("/{resource_id}/", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a resource.

    Args:
        resource_id: Resource UUID
        resource_data: Resource update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated resource response

    Raises:
        HTTPException 404: If resource is not found
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        return ResourceService.update(db, resource_id, resource_data)
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


@router.delete("/{resource_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a resource.

    Args:
        resource_id: Resource UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If resource is not found
    """
    from core.exceptions import NotFoundException

    try:
        ResourceService.delete(db, resource_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return None
