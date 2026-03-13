"""SkillList service for skill market management operations.

This module provides the business logic layer for skill CRUD operations,
including creation, retrieval, update, and deletion of skills in the skill market.

Security Policy:
- Write operations (update/delete) are restricted to:
    * Skill creator (created_by matches user.username)
    * Users with 'admin' or 'super_admin' role
"""
from sqlalchemy.orm import Session
from models.skill_list import SkillList
from models.user import User
from schemas.skill_list import SkillListCreate, SkillListUpdate, SkillListResponse
from core.exceptions import ValidationException, NotFoundException
from typing import Optional, List

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
    def list_with_filters(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        author: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[SkillList], int]:
        """List skills with multiple combined filters (AND logic).

        All provided filters are applied together using AND logic.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            category: Optional category filter
            tags: Optional comma-separated tags filter (matches ANY tag within the tag list, AND with other filters)
            author: Optional creator username filter
            search: Optional search term for fuzzy matching skill name

        Returns:
            Tuple of (list of filtered skills ordered by created_at DESC, total count)
        """
        from sqlalchemy import or_

        query = db.query(SkillList)

        # Apply filters using AND logic
        # Each filter independently can use OR (e.g., tags), but filters combine with AND
        if category:
            query = query.filter(SkillList.category == category)

        if author:
            query = query.filter(SkillList.created_by == author)

        if search:
            # Fuzzy search on skill name (case-insensitive)
            query = query.filter(SkillList.name.ilike(f'%{search}%'))

        if tags:
            # Tags use OR within the tag list (match ANY), but AND with other filters
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if tag_list:
                tag_conditions = [SkillList.tags.like(f'%{tag}%') for tag in tag_list]
                query = query.filter(or_(*tag_conditions))
            else:
                # Empty tag list after parsing = no results
                return [], 0

        # Get total count before applying pagination
        total = query.count()

        # Apply pagination and ordering
        skills = query.order_by(
            SkillList.created_at.desc()
        ).offset(skip).limit(limit).all()

        return skills, total

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
    def update(db: Session, skill_id: str, skill_data: SkillListUpdate, user: Optional[User] = None) -> SkillListResponse:
        """Update an existing skill.

        Only the skill creator or admin users can update skills.

        Args:
            db: Database session
            skill_id: Skill UUID
            skill_data: Skill update data
            user: User object for permission check

        Returns:
            Updated skill response

        Raises:
            NotFoundException: If skill is not found
            ValidationException: If new name conflicts with existing skill or user lacks permission
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        # Check permission - only creator or admin can update
        if not _is_admin_user(user):
            if not user or skill.created_by != user.username:
                raise ValidationException("You do not have permission to update this skill")

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
    def delete(db: Session, skill_id: str, user: Optional[User] = None) -> bool:
        """Delete a skill.

        Only the skill creator or admin users can delete skills.

        Args:
            db: Database session
            skill_id: Skill UUID
            user: User object for permission check

        Returns:
            True if deletion was successful

        Raises:
            NotFoundException: If skill is not found
            ValidationException: If user lacks permission
        """
        skill = db.query(SkillList).filter(SkillList.id == skill_id).first()
        if not skill:
            raise NotFoundException(f"Skill with id '{skill_id}' not found")

        # Check permission - only creator or admin can delete
        if not _is_admin_user(user):
            if not user or skill.created_by != user.username:
                raise ValidationException("You do not have permission to delete this skill")

        db.delete(skill)
        db.commit()

        return True

    @staticmethod
    def get_statistics(db: Session) -> dict:
        """Get skill statistics including total, published, drafts, and active user count.

        Args:
            db: Database session

        Returns:
            Dictionary with statistics:
            - total_skills: Total number of skills
            - published_skills: Skills with 'published' tag
            - draft_skills: Skills without 'published' tag (total - published)
            - new_skills_last_7days: Skills created in the last 7 days
            - active_users: Number of active users (is_active=True)
        """
        from models.user import User
        from datetime import datetime, timedelta

        # Get total skills count
        total_skills = db.query(SkillList).count()

        # Get published skills count (skills with 'published' in tags)
        published_skills = db.query(SkillList).filter(
            SkillList.tags.like('%published%')
        ).count()

        # Calculate draft skills
        draft_skills = total_skills - published_skills

        # Get skills created in the last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        new_skills_last_7days = db.query(SkillList).filter(
            SkillList.created_at >= seven_days_ago
        ).count()

        # Get active users count
        active_users = db.query(User).filter(User.is_active == True).count()

        return {
            "total_skills": total_skills,
            "published_skills": published_skills,
            "draft_skills": draft_skills,
            "new_skills_last_7days": new_skills_last_7days,
            "active_users": active_users
        }
