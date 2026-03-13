"""Pydantic schemas for skill market management."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillListBase(BaseModel):
    """Base schema for skill list with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Skill list name")
    description: Optional[str] = Field(
        None, max_length=10000, description="Detailed description of the skill list"
    )
    content: str = Field(
        None, max_length=100000, description="Content of the skill list"
    )
    created_by: Optional[str] = None 
    # Field(
    #     ...,
    #     min_length=1,
    #     max_length=255,
    #     description="User ID who created the skill list",
    # )
    category: Optional[str] = Field(
        None, max_length=100, description="Category of the skill list"
    )
    tags: Optional[str] = Field(
        None, max_length=500, description="Comma-separated tags"
    )
    version: str = Field(
        default="1.0.0", max_length=50, description="Version of the skill list"
    )


class SkillListCreate(SkillListBase):
    """Schema for creating a new skill list."""

    pass


class SkillListUpdate(BaseModel):
    """Schema for updating a skill list (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    content: Optional[str] = Field(None, max_length=100000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    version: Optional[str] = Field(None, max_length=50)


class SkillListResponse(SkillListBase):
    """Schema for skill list response with all fields including system-generated."""

    id: str = Field(..., description="Unique identifier for the skill list")
    created_at: datetime = Field(..., description="Timestamp when the skill list was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when the skill list was last updated"
    )

    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""

        from_attributes = True


class SkillListSummary(BaseModel):
    """Schema for skill list summary without content field (used in list responses)."""

    id: str = Field(..., description="Unique identifier for the skill list")
    name: str = Field(..., description="Skill list name")
    description: Optional[str] = Field(None, description="Detailed description of the skill list")
    created_by: Optional[str] = None
    category: Optional[str] = Field(None, description="Category of the skill list")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    version: str = Field(default="1.0.0", description="Version of the skill list")
    created_at: datetime = Field(..., description="Timestamp when the skill list was created")
    updated_at: datetime = Field(..., description="Timestamp when the skill list was last updated")

    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""

        from_attributes = True


class SkillListListResponse(BaseModel):
    """Schema for paginated list of skill lists."""

    items: list[SkillListSummary] = Field(
        ..., description="List of skill list summaries for the current page (without content)"
    )
    total: int = Field(..., description="Total number of skill lists")
    page: int = Field(..., description="Current page number (1-based)")
    size: int = Field(..., description="Number of items per page")


class SkillStatisticsResponse(BaseModel):
    """Schema for skill statistics response."""

    total_skills: int = Field(..., description="Total number of skills")
    published_skills: int = Field(..., description="Number of published skills (with 'published' tag)")
    draft_skills: int = Field(..., description="Number of draft skills (total - published)")
    new_skills_last_7days: int = Field(..., description="Number of skills created in the last 7 days")
    active_users: int = Field(..., description="Number of active users (is_active=True)")
