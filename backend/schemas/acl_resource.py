"""Pydantic schemas for resource ACL management.

This module defines the request/response schemas used by the resource ACL API endpoints,
including base models for create, update, and response operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.acl import AccessMode


# Permission enums
class PermissionAction(str):
    """Permission action types."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


# Role binding schemas
class RoleBindingCreate(BaseModel):
    """Schema for creating a role binding."""
    role_id: str = Field(..., description="Role ID")
    permissions: List[str] = Field(
        default=["read"],
        description="List of permissions (e.g., ['read', 'write'])"
    )


class RoleBindingResponse(BaseModel):
    """Schema for role binding response."""
    id: str
    role_id: str
    role_name: Optional[str] = None
    permissions: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Condition schemas
class ConditionSchema(BaseModel):
    """Base schema for ACL conditions."""
    users: Optional[List[str]] = Field(
        None,
        description="List of user IDs allowed to access"
    )
    roles: Optional[List[str]] = Field(
        None,
        description="List of role IDs allowed to access"
    )
    ip_whitelist: Optional[List[str]] = Field(
        None,
        description="List of allowed IP addresses/CIDR ranges"
    )
    rate_limit: Optional[Dict[str, int]] = Field(
        None,
        description="Rate limit configuration (e.g., {'requests': 100, 'window': 60})"
    )
    time_windows: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Time windows for access (e.g., [{'start': '09:00', 'end': '18:00'}])"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for custom conditions"
    )


# Base ACL rule schema
class ACLRuleBase(BaseModel):
    """Base schema for ACL rule data."""
    resource_id: str = Field(..., description="Resource ID to control access for")
    resource_name: str = Field(..., description="Resource name (for easier lookup)")
    access_mode: AccessMode = Field(
        default=AccessMode.RBAC,
        description="Access mode: 'any' (public) or 'rbac' (role-based)"
    )
    conditions: Optional[ConditionSchema] = Field(
        None,
        description="Conditional constraints (users, roles, IP whitelist, etc.)"
    )


# Create schema
class ACLRuleCreate(ACLRuleBase):
    """Schema for creating a new ACL rule."""
    role_bindings: Optional[List[RoleBindingCreate]] = Field(
        default=[],
        description="Role bindings (required for RBAC mode)"
    )


# Update schema
class ACLRuleUpdate(BaseModel):
    """Schema for updating an existing ACL rule."""
    access_mode: Optional[AccessMode] = None
    conditions: Optional[ConditionSchema] = None


# Response schema
class ACLRuleResponse(ACLRuleBase):
    """Schema for ACL rule response."""
    id: str
    conditions: Optional[Dict[str, Any]] = None
    created_at: datetime
    role_bindings: List[RoleBindingResponse] = []

    model_config = ConfigDict(from_attributes=True)


# List response schema (paginated)
class ACLRuleListResponse(BaseModel):
    """Schema for paginated ACL rule list response."""
    items: List[ACLRuleResponse]
    total: int
    page: int
    size: int


# Permission check schema
class PermissionCheckRequest(BaseModel):
    """Schema for checking user permissions."""
    user_id: str = Field(..., description="User ID to check")
    required_permission: str = Field(
        default="read",
        description="Required permission (read, write, delete, execute, admin)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context (IP address, timestamp, etc.)"
    )


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response."""
    allowed: bool
    reason: str
    access_mode: str
    matched_conditions: Optional[Dict[str, Any]] = None
