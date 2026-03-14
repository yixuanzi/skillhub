"""User Management API endpoints (admin-only).

This module provides FastAPI endpoints for admin operations including:
- List users
- Update user
- List roles
- Create role
- Assign roles to users
- List permissions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from models.user import User, Role, Permission
from core.deps import get_current_active_user
from core.exceptions import ValidationException, NotFoundException

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


# Schemas for user management
class RoleResponse(BaseModel):
    """Role response schema."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    username: str
    email: str
    is_active: bool
    roles: List[RoleResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema with pagination."""
    items: List[UserResponse]
    total: int
    page: int
    size: int


class UserUpdate(BaseModel):
    """User update schema (admin) - supports partial updates."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class RoleCreate(BaseModel):
    """Role creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleAssignment(BaseModel):
    """Role assignment schema."""
    role_ids: List[str] = Field(..., min_length=1)


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: str
    resource: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """Schema for admin user creation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username for the new account")
    email: str = Field(..., format="email", description="Email address for the new account")
    password: str = Field(..., min_length=8, max_length=100, description="Password for the new account (min 8 characters)")
    role_ids: List[str] = Field(default_factory=list, description="List of role IDs to assign to the user")
    is_active: bool = Field(default=True, description="Whether the account should be active")


def require_admin(user: User) -> User:
    """Dependency to check if user is admin or super_admin."""
    admin_roles = {"admin", "super_admin"}
    if not any(role.name in admin_roles for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user (admin-only).

    Args:
        user_data: User creation data
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Created user

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 400: If username or email already exists
    """
    from core.security import get_password_hash

    require_admin(current_user)

    # Check if username already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )

    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists"
        )

    # Verify all roles exist
    if user_data.role_ids:
        roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        if len(roles) != len(user_data.role_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more roles not found"
            )
    else:
        roles = []

    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=user_data.is_active
    )
    new_user.roles = roles
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.get("/list/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all users (admin-only).

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        search: Optional search query for username or email
        role_id: Optional role ID to filter by
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Paginated list of users

    Raises:
        HTTPException 403: If user is not admin
    """
    require_admin(current_user)

    # Eager load roles to include them in response
    query = db.query(User).options(selectinload(User.roles))

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )

    # Apply role filter
    if role_id:
        # Join with roles table
        query = query.join(User.roles).filter(Role.id == role_id)

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * size
    users = query.offset(skip).limit(size).all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size
    )


@router.get("/{user_id}/", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific user (admin-only).

    Args:
        user_id: User UUID
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        User details

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
    """
    require_admin(current_user)

    # Eager load roles to include them in response
    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    return UserResponse.model_validate(user)


@router.put("/{user_id}/", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user (admin-only).

    Supports partial updates for:
    - username: Update username (must be unique)
    - email: Update email (must be unique)
    - password: Update password
    - is_active: Enable/disable user account

    Args:
        user_id: User UUID
        user_data: User update data (all fields optional)
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Updated user

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user not found
        HTTPException 400: If username or email already exists
    """
    from core.security import get_password_hash

    require_admin(current_user)

    # Eager load roles to include them in response
    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    # Update username if provided
    if user_data.username is not None:
        # Check if username already exists for another user
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' already exists"
            )
        user.username = user_data.username

    # Update email if provided
    if user_data.email is not None:
        # Check if email already exists for another user
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists"
            )
        user.email = user_data.email

    # Update password if provided
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)

    # Update active status if provided
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.put("/{user_id}/roles/", response_model=UserResponse)
async def assign_user_roles(
    user_id: str,
    assignment: RoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign roles to a user (admin-only).

    Replaces all existing roles with the provided list.

    Args:
        user_id: User UUID
        assignment: Role assignment data
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Updated user with new roles

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If user or role not found
    """
    require_admin(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found"
        )

    # Verify all roles exist
    roles = db.query(Role).filter(Role.id.in_(assignment.role_ids)).all()
    if len(roles) != len(assignment.role_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more roles not found"
        )

    # Replace roles
    user.roles = roles
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


# Role management endpoints
role_router = APIRouter(prefix="/admin/roles", tags=["Admin - Role Management"])


@role_router.get("/list/", response_model=List[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all roles (admin-only).

    Args:
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        List of roles

    Raises:
        HTTPException 403: If user is not admin
    """
    require_admin(current_user)

    roles = db.query(Role).all()
    return [RoleResponse.model_validate(r) for r in roles]


@role_router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new role (admin-only).

    Args:
        role_data: Role creation data
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Created role

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 400: If role name already exists
    """
    require_admin(current_user)

    # Check if role already exists
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.name}' already exists"
        )

    role = Role(
        name=role_data.name,
        description=role_data.description
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    return RoleResponse.model_validate(role)


@role_router.get("/{role_id}/", response_model=RoleResponse)
async def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific role (admin-only).

    Args:
        role_id: Role UUID
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Role details

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If role not found
    """
    require_admin(current_user)

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id '{role_id}' not found"
        )

    return RoleResponse.model_validate(role)


@role_router.get("/{role_id}/permissions/", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get permissions for a role (admin-only).

    Args:
        role_id: Role UUID
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        List of permissions

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 404: If role not found
    """
    require_admin(current_user)

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id '{role_id}' not found"
        )

    return [PermissionResponse.model_validate(p) for p in role.permissions]


# Permission management endpoints
permission_router = APIRouter(prefix="/admin/permissions", tags=["Admin - Permission Management"])


@permission_router.get("/list/", response_model=List[PermissionResponse])
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all permissions (admin-only).

    Args:
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        List of permissions

    Raises:
        HTTPException 403: If user is not admin
    """
    require_admin(current_user)

    permissions = db.query(Permission).all()
    return [PermissionResponse.model_validate(p) for p in permissions]
