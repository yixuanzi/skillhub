"""Resource ACL API endpoints for access control management.

This module provides FastAPI endpoints for resource ACL operations including:
- Create ACL rule
- List ACL rules (with pagination and mode filtering)
- Get ACL rule by ID or resource ID
- Update ACL rule
- Delete ACL rule
- Add/Remove/Update role bindings
- Check user permissions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.acl_resource import (
    ACLRuleCreate,
    ACLRuleUpdate,
    ACLRuleResponse,
    ACLRuleListResponse,
    RoleBindingCreate,
    RoleBindingResponse,
    PermissionCheckRequest,
    PermissionCheckResponse
)
from services.acl_resource_service import ACLResourceService
from core.deps import get_current_active_user
from models.user import User
from models.acl import AccessMode
from core.exceptions import ValidationException, NotFoundException

router = APIRouter(prefix="/acl/resources", tags=["Resource ACL"])


@router.post("/", response_model=ACLRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_acl_rule(
    acl_data: ACLRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new ACL rule for a resource.

    Args:
        acl_data: ACL rule creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created ACL rule response

    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If resource or role not found
    """
    try:
        return ACLResourceService.create(db, acl_data)
    except (ValidationException, NotFoundException) as e:
        status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationException) else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )


@router.get("/", response_model=ACLRuleListResponse)
async def list_acl_rules(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    access_mode: AccessMode | None = Query(None, description="Filter by access mode"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all ACL rules with optional filtering by access mode.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        access_mode: Optional access mode filter (any, rbac)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of ACL rules
    """
    if access_mode:
        acl_rules = ACLResourceService.list_by_mode(db, access_mode, (page - 1) * size, size)
        total = ACLResourceService.count_by_mode(db, access_mode)
    else:
        acl_rules = ACLResourceService.list_all(db, (page - 1) * size, size)
        total = ACLResourceService.count_all(db)

    return ACLRuleListResponse(
        items=acl_rules,
        total=total,
        page=page,
        size=size
    )


@router.get("/{acl_rule_id}", response_model=ACLRuleResponse)
async def get_acl_rule(
    acl_rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific ACL rule by ID.

    Args:
        acl_rule_id: ACL rule UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        ACL rule response

    Raises:
        HTTPException 404: If ACL rule not found
    """
    acl_rule = ACLResourceService.get_by_id(db, acl_rule_id)
    if not acl_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ACL rule with id '{acl_rule_id}' not found"
        )
    return acl_rule


@router.get("/resource/{resource_id}", response_model=ACLRuleResponse)
async def get_acl_rule_by_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get ACL rule by resource ID.

    Args:
        resource_id: Resource UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        ACL rule response

    Raises:
        HTTPException 404: If ACL rule not found
    """
    acl_rule = ACLResourceService.get_by_resource_id(db, resource_id)
    if not acl_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ACL rule for resource '{resource_id}' not found"
        )
    return acl_rule


@router.put("/{acl_rule_id}", response_model=ACLRuleResponse)
async def update_acl_rule(
    acl_rule_id: str,
    acl_data: ACLRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an ACL rule.

    Args:
        acl_rule_id: ACL rule UUID
        acl_data: ACL rule update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated ACL rule response

    Raises:
        HTTPException 404: If ACL rule not found
    """
    try:
        return ACLResourceService.update(db, acl_rule_id, acl_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{acl_rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_acl_rule(
    acl_rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an ACL rule.

    Args:
        acl_rule_id: ACL rule UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If ACL rule not found
    """
    try:
        ACLResourceService.delete(db, acl_rule_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return None


# Role binding endpoints
@router.post("/{acl_rule_id}/role-bindings", response_model=RoleBindingResponse, status_code=status.HTTP_201_CREATED)
async def add_role_binding(
    acl_rule_id: str,
    binding_data: RoleBindingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a role binding to an ACL rule.

    Args:
        acl_rule_id: ACL rule UUID
        binding_data: Role binding data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created role binding response

    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If ACL rule or role not found
    """
    try:
        return ACLResourceService.add_role_binding(db, acl_rule_id, binding_data)
    except (ValidationException, NotFoundException) as e:
        status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationException) else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )


@router.delete("/{acl_rule_id}/role-bindings/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_binding(
    acl_rule_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a role binding from an ACL rule.

    Args:
        acl_rule_id: ACL rule UUID
        role_id: Role UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: If role binding not found
    """
    try:
        ACLResourceService.remove_role_binding(db, acl_rule_id, role_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return None


@router.put("/{acl_rule_id}/role-bindings/{role_id}", response_model=RoleBindingResponse)
async def update_role_binding(
    acl_rule_id: str,
    role_id: str,
    permissions: list[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update permissions for a role binding.

    Args:
        acl_rule_id: ACL rule UUID
        role_id: Role UUID
        permissions: New list of permissions
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated role binding response

    Raises:
        HTTPException 404: If role binding not found
    """
    try:
        return ACLResourceService.update_role_binding(db, acl_rule_id, role_id, permissions)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Permission check endpoint
@router.post("/check-permission/{resource_id}", response_model=PermissionCheckResponse)
async def check_permission(
    resource_id: str,
    check_data: PermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if a user has permission to access a resource.

    Args:
        resource_id: Resource UUID
        check_data: Permission check request data
        db: Database session
        current_user: Authenticated user

    Returns:
        Permission check response with allowed/rejected decision
    """
    try:
        return ACLResourceService.check_permission(db, resource_id, check_data)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
