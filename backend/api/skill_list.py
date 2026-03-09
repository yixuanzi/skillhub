"""Skill List API endpoints for skill market management operations.

This module provides FastAPI endpoints for skill CRUD operations including:
- Create skill
- List skills (with pagination and filtering by category, tags, author)
- Get skill by ID
- Update skill
- Delete skill
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.skill_list import (
    SkillListCreate,
    SkillListUpdate,
    SkillListResponse,
    SkillListListResponse
)
from services.skill_list_service import SkillListService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post("/", response_model=SkillListResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new skill.

    Args:
        skill_data: Skill creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created skill response

    Raises:
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import ValidationException

    try:
        return SkillListService.create(db, skill_data,current_user)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=SkillListListResponse)
async def list_skills(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    category: str | None = Query(None, description="Filter by category"),
    tags: str | None = Query(None, description="Filter by tags (comma-separated)"),
    author: str | None = Query(None, description="Filter by creator username"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all skills with optional filtering.

    Multiple filters are combined using AND logic:
    - category: Exact match
    - author: Exact match on created_by field
    - tags: Matches ANY tag within the comma-separated list

    Example: ?category=data&tags=python,ai returns skills in 'data' category
    that have either 'python' OR 'ai' tags.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        category: Optional category filter
        tags: Optional comma-separated tags filter (matches ANY tag)
        author: Optional creator username filter (maps to created_by)
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of skills
    """
    skip = (page - 1) * size

    # Use combined filters (AND logic between filters, OR within tags)
    skills, total = SkillListService.list_with_filters(
        db, skip, size, category, tags, author
    )

    return SkillListListResponse(
        items=[SkillListResponse.model_validate(s) for s in skills],
        total=total,
        page=page,
        size=size
    )


@router.get("/{skill_id}/", response_model=SkillListResponse)
async def get_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific skill by ID.

    Args:
        skill_id: Skill UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Skill response

    Raises:
        HTTPException 404: If skill is not found
    """
    skill = SkillListService.get_by_id(db, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id '{skill_id}' not found"
        )
    return SkillListResponse.model_validate(skill)


@router.put("/{skill_id}/", response_model=SkillListResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillListUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a skill.

    Only the skill creator or admin users can update skills.

    Args:
        skill_id: Skill UUID
        skill_data: Skill update data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated skill response

    Raises:
        HTTPException 403: If user lacks permission
        HTTPException 404: If skill is not found
        HTTPException 400: If validation fails (e.g., duplicate name)
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        return SkillListService.update(db, skill_id, skill_data, user=current_user)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        # Check if it's a permission error
        if "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{skill_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a skill.

    Only the skill creator or admin users can delete skills.

    Args:
        skill_id: Skill UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 403: If user lacks permission
        HTTPException 404: If skill is not found
    """
    from core.exceptions import NotFoundException, ValidationException

    try:
        SkillListService.delete(db, skill_id, user=current_user)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        # Check if it's a permission error
        if "permission" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return None
