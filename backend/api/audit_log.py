"""System Audit Log endpoints for audit log querying operations.

This module provides FastAPI endpoints for retrieving system audit logs,
including filtering by action, resource type, user, and date range.

Security Policy:
- Admin users (admin, super_admin) can view all audit logs
- Regular users can only view their own audit logs
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

# Admin role names
ADMIN_ROLES = {"admin", "super_admin"}


def _is_admin_user(user: User) -> bool:
    """Check if user has admin or super_admin role.

    Args:
        user: User object with roles relationship

    Returns:
        True if user has admin or super_admin role
    """
    if not user or not user.roles:
        return False
    user_role_names = {role.name for role in user.roles}
    return bool(user_role_names & ADMIN_ROLES)


@router.get("/", response_model=SystemAuditLogListResponse)
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
    """List audit logs with filters.

    - Admin users can view all audit logs with optional filters
    - Regular users can only view their own audit logs

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (max 100)
        action: Filter by action type (admin only)
        resource_type: Filter by resource type (admin only)
        user_id: Filter by user ID (admin only)
        status_filter: Filter by status (success/failure)
        start_date: Filter by start date
        end_date: Filter by end date
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of audit logs

    Raises:
        HTTPException 400: If regular user tries to use admin-only filters
    """
    is_admin = _is_admin_user(current_user)

    # Non-admin users can only view their own logs
    if not is_admin:
        # Non-admin users cannot use filters that would let them see other users' logs
        if user_id and user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only view your own audit logs"
            )
        # Force filter to current user's logs
        user_id = str(current_user.id)

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


@router.get("/{log_id}/", response_model=SystemAuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit log details by ID.

    - Admin users can view any audit log
    - Regular users can only view their own audit logs

    Args:
        log_id: Audit log UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Audit log details

    Raises:
        HTTPException 403: If user is not the owner and not an admin
        HTTPException 404: If log not found
    """
    is_admin = _is_admin_user(current_user)

    log = SystemAuditLogService.get_by_id_for_user(db, log_id, str(current_user.id) if not is_admin else None)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with id '{log_id}' not found"
        )

    return SystemAuditLogResponse.model_validate(log)
