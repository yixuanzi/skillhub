"""SkillList service for skill market management operations.

This module provides the business logic layer for skill CRUD operations,
including creation, retrieval, update, and deletion of skills in the skill market.
"""
from sqlalchemy.orm import Session
from models.skill_list import SkillList
from schemas.skill_list import SkillListCreate, SkillListUpdate, SkillListResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List


class SkillListService:
    """Service class for skill market management operations."""

    @staticmethod
    def create(db: Session, skill_data: SkillListCreate,current_user) -> SkillListResponse:
        """Create a new skill.

        Args:
            db: Database session
            skill_data: Skill creation data

        Returns:
            Created skill response

        Raises:
            ValidationException: If skill with the same name already exists
        """
        # Check name uniqueness
        existing = db.query(SkillList).filter(SkillList.name == skill_data.name).first()
        if existing:
            raise ValidationException(f"Skill with name '{skill_data.name}' already exists")

        # Create skill
        new_skill = SkillList(
            name=skill_data.name,
            description=skill_data.description,
            content=skill_data.content,
            created_by=current_user.username,
            category=skill_data.category,
            tags=skill_data.tags,
            version=skill_data.version
        )

        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)

        return SkillListResponse.model_validate(new_skill)

    @staticmethod
    def get_by_id(db: Session, skill_id: str) -> Optional[SkillList]:
        """Get skill by ID.

        Args:
            db: Database session
            skill_id: Skill UUID

        Returns:
            SkillList object or None if not found
        """
        return db.query(SkillList).filter(SkillList.id == skill_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[SkillList]:
        """Get skill by name.

        Args:
            db: Database session
            name: Skill name

        Returns:
            SkillList object or None if not found
        """
        return db.query(SkillList).filter(SkillList.name == name).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List all skills with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of skills ordered by created_at DESC
        """
        return db.query(SkillList).order_by(
            SkillList.created_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_category(db: Session, category: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by category.

        Args:
            db: Database session
            category: Category to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered skills ordered by created_at DESC
        """
        return db.query(SkillList).filter(
            SkillList.category == category
        ).order_by(
            SkillList.created_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_author(db: Session, author: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by creator.

        Args:
            db: Database session
            author: Creator user ID to filter by (created_by field)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered skills ordered by created_at DESC
        """
        return db.query(SkillList).filter(
            SkillList.created_by == author
        ).order_by(
            SkillList.created_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def list_by_tags(db: Session, tags: str, skip: int = 0, limit: int = 100) -> List[SkillList]:
        """List skills by tags (match ANY).

        Args:
            db: Database session
            tags: Comma-separated tags to filter by (matches ANY tag)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of filtered skills ordered by created_at DESC
        """
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        if not tag_list:
            return []

        # Build OR condition for tags - match ANY of the provided tags
        conditions = []
        for tag in tag_list:
            conditions.append(SkillList.tags.like(f'%{tag}%'))

        from sqlalchemy import or_
        query = db.query(SkillList).filter(or_(*conditions))

        return query.order_by(
            SkillList.created_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def count_all(db: Session) -> int:
        """Count total number of skills.

        Args:
            db: Database session

        Returns:
            Total count of skills
        """
        return db.query(SkillList).count()

    @staticmethod
    def count_by_category(db: Session, category: str) -> int:
        """Count skills by category.

        Args:
            db: Database session
            category: Category to filter by

        Returns:
            Count of filtered skills
        """
        return db.query(SkillList).filter(SkillList.category == category).count()

    @staticmethod
    def count_by_author(db: Session, author: str) -> int:
        """Count skills by creator.

        Args:
            db: Database session
            author: Creator user ID to filter by (created_by field)

        Returns:
            Count of filtered skills
        """
        return db.query(SkillList).filter(SkillList.created_by == author).count()

    @staticmethod
    def count_by_tags(db: Session, tags: str) -> int:
        """Count skills by tags.

        Args:
            db: Database session
            tags: Comma-separated tags to filter by (matches ANY tag)

        Returns:
            Count of filtered skills
        """
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

        if not tag_list:
            return 0

        # Build OR condition for tags - match ANY of the provided tags
        conditions = []
        for tag in tag_list:
            conditions.append(SkillList.tags.like(f'%{tag}%'))

        from sqlalchemy import or_
        return db.query(SkillList).filter(or_(*conditions)).count()

    @staticmethod
    def update(db: Session, skill_id: str, skill_data: SkillListUpdate) -> SkillListResponse:
        """Update an existing skill.

        Args:
            db: Database session
            skill_id: Skill UUID
            skill_data: Skill update data

        Returns:
            Updated skill response

        Raises:
            NotFoundException: If skill is not found
            ValidationException: If new name conflicts with existing skill
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        # Check name uniqueness (if changing name)
        if skill_data.name and skill_data.name != skill.name:
            existing = db.query(SkillList).filter(
                SkillList.name == skill_data.name
            ).first()
            if existing:
                raise ValidationException(f"Skill with name '{skill_data.name}' already exists")
            skill.name = skill_data.name

        # Update fields
        if skill_data.description is not None:
            skill.description = skill_data.description
        if skill_data.content is not None:
            skill.content = skill_data.content
        if skill_data.category is not None:
            skill.category = skill_data.category
        if skill_data.tags is not None:
            skill.tags = skill_data.tags
        if skill_data.version is not None:
            skill.version = skill_data.version

        db.commit()
        db.refresh(skill)

        return SkillListResponse.model_validate(skill)

    @staticmethod
    def delete(db: Session, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            db: Database session
            skill_id: Skill UUID

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If skill is not found
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        db.delete(skill)
        db.commit()

        return True
