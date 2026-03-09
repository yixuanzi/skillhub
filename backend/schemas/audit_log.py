"""Pydantic schemas for System Audit Log operations."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, List
from enum import Enum


class AuditAction(str, Enum):
    """Enumeration of all auditable system actions."""
    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"

    # Resource actions
    RESOURCE_CREATE = "resource.create"
    RESOURCE_UPDATE = "resource.update"
    RESOURCE_DELETE = "resource.delete"
    RESOURCE_READ = "resource.read"

    # Skill actions
    SKILL_CALL = "skill.call"
    SKILL_CREATE = "skill.create"
    SKILL_UPDATE = "skill.update"
    SKILL_DELETE = "skill.delete"

    # ACL actions
    ACL_CREATE = "acl.create"
    ACL_UPDATE = "acl.update"
    ACL_DELETE = "acl.delete"
    PERMISSION_CHECK = "acl.check_permission"

    # API Key actions
    API_KEY_CREATE = "api_key.create"
    API_KEY_UPDATE = "api_key.update"
    API_KEY_DELETE = "api_key.delete"
    API_KEY_ROTATE = "api_key.rotate"
    API_KEY_USE = "api_key.use"

    # User actions
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    ROLE_ASSIGN = "user.role_assign"

    # Token actions
    TOKEN_CREATE = "token.create"
    TOKEN_UPDATE = "token.update"
    TOKEN_DELETE = "token.delete"

    # Gateway actions
    GATEWAY_REQUEST = "gateway.request"
    GATEWAY_PROXY = "gateway.proxy"


class SystemAuditLogResponse(BaseModel):
    """Schema for system audit log response."""
    id: str
    user_id: Optional[str]
    username: Optional[str]  # Username of the user who performed the action
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SystemAuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""
    items: List[SystemAuditLogResponse]
    total: int
    page: int
    size: int


class SystemAuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    action: Optional[str] = None
    resource_type: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
