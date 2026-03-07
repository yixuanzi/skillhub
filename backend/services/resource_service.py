"""Resource service for resource management operations.

This module provides the business logic layer for resource CRUD operations,
including creation, retrieval, update, and deletion of resources.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.resource import Resource, ResourceType
from models.user import User
from schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List
import json


class ResourceService:
    """Service class for resource management operations."""

    @staticmethod
    def create(db: Session, resource_data: ResourceCreate, user: Optional[User] = None) -> ResourceResponse:
        """Create a new resource.

        Args:
            db: Database session
            resource_data: Resource creation data
            user: Optional user object for setting owner_id on private resources

        Returns:
            Created resource response

        Raises:
            ValidationException: If resource with the same name already exists
        """
        # 检查名称唯一性
        existing = db.query(Resource).filter(Resource.name == resource_data.name).first()
        if existing:
            raise ValidationException(f"Resource with name '{resource_data.name}' already exists")

        # Get view_scope value (default to private)
        view_scope = resource_data.view_scope if hasattr(resource_data, 'view_scope') and resource_data.view_scope else "private"

        # Set owner_id for private resources
        owner_id = None
        if view_scope == "private" and user:
            owner_id = user.id

        # 创建资源
        new_resource = Resource(
            name=resource_data.name,
            desc=resource_data.desc,
            type=resource_data.type,
            url=resource_data.url,
            view_scope=view_scope,
            owner_id=owner_id,
            api_description=resource_data.api_description if hasattr(resource_data, 'api_description') else None,
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
        - The user is an admin (is_superuser=True)

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
        if resource.view_scope == "public":
            return resource
        if resource.owner_id and user and resource.owner_id == user.id:
            return resource
        if user and getattr(user, 'is_superuser', False):
            return resource

        raise ValidationException("You do not have permission to access this resource")

    @staticmethod
    def list_accessible(db: Session, user: Optional[User], skip: int = 0, limit: int = 100) -> List[Resource]:
        """List resources accessible to the user.

        Returns:
        - All public resources (view_scope='public')
        - User's own private resources (owner_id=user.id)

        Args:
            db: Database session
            user: User object to filter resources for
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of accessible resources
        """
        if user:
            # Return public resources + user's own resources
            return db.query(Resource).filter(
                or_(
                    Resource.view_scope == "public",
                    Resource.owner_id == user.id
                )
            ).offset(skip).limit(limit).all()
        else:
            # Anonymous users only see public resources
            return db.query(Resource).filter(
                Resource.view_scope == "public"
            ).offset(skip).limit(limit).all()

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
