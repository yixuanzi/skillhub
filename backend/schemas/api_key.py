"""Pydantic schemas for API Key operations."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class APIScope:
    """API key permission scopes.

    Scopes define what operations an API key can perform.
    Each scope follows the pattern: resource:action
    """
    RESOURCES_READ = "resources:read"
    RESOURCES_WRITE = "resources:write"
    SKILLS_READ = "skills:read"
    SKILLS_CALL = "skills:call"
    SKILLS_WRITE = "skills:write"
    ACL_READ = "acl:read"
    ACL_WRITE = "acl:write"
    TOKENS_READ = "tokens:read"
    TOKENS_WRITE = "tokens:write"
    AUDIT_READ = "audit:read"
    USERS_READ = "users:read"

    @classmethod
    def all_scopes(cls) -> List[str]:
        """Return list of all valid scopes."""
        return [
            cls.RESOURCES_READ, cls.RESOURCES_WRITE,
            cls.SKILLS_READ, cls.SKILLS_CALL, cls.SKILLS_WRITE,
            cls.ACL_READ, cls.ACL_WRITE,
            cls.TOKENS_READ, cls.TOKENS_WRITE,
            cls.AUDIT_READ,
            cls.USERS_READ,
        ]

    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> List[str]:
        """Validate scopes and raise ValueError if any are invalid."""
        valid_scopes = cls.all_scopes()
        invalid_scopes = set(scopes) - set(valid_scopes)
        if invalid_scopes:
            raise ValueError(f"Invalid scopes: {', '.join(invalid_scopes)}")
        return scopes


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the API key")
    scopes: List[str] = Field(..., min_length=1, description="List of permission scopes")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")

    def validate_scopes(self) -> None:
        """Validate that all scopes are valid."""
        APIScope.validate_scopes(self.scopes)


class APIKeyResponse(BaseModel):
    """Schema for API key response (excludes full key)."""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
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
    scopes: Optional[List[str]] = Field(None, min_length=1)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

    def validate_scopes(self) -> None:
        """Validate scopes if provided."""
        if self.scopes is not None:
            APIScope.validate_scopes(self.scopes)
