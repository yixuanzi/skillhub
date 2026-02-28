"""Pydantic schemas for resource management API.

This module defines the request/response schemas used by the resource API endpoints,
including base models for create, update, and response operations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.resource import ResourceType


# 基础 Schema
class ResourceBase(BaseModel):
    """Base schema for resource data."""
    name: str = Field(..., min_length=1, max_length=255)
    desc: Optional[str] = None
    type: ResourceType
    url: Optional[str] = Field(None, max_length=2048)
    ext: Optional[dict] = None


# 创建 Schema
class ResourceCreate(ResourceBase):
    """Schema for creating a new resource."""
    pass


# 更新 Schema
class ResourceUpdate(BaseModel):
    """Schema for updating an existing resource."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    desc: Optional[str] = None
    type: Optional[ResourceType] = None
    url: Optional[str] = Field(None, max_length=2048)
    ext: Optional[dict] = None


# 响应 Schema
class ResourceResponse(ResourceBase):
    """Schema for resource response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 列表响应 Schema（分页）
class ResourceListResponse(BaseModel):
    """Schema for paginated resource list response."""
    items: list[ResourceResponse]
    total: int
    page: int
    size: int
