"""System Audit Log service for audit log operations.

This module provides the business logic layer for system audit logging,
including creating logs and querying with filters.
"""
from sqlalchemy.orm import Session
from typing import Optional, Any, List
from datetime import datetime

from models.system_audit_log import SystemAuditLog
from models.user import User


class SystemAuditLogService:
    """Service class for system audit log operations."""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> SystemAuditLog:
        """Log a system audit action.

        Args:
            db: Database session
            user_id: ID of the user performing the action (None for anonymous)
            action: Action being performed
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            details: Additional details about the action
            ip_address: IP address of the request
            user_agent: User agent string
            status: Status of the action (success/failure)
            error_message: Error message if status is failure

        Returns:
            Created SystemAuditLog object
        """
        log = SystemAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[SystemAuditLog], int]:
        """List audit logs with filters.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            action: Filter by action
            resource_type: Filter by resource type
            user_id: Filter by user ID
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Tuple of (list of logs, total count)
        """
        query = db.query(SystemAuditLog)

        if action:
            query = query.filter(SystemAuditLog.action == action)
        if resource_type:
            query = query.filter(SystemAuditLog.resource_type == resource_type)
        if user_id:
            query = query.filter(SystemAuditLog.user_id == user_id)
        if status:
            query = query.filter(SystemAuditLog.status == status)
        if start_date:
            query = query.filter(SystemAuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemAuditLog.created_at <= end_date)

        total = query.count()
        logs = query.order_by(
            SystemAuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()

        return logs, total

    @staticmethod
    def get_by_id(db: Session, log_id: str) -> Optional[SystemAuditLog]:
        """Get audit log by ID.

        Args:
            db: Database session
            log_id: Log UUID

        Returns:
            SystemAuditLog object or None
        """
        return db.query(SystemAuditLog).filter(
            SystemAuditLog.id == log_id
        ).first()
