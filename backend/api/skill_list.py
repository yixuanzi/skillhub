"""Skill List API endpoints for skill market management operations.

This module provides FastAPI endpoints for skill CRUD operations including:
- Create skill
- List skills (with pagination and filtering by category, tags, author)
- Get skill by ID
- Update skill
- Delete skill
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.skill_list import (
    SkillListCreate,
    SkillListUpdate,
    SkillListResponse,
    SkillListSummary,
    SkillListListResponse,
    SkillStatisticsResponse
)
from services.skill_list_service import SkillListService
from core.deps import get_current_active_user, get_optional_user
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
    search: str | None = Query(None, description="Fuzzy search by skill name"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    """List all skills with optional filtering.

    Multiple filters are combined using AND logic:
    - category: Exact match
    - author: Exact match on created_by field
    - search: Fuzzy match on skill name (case-insensitive)
    - tags: Matches ANY tag within the comma-separated list

    Example: ?category=data&tags=python,ai&search=weather returns skills in 'data' category
    that have either 'python' OR 'ai' tags AND name contains 'weather'.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        category: Optional category filter
        tags: Optional comma-separated tags filter (matches ANY tag)
        author: Optional creator username filter (maps to created_by)
        search: Optional fuzzy search term for skill name
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        Paginated list of skill summaries (without content field)
    """
    skip = (page - 1) * size

    # For unauthenticated users, only show public skills
    if current_user is None:
        if tags:
            # Append "public" to existing tags filter
            tags = f"{tags},public"
        else:
            tags = "public"

    # Use combined filters (AND logic between filters, OR within tags)
    skills, total = SkillListService.list_with_filters(
        db, skip, size, category, tags, author, search
    )

    return SkillListListResponse(
        items=[SkillListSummary.model_validate(s) for s in skills],
        total=total,
        page=page,
        size=size
    )


@router.get("/stats/", response_model=SkillStatisticsResponse)
async def get_skill_statistics(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    """Get skill statistics including totals, published, drafts, and active user count.

    Args:
        db: Database session
        current_user: Authenticated user (optional, for logging/audit purposes)

    Returns:
        Skill statistics including:
        - total_skills: Total number of skills
        - published_skills: Skills with 'published' tag
        - draft_skills: Skills without 'published' tag (total - published)
        - new_skills_last_7days: Skills created in the last 7 days
        - active_users: Number of active users (is_active=True)
    """
    stats = SkillListService.get_statistics(db)
    return SkillStatisticsResponse(**stats)


@router.get("/{skill_id}/", response_model=SkillListResponse)
async def get_skill(
    skill_id: str,
    install: bool = Query(False, description="If true, return only skill.content as plain text for installation"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    """Get a specific skill by ID.

    Args:
        skill_id: Skill UUID or name
        install: If true, returns only skill.content as plain text
        db: Database session
        current_user: Authenticated user (optional)

    Returns:
        Skill response (JSON) or skill.content as plain text

    Raises:
        HTTPException 404: If skill is not found or access is denied
    """
    # Get skill by ID or name
    if len(skill_id) == 36:
        skill = SkillListService.get_by_id(db, skill_id)
    else:
        skill = SkillListService.get_by_name(db, skill_id)

    # Check if skill exists
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id/name '{skill_id}' not found"
        )

    # For unauthenticated users, only allow access to public skills
    if current_user is None:
        if not skill.tags or "public" not in skill.tags:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found or access denied. Public skills only for unauthenticated users."
            )

    # If install=true, return only content as plain text
    if install:
        return PlainTextResponse(content=skill.content or "", media_type="text/plain; charset=utf-8")

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
