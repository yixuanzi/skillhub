"""Pydantic schemas for API Key operations."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class APIKeyResponse(BaseModel):
    """Schema for API key response (excludes full key)."""
    id: str
    name: str
    key_prefix: str
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes full key)."""
    key: str = Field(..., description="Full API key - only returned once")
    api_key: APIKeyResponse


class APIKeyListResponse(BaseModel):
    """Schema for API key list response (paginated)."""
    items: List[APIKeyResponse]
    total: int


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
