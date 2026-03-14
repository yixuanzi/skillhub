from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserResponse(UserBase):
    id: str  # UUID stored as string in SQLite
    is_active: bool
    created_at: datetime
    roles: List['RoleWithPermissions'] = []

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str  # Last 32 chars
    refresh_token: str  # Last 32 chars
    #tmpkey: str  # 32字符的临时密钥，可用于API认证
    token_type: str = "bearer"
    expires_in: int  # Seconds

class RefreshTokenRequest(BaseModel):
    refresh_token: str  # Last 32 chars

class RefreshTokenResponse(BaseModel):
    access_token: str  # Last 32 chars
    token_type: str = "bearer"
    expires_in: int

class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: str  # UUID stored as string in SQLite
    created_at: datetime

    class Config:
        from_attributes = True

class PermissionResponse(BaseModel):
    id: str  # UUID stored as string in SQLite
    resource: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class RoleWithPermissions(RoleResponse):
    permissions: List[PermissionResponse] = []

class UserUpdate(BaseModel):
    """Schema for updating user profile (username and/or email)."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None

class PasswordChange(BaseModel):
    """Schema for changing user password."""
    old_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 characters)")
