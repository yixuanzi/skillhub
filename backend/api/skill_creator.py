"""Skill Creator API endpoints for generating skill content.

This module provides FastAPI endpoints for generating skill content based on:
- Resources (base mode): Generate skill from resource specifications
- Existing Skills (sop mode): Generate SOP skill from multiple existing skills
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from database import get_db
from schemas.skill_creator import SkillCreatorRequest, SkillCreatorResponse
from services.skill_creator_service import SkillCreatorService
from core.deps import get_current_active_user
from models.user import User
from core.exceptions import ValidationException, NotFoundException

router = APIRouter(prefix="/skill-creator", tags=["Skill Creator"])


@router.post("/", response_model=SkillCreatorResponse, status_code=status.HTTP_200_OK)
async def generate_skill_content(
    request: SkillCreatorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate skill content based on resources or existing skills.

    ## Base Mode
    Generates markdown content from a list of resources. Each resource contributes:
    - name, desc, type, url
    - method (if available for third-party resources)
    - tools (for MCP type resources - fetches available tools from server)
    - document (api_description)

    Example request:
    ```json
    {
        "type": "base",
        "resource_id_list": ["resource-id-1", "resource-id-2"]
    }
    ```

    ## SOP Mode
    Generates markdown content from existing skills with custom user requirements.

    Example request:
    ```json
    {
        "type": "sop",
        "skill_id_list": ["skill-id-1", "skill-id-2"],
        "userinput": "Create a customer support workflow that handles..."
    }
    ```

    Args:
        request: Skill creator request with type and references
        db: Database session
        current_user: Authenticated user

    Returns:
        Generated markdown content

    Raises:
        HTTPException 400: If validation fails
        HTTPException 403: If access denied to referenced resources/skills
        HTTPException 404: If referenced resources/skills not found
    """
    try:
        content = await SkillCreatorService.generate_content(db, request, user=current_user)
        return SkillCreatorResponse(content=content)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        # Check if it's an access permission error
        if "permission" in str(e).lower() or "access" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
