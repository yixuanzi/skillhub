"""Resource service for resource management operations.

This module provides the business logic layer for resource CRUD operations,
including creation, retrieval, update, and deletion of resources.

Security Policy:
- All resources (public and private) have an owner_id set to the creating user
- Read operations: public resources accessible to all; private resources only to owner, admin/super_admin, or ACL-granted users
- Write operations: only the resource owner can modify
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from models.resource import Resource, ResourceType
from models.user import User, Role
from models.acl import ACLRule, AccessMode
from schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List
import json

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


class ResourceService:
    """Service class for resource management operations."""

    @staticmethod
    def create(db: Session, resource_data: ResourceCreate, user: Optional[User] = None) -> ResourceResponse:
        """Create a new resource.

        The resource's owner_id will be set to the current user for all resources
        (both public and private) to ensure proper ownership and modification control.

        Args:
            db: Database session
            resource_data: Resource creation data
            user: Optional user object for setting owner_id

        Returns:
            Created resource response

        Raises:
            ValidationException: If resource with the same name already exists
        """
        # 检查名称唯一性
        existing = db.query(Resource).filter(Resource.name == resource_data.name).first()
        if existing:
            raise ValidationException(f"Resource with name '{resource_data.name}' already exists")

        # Get view_scope value (Pydantic schema has default value)
        view_scope = resource_data.view_scope.value if resource_data.view_scope else "private"

        # Set owner_id - all resources should have an owner for proper tracking and control
        owner_id = user.id if user else None

        # 创建资源
        new_resource = Resource(
            name=resource_data.name,
            desc=resource_data.desc,
            type=resource_data.type,
            url=resource_data.url,
            view_scope=view_scope,
            owner_id=owner_id,
            api_description=resource_data.api_description,
            ext=resource_data.ext  # hybrid_property handles JSON serialization
        )

        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        return ResourceResponse.model_validate(new_resource)

    @staticmethod
    def get_by_id(db: Session, resource_id: str) -> Optional[Resource]:
        """Get resource by ID.

        Args:
            db: Database session
            resource_id: Resource UUID

        Returns:
            Resource object or None if not found
        """
        return db.query(Resource).filter(Resource.id == resource_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Resource]:
        """Get resource by name.

        Args:
            db: Database session
            name: Resource name

        Returns:
            Resource object or None if not found
        """
        return db.query(Resource).filter(Resource.name == name).first()

    @staticmethod
    def get_accessible(db: Session, resource_id: str, user: Optional[User]) -> Resource:
        """Get a resource if the user has access to it.

        A user can access a resource if:
        - The resource is public (view_scope='public')
        - The resource is owned by the user (owner_id=user.id)
        - The user is an admin (has admin or super_admin role)
        - The user has been granted access via ACL rules

        Args:
            db: Database session
            resource_id: Resource UUID
            user: User object to check access for

        Returns:
            Resource object

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If user does not have access to the resource
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        # Check access
        # 1. Public resources are accessible to all
        if resource.view_scope == "public":
            return resource

        # No user = anonymous access to private resource denied
        if not user:
            raise ValidationException("You do not have permission to access this resource")

        # 2. Owner can always access their own resources
        if resource.owner_id and resource.owner_id == user.id:
            return resource

        # 3. Admin users (admin/super_admin) can access all resources
        if _is_admin_user(user):
            return resource

        # 4. Check ACL rules for additional access
        acl_permission = ResourceService._check_acl_permission(db, resource_id, user)
        if acl_permission:
            return resource

        raise ValidationException("You do not have permission to access this resource")

    @staticmethod
    def list_accessible(db: Session, user: Optional[User], skip: int = 0, limit: int = 100) -> List[Resource]:
        """List resources accessible to the user.

        Returns:
        - All public resources (view_scope='public')
        - User's own private resources (owner_id=user.id)
        - For admin users: all resources
        - For non-admin users: resources granted via ACL rules

        Args:
            db: Database session
            user: User object to filter resources for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of accessible resources
        """
        # Anonymous users only see public resources
        if not user:
            return db.query(Resource).filter(
                Resource.view_scope == "public"
            ).offset(skip).limit(limit).all()

        # Admin users can see all resources
        if _is_admin_user(user):
            return db.query(Resource).offset(skip).limit(limit).all()

        # Regular users: public resources + own resources + ACL-granted resources
        # Get ACL-granted resource IDs
        acl_resource_ids = ResourceService._get_acl_granted_resource_ids(db, user)

        # Build query for accessible resources
        base_query = db.query(Resource).filter(
            or_(
                Resource.view_scope == "public",
                Resource.owner_id == user.id,
                Resource.id.in_(acl_resource_ids) if acl_resource_ids else False
            )
        )

        return base_query.offset(skip).limit(limit).all()

    @staticmethod
    def list_accessible_with_count(db: Session, user: Optional[User], skip: int = 0, limit: int = 100) -> tuple[List[Resource], int]:
        """List resources accessible to the user with total count for pagination.

        Returns:
        - All public resources (view_scope='public')
        - User's own private resources (owner_id=user.id)
        - For admin users: all resources
        - For non-admin users: resources granted via ACL rules

        Args:
            db: Database session
            user: User object to filter resources for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of accessible resources, total count)
        """
        # Anonymous users only see public resources
        if not user:
            query = db.query(Resource).filter(Resource.view_scope == "public")
            total = query.count()
            return query.offset(skip).limit(limit).all(), total

        # Admin users can see all resources
        if _is_admin_user(user):
            total = db.query(Resource).count()
            return db.query(Resource).offset(skip).limit(limit).all(), total

        # Regular users: public resources + own resources + ACL-granted resources
        # Get ACL-granted resource IDs
        acl_resource_ids = ResourceService._get_acl_granted_resource_ids(db, user)

        # Build query for accessible resources
        base_query = db.query(Resource).filter(
            or_(
                Resource.view_scope == "public",
                Resource.owner_id == user.id,
                Resource.id.in_(acl_resource_ids) if acl_resource_ids else False
            )
        )

        total = base_query.count()
        return base_query.offset(skip).limit(limit).all(), total

    @staticmethod
    def _get_acl_granted_resource_ids(db: Session, user: User) -> List[str]:
        """Get list of resource IDs the user has access to via ACL rules.

        Uses SQLite JSON functions for efficient database-level filtering.

        Args:
            db: Database session
            user: User object

        Returns:
            List of resource IDs accessible via ACL
        """
        from sqlalchemy import func, or_, and_

        if not user or not user.roles:
            return []

        user_role_ids = [str(role.id) for role in user.roles]
        username_literal = user.username.replace("'", "''")  # Escape single quotes

        # Use SQLite JSON functions to filter ACL rules at database level
        # Filter for:
        # 1. access_mode = 'any' OR
        # 2. (access_mode = 'rbac' AND
        #    (conditions->>'$.users' LIKE '%username%' OR
        #     conditions->>'$.roles' LIKE '%role_id%'))

        # Build role filter with OR conditions for each role
        role_filters = [
            func.json_extract(ACLRule.conditions, '$.roles').like(f'%{role_id}%')
            for role_id in user_role_ids
        ]

        # Combine filters: ANY mode OR (RBAC mode AND (user_in_users OR user_has_role))
        query = db.query(ACLRule.resource_id).filter(
            or_(
                ACLRule.access_mode == AccessMode.ANY,
                and_(
                    ACLRule.access_mode == AccessMode.RBAC,
                    or_(
                        func.json_extract(ACLRule.conditions, '$.users').like(f'%{username_literal}%'),
                        *role_filters
                    )
                )
            )
        )

        # Return unique resource IDs
        result = query.distinct().all()
        return [row[0] for row in result]

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Resource]:
        """List all resources with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of resources
        """
        return db.query(Resource).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_type(db: Session, resource_type: str, skip: int = 0, limit: int = 100) -> List[Resource]:
        """List resources by type.

        Args:
            db: Database session
            resource_type: Resource type to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered resources
        """
        return db.query(Resource).filter(
            Resource.type == resource_type
        ).offset(skip).limit(limit).all()

    @staticmethod
    def count_all(db: Session) -> int:
        """Count total number of resources.

        Args:
            db: Database session

        Returns:
            Total count of resources
        """
        return db.query(Resource).count()

    @staticmethod
    def count_by_type(db: Session, resource_type: str) -> int:
        """Count resources by type.

        Args:
            db: Database session
            resource_type: Resource type to filter by

        Returns:
            Count of filtered resources
        """
        return db.query(Resource).filter(Resource.type == resource_type).count()

    @staticmethod
    def update(db: Session, resource_id: str, resource_data: ResourceUpdate, user: Optional[User] = None) -> ResourceResponse:
        """Update an existing resource.

        Args:
            db: Database session
            resource_id: Resource UUID
            resource_data: Resource update data
            user: User object for ownership validation

        Returns:
            Updated resource response

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If new name conflicts with existing resource or user lacks permission
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        # Check ownership for private resources
        if resource.view_scope == "private" and resource.owner_id:
            if not user or (resource.owner_id != user.id and not getattr(user, 'is_superuser', False)):
                raise ValidationException("You do not have permission to update this resource")

        # 检查名称唯一性（如果更改了名称）
        if resource_data.name and resource_data.name != resource.name:
            existing = db.query(Resource).filter(
                Resource.name == resource_data.name
            ).first()
            if existing:
                raise ValidationException(f"Resource with name '{resource_data.name}' already exists")
            resource.name = resource_data.name

        # 更新字段
        if resource_data.desc is not None:
            resource.desc = resource_data.desc
        if resource_data.type is not None:
            resource.type = resource_data.type
        if resource_data.url is not None:
            resource.url = resource_data.url
        if resource_data.view_scope is not None:
            resource.view_scope = resource_data.view_scope
        if resource_data.api_description is not None:
            resource.api_description = resource_data.api_description
        if resource_data.ext is not None:
            resource.ext = resource_data.ext  # hybrid_property handles JSON serialization

        db.commit()
        db.refresh(resource)

        return ResourceResponse.model_validate(resource)

    @staticmethod
    def delete(db: Session, resource_id: str, user: Optional[User] = None) -> bool:
        """Delete a resource.

        Args:
            db: Database session
            resource_id: Resource UUID
            user: User object for ownership validation

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If user lacks permission to delete the resource
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        # Check ownership for private resources
        if resource.view_scope == "private" and resource.owner_id:
            if not user or (resource.owner_id != user.id and not getattr(user, 'is_superuser', False)):
                raise ValidationException("You do not have permission to delete this resource")

        db.delete(resource)
        db.commit()

        return True

    @staticmethod
    def list_by_view_scope(db: Session, view_scope: str, skip: int = 0, limit: int = 100) -> List[Resource]:
        """List resources by view_scope.

        Args:
            db: Database session
            view_scope: View scope to filter by (e.g., 'private', 'public', 'team')
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered resources
        """
        return db.query(Resource).filter(
            Resource.view_scope == view_scope
        ).offset(skip).limit(limit).all()

    @staticmethod
    def count_by_view_scope(db: Session, view_scope: str) -> int:
        """Count resources by view_scope.

        Args:
            db: Database session
            view_scope: View scope to filter by

        Returns:
            Count of filtered resources
        """
        return db.query(Resource).filter(Resource.view_scope == view_scope).count()

    @staticmethod
    def get_mcp_resources(db: Session, skip: int = 0, limit: int = 100) -> List[Resource]:
        """Get all MCP type resources.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of MCP resources
        """
        return db.query(Resource).filter(
            Resource.type == ResourceType.MCP
        ).offset(skip).limit(limit).all()

    @staticmethod
    def _check_acl_permission(db: Session, resource_id: str, user: User) -> bool:
        """Check if user has permission via ACL rules.

        Args:
            db: Database session
            resource_id: Resource UUID
            user: User object

        Returns:
            True if user has ACL permission, False otherwise
        """
        # Get ACL rule for resource
        acl_rule = db.query(ACLRule).options(
            joinedload(ACLRule.role_bindings)
        ).filter(ACLRule.resource_id == resource_id).first()

        if not acl_rule:
            return False

        # ANY mode means public access
        if acl_rule.access_mode == AccessMode.ANY:
            return True

        # RBAC mode - check user permissions
        if acl_rule.access_mode == AccessMode.RBAC:
            # Reload user with roles
            user_with_roles = db.query(User).options(
                joinedload(User.roles)
            ).filter(User.id == user.id).first()

            if not user_with_roles:
                return False

            # Check conditions - user whitelist
            if acl_rule.conditions:
                conditions = acl_rule.conditions
                if "users" in conditions and conditions["users"]:
                    if user.username in conditions["users"]:
                        return True

                # Check conditions - role whitelist
                if "roles" in conditions and conditions["roles"]:
                    user_role_ids = [str(role.id) for role in user_with_roles.roles]
                    if any(role_id in conditions["roles"] for role_id in user_role_ids):
                        return True

        return False

    @staticmethod
    def update_owner_only(db: Session, resource_id: str, resource_data: ResourceUpdate, user: Optional[User] = None) -> ResourceResponse:
        """Update an existing resource - only the owner can update.

        Args:
            db: Database session
            resource_id: Resource UUID
            resource_data: Resource update data
            user: User object for ownership validation

        Returns:
            Updated resource response

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If new name conflicts with existing resource or user is not the owner
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        # Only owner can update (admin users cannot modify other users' resources)
        if resource.owner_id:
            if not user or resource.owner_id != user.id:
                raise ValidationException("You do not have permission to update this resource")

        # 检查名称唯一性（如果更改了名称）
        if resource_data.name and resource_data.name != resource.name:
            existing = db.query(Resource).filter(
                Resource.name == resource_data.name
            ).first()
            if existing:
                raise ValidationException(f"Resource with name '{resource_data.name}' already exists")
            resource.name = resource_data.name

        # 更新字段
        if resource_data.desc is not None:
            resource.desc = resource_data.desc
        if resource_data.type is not None:
            resource.type = resource_data.type
        if resource_data.url is not None:
            resource.url = resource_data.url
        if resource_data.view_scope is not None:
            resource.view_scope = resource_data.view_scope
        if resource_data.api_description is not None:
            resource.api_description = resource_data.api_description
        if resource_data.ext is not None:
            resource.ext = resource_data.ext

        db.commit()
        db.refresh(resource)

        return ResourceResponse.model_validate(resource)

    @staticmethod
    def delete_owner_only(db: Session, resource_id: str, user: Optional[User] = None) -> bool:
        """Delete a resource - only the owner can delete.

        Args:
            db: Database session
            resource_id: Resource UUID
            user: User object for ownership validation

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If user is not the resource owner
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        # Only owner can delete (admin users cannot delete other users' resources)
        if resource.owner_id:
            if not user or resource.owner_id != user.id:
                raise ValidationException("You do not have permission to delete this resource")

        db.delete(resource)
        db.commit()

        return True
