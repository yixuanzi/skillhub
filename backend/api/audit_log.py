"""System Audit Log endpoints for audit log querying operations.

This module provides FastAPI endpoints for retrieving system audit logs,
including filtering by action, resource type, user, and date range.
Access to audit logs is restricted to admin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from schemas.audit_log import SystemAuditLogResponse, SystemAuditLogListResponse
from services.system_audit_log_service import SystemAuditLogService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def _check_admin_access(user: User) -> None:
    """Check if user has admin access.

    Args:
        user: Current user

    Raises:
        HTTPException 403: If user is not an admin
    """
    # Check if user has admin role
    admin_roles = {"admin", "superadmin", "super_admin"}
    is_admin = any(role.name in admin_roles for role in user.roles) if user.roles else False

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view audit logs"
        )


@router.get("", response_model=SystemAuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List audit logs with filters (admin only).

    Requires admin role to access.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        action: Filter by action type
        resource_type: Filter by resource type
        user_id: Filter by user ID
        status_filter: Filter by status (success/failure)
        start_date: Filter by start date
        end_date: Filter by end date
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of audit logs

    Raises:
        HTTPException 403: If user is not an admin
    """
    _check_admin_access(current_user)

    skip = (page - 1) * size
    logs, total = SystemAuditLogService.list_logs(
        db,
        skip=skip,
        limit=size,
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date
    )

    return SystemAuditLogListResponse(
        items=[SystemAuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size
    )


@router.get("/{log_id}", response_model=SystemAuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit log details by ID (admin only).

    Args:
        log_id: Audit log UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Audit log details

    Raises:
        HTTPException 403: If user is not an admin
        HTTPException 404: If log not found
    """
    _check_admin_access(current_user)

    log = SystemAuditLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with id '{log_id}' not found"
        )

    return SystemAuditLogResponse.model_validate(log)
