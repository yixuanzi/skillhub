"""Pydantic schemas for skill creator API.

This module defines the request/response schemas for the skill creator endpoint,
which generates skill content based on resources or existing skills.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class SkillCreatorType(str, Enum):
    """Skill creator type options."""

    BASE = "base"  # Generate skill content from resources
    SOP = "sop"    # Generate SOP skill from existing skills


class SkillCreatorRequest(BaseModel):
    """Schema for skill creator request."""

    type: SkillCreatorType = Field(
        ..., description="Creator type: base (from resources) or sop (from skills)"
    )
    resource_id_list: Optional[List[str]] = Field(
        None, description="List of resource IDs for base mode"
    )
    skill_id_list: Optional[List[str]] = Field(
        None, description="List of skill IDs for sop mode"
    )
    userinput: Optional[str] = Field(
        None,
        max_length=10000,
        description="User's detailed requirements for skill generation (required for sop mode, optional for base mode)"
    )

    @field_validator("userinput")
    @classmethod
    def validate_userinput_for_sop(cls, v, info):
        """Validate that userinput is provided for sop mode."""
        if info.data.get("type") == SkillCreatorType.SOP and not v:
            raise ValueError("userinput is required for sop mode")
        return v

    @field_validator("resource_id_list", "skill_id_list")
    @classmethod
    def validate_reference_lists(cls, v, info):
        """Validate that correct reference list is provided based on type."""
        creator_type = info.data.get("type")
        if creator_type == SkillCreatorType.BASE:
            if info.field_name == "skill_id_list" and v:
                raise ValueError("skill_id_list should not be provided for base mode")
            if info.field_name == "resource_id_list" and not v:
                raise ValueError("resource_id_list is required for base mode")
        elif creator_type == SkillCreatorType.SOP:
            if info.field_name == "resource_id_list" and v:
                raise ValueError("resource_id_list should not be provided for sop mode")
            if info.field_name == "skill_id_list" and not v:
                raise ValueError("skill_id_list is required for sop mode")
        return v


class SkillCreatorResponse(BaseModel):
    """Schema for skill creator response."""

    content: str = Field(..., description="Generated skill content in markdown format")
    context_conf: Optional[str] = Field(None, description="Contextual configuration for skill generation")
