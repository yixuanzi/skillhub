"""Resource API endpoints for resource management operations.

This module provides FastAPI endpoints for resource CRUD operations including:
- Create resource
- List resources (with pagination and type filtering)
- Get resource by ID
- Update resource
- Delete resource
- Call MCP resource (execute MCP server methods)

Security Policy:
- All resources (public and private) have an owner_id set to the creating user
- Read operations (GET):
    * view_scope='public': Accessible to all authenticated users
    * view_scope='private': Only accessible to:
        - Resource owner
        - Users with 'admin' or 'super_admin' role
        - Users granted access via ACL rules
- Write operations (POST/PUT/DELETE):
    * Only the resource owner can modify the resource
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field

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

# Admin role names
ADMIN_ROLES = {"admin", "super_admin"}


def _is_admin_user(user: Optional[User]) -> bool:
    """Check if user has admin or super_admin role.

    Args:
        user: User object with roles relationship

    Returns:
        True if user has admin or super_admin role
    """
    if not user or not user.roles:
        return False
    user_role_names = {role.name for role in user.roles}
    return bool(user_role_names & ADMIN_ROLES)


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
        return ResourceService.create(db, resource_data, user=current_user)
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
    """List resources accessible to the user with optional filtering by type.

    Returns:
    - For admin users: all resources
    - For regular users: public resources, own resources, and ACL-granted resources

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        resource_type: Optional resource type filter (build, gateway, third, mcp)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of accessible resources
    """
    skip = (page - 1) * size

    # Get accessible resources and total count
    resources, total = ResourceService.list_accessible_with_count(db, current_user, skip, size)

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

    Only returns resources the user has access to (public or owned by user).

    Args:
        resource_id: Resource UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Resource response

    Raises:
        HTTPException 404: If resource is not found
        HTTPException 403: If user lacks permission to access the resource
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        resource = ResourceService.get_accessible(db, resource_id, current_user)
        return ResourceResponse.model_validate(resource)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{resource_id}/", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a resource.

    Only the resource owner can update a resource.

    Args:
        resource_id: Resource UUID
        resource_data: Resource update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated resource response

    Raises:
        HTTPException 404: If resource is not found
        HTTPException 403: If user is not the resource owner
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        # Only owner can update, not even admin users
        return ResourceService.update_owner_only(db, resource_id, resource_data, user=current_user)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{resource_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a resource.

    Only the resource owner can delete a resource.

    Args:
        resource_id: Resource UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If resource is not found
        HTTPException 403: If user is not the resource owner
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        # Only owner can delete, not even admin users
        ResourceService.delete_owner_only(db, resource_id, user=current_user)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    return None
