"""Pydantic schemas for mtoken management API.

This module defines the request/response schemas used by the mtoken API endpoints,
including base models for create, update, and response operations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Base Schema
class MTokenBase(BaseModel):
    """Base schema for mtoken data."""
    app_name: str = Field(..., min_length=1, max_length=255, description="应用名称 (如 GitHub, OpenAI)")
    key_name: str = Field(..., min_length=1, max_length=255, description="密钥名称 (如 API Key, Access Token)")
    value: str = Field(..., min_length=1, max_length=10000, description="密钥值")
    desc: Optional[str] = Field(None, max_length=10000, description="描述信息")


# Create Schema
class MTokenCreate(MTokenBase):
    """Schema for creating a new mtoken."""
    pass


# Update Schema
class MTokenUpdate(BaseModel):
    """Schema for updating an existing mtoken."""
    app_name: Optional[str] = Field(None, min_length=1, max_length=255)
    key_name: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[str] = Field(None, min_length=1, max_length=10000)
    desc: Optional[str] = Field(None, max_length=10000)


# Response Schema
class MTokenResponse(MTokenBase):
    """Schema for mtoken response."""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List Response Schema (paginated)
class MTokenListResponse(BaseModel):
    """Schema for paginated mtoken list response."""
    items: list[MTokenResponse]
    total: int
    page: int
    size: int
