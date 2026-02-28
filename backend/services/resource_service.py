"""Resource service for resource management operations.

This module provides the business logic layer for resource CRUD operations,
including creation, retrieval, update, and deletion of resources.
"""
from sqlalchemy.orm import Session
from models.resource import Resource
from schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List
import json


class ResourceService:
    """Service class for resource management operations."""

    @staticmethod
    def create(db: Session, resource_data: ResourceCreate) -> ResourceResponse:
        """Create a new resource.

        Args:
            db: Database session
            resource_data: Resource creation data

        Returns:
            Created resource response

        Raises:
            ValidationException: If resource with the same name already exists
        """
        # 检查名称唯一性
        existing = db.query(Resource).filter(Resource.name == resource_data.name).first()
        if existing:
            raise ValidationException(f"Resource with name '{resource_data.name}' already exists")

        # 创建资源
        new_resource = Resource(
            name=resource_data.name,
            desc=resource_data.desc,
            type=resource_data.type,
            url=resource_data.url,
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
    def update(db: Session, resource_id: str, resource_data: ResourceUpdate) -> ResourceResponse:
        """Update an existing resource.

        Args:
            db: Database session
            resource_id: Resource UUID
            resource_data: Resource update data

        Returns:
            Updated resource response

        Raises:
            NotFoundException: If resource is not found
            ValidationException: If new name conflicts with existing resource
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

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
        if resource_data.ext is not None:
            resource.ext = resource_data.ext  # hybrid_property handles JSON serialization

        db.commit()
        db.refresh(resource)

        return ResourceResponse.model_validate(resource)

    @staticmethod
    def delete(db: Session, resource_id: str) -> bool:
        """Delete a resource.

        Args:
            db: Database session
            resource_id: Resource UUID

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If resource is not found
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise NotFoundException(f"Resource with id '{resource_id}' not found")

        db.delete(resource)
        db.commit()

        return True
