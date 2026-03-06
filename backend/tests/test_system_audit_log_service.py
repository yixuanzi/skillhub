"""Unit tests for System Audit Log Service.

This test suite covers:
- Creating audit log entries
- Listing audit logs with filters
- Getting audit log by ID
- Filter by action, resource type, user ID, status
- Filter by date range
- Pagination
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from models.user import User
from models.system_audit_log import SystemAuditLog
from schemas.audit_log import AuditAction
from services.system_audit_log_service import SystemAuditLogService


class TestSystemAuditLogCreate:
    """Test suite for audit log creation."""

    def test_log_action_success(self, db: Session, test_user: User):
        """Test logging a successful action."""
        log = SystemAuditLogService.log_action(
            db,
            user_id=str(test_user.id),
            action=AuditAction.LOGIN,
            resource_type="user",
            resource_id=str(test_user.id),
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            status="success"
        )

        assert log.id is not None
        assert log.user_id == str(test_user.id)
        assert log.action == AuditAction.LOGIN
        assert log.resource_type == "user"
        assert log.ip_address == "192.168.1.1"
        assert log.status == "success"
        assert log.error_message is None

    def test_log_action_failure(self, db: Session, test_user: User):
        """Test logging a failed action."""
        log = SystemAuditLogService.log_action(
            db,
            user_id=str(test_user.id),
            action=AuditAction.LOGIN_FAILED,
            ip_address="192.168.1.1",
            status="failure",
            error_message="Invalid password"
        )

        assert log.status == "failure"
        assert log.error_message == "Invalid password"

    def test_log_action_anonymous(self, db: Session):
        """Test logging action without user (anonymous)."""
        log = SystemAuditLogService.log_action(
            db,
            user_id=None,
            action=AuditAction.RESOURCE_READ,
            resource_type="resource",
            resource_id="res_123",
            ip_address="10.0.0.1",
            status="success"
        )

        assert log.user_id is None
        assert log.action == AuditAction.RESOURCE_READ

    def test_log_action_with_details(self, db: Session, test_user: User):
        """Test logging action with additional details."""
        details = {
            "method": "POST",
            "path": "/api/v1/skills",
            "duration_ms": 150
        }

        log = SystemAuditLogService.log_action(
            db,
            user_id=str(test_user.id),
            action=AuditAction.SKILL_CALL,
            resource_type="skill",
            resource_id="skill_123",
            details=details,
            status="success"
        )

        assert log.details == details

    def test_log_action_creates_timestamp(self, db: Session, test_user: User):
        """Test that logging creates appropriate timestamp."""
        before = datetime.now(timezone.utc)

        log = SystemAuditLogService.log_action(
            db,
            user_id=str(test_user.id),
            action=AuditAction.LOGOUT,
            status="success"
        )

        after = datetime.now(timezone.utc)

        assert log.created_at is not None
        # Convert to naive for comparison (SQLite doesn't preserve timezone)
        before_naive = before.replace(tzinfo=None)
        after_naive = after.replace(tzinfo=None)
        log_naive = log.created_at.replace(tzinfo=None) if log.created_at.tzinfo else log.created_at
        assert before_naive <= log_naive <= after_naive


class TestSystemAuditLogList:
    """Test suite for listing audit logs."""

    def test_list_logs_empty(self, db: Session):
        """Test listing when no logs exist."""
        logs, total = SystemAuditLogService.list_logs(db)
        assert total == 0
        assert len(logs) == 0

    def test_list_logs_with_data(self, db: Session, test_user: User):
        """Test listing returns all logs."""
        # Create multiple logs
        for i in range(3):
            SystemAuditLogService.log_action(
                db,
                user_id=str(test_user.id),
                action=AuditAction.RESOURCE_READ,
                resource_type="resource",
                resource_id=f"res_{i}",
                status="success"
            )

        logs, total = SystemAuditLogService.list_logs(db)
        assert total == 3
        assert len(logs) == 3

    def test_list_logs_ordering(self, db: Session, test_user: User):
        """Test logs are ordered by created_at descending (newest first)."""
        # Create logs with delays
        log1 = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        log2 = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        logs, _ = SystemAuditLogService.list_logs(db)
        assert logs[0].id == log2.id  # Newest first
        assert logs[1].id == log1.id

    def test_list_logs_pagination(self, db: Session, test_user: User):
        """Test pagination of audit logs."""
        # Create 5 logs
        for i in range(5):
            SystemAuditLogService.log_action(
                db,
                user_id=str(test_user.id),
                action=AuditAction.RESOURCE_READ,
                status="success"
            )

        logs, total = SystemAuditLogService.list_logs(db, skip=0, limit=3)
        assert total == 5
        assert len(logs) == 3

        logs, total = SystemAuditLogService.list_logs(db, skip=3, limit=3)
        assert total == 5
        assert len(logs) == 2


class TestSystemAuditLogFilterByAction:
    """Test suite for filtering audit logs by action."""

    def test_filter_by_action(self, db: Session, test_user: User):
        """Test filtering logs by action type."""
        SystemAuditLogService.log_action(db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success")
        SystemAuditLogService.log_action(db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success")
        SystemAuditLogService.log_action(db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success")

        logs, total = SystemAuditLogService.list_logs(db, action=AuditAction.LOGIN)
        assert total == 2
        assert all(log.action == AuditAction.LOGIN for log in logs)

        logs, total = SystemAuditLogService.list_logs(db, action=AuditAction.LOGOUT)
        assert total == 1


class TestSystemAuditLogFilterByResourceType:
    """Test suite for filtering audit logs by resource type."""

    def test_filter_by_resource_type(self, db: Session, test_user: User):
        """Test filtering logs by resource type."""
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.RESOURCE_CREATE,
            resource_type="resource", status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.SKILL_CALL,
            resource_type="skill", status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.RESOURCE_READ,
            resource_type="resource", status="success"
        )

        logs, total = SystemAuditLogService.list_logs(db, resource_type="resource")
        assert total == 2

        logs, total = SystemAuditLogService.list_logs(db, resource_type="skill")
        assert total == 1


class TestSystemAuditLogFilterByUserId:
    """Test suite for filtering audit logs by user ID."""

    def test_filter_by_user_id(self, db: Session, test_user: User, admin_user: User):
        """Test filtering logs by user ID."""
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(admin_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        logs, total = SystemAuditLogService.list_logs(db, user_id=str(test_user.id))
        assert total == 2
        assert all(log.user_id == str(test_user.id) for log in logs)


class TestSystemAuditLogFilterByStatus:
    """Test suite for filtering audit logs by status."""

    def test_filter_by_status_success(self, db: Session, test_user: User):
        """Test filtering successful logs."""
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN_FAILED, status="failure"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        logs, total = SystemAuditLogService.list_logs(db, status="success")
        assert total == 2
        assert all(log.status == "success" for log in logs)

        logs, total = SystemAuditLogService.list_logs(db, status="failure")
        assert total == 1
        assert logs[0].status == "failure"


class TestSystemAuditLogFilterByDateRange:
    """Test suite for filtering audit logs by date range."""

    def test_filter_by_start_date(self, db: Session, test_user: User):
        """Test filtering logs by start date."""
        # Create an old log
        old_log = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )

        # Manually set old timestamp
        old_time = datetime.now(timezone.utc) - timedelta(days=7)
        old_log.created_at = old_time
        db.commit()

        # Create new log
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        # Filter for recent logs only
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        logs, total = SystemAuditLogService.list_logs(db, start_date=start_date)
        assert total == 1
        assert logs[0].action == AuditAction.LOGOUT

    def test_filter_by_end_date(self, db: Session, test_user: User):
        """Test filtering logs by end date."""
        # Create a new log
        new_log = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        # Manually set future timestamp
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        new_log.created_at = future_time
        db.commit()

        # Create old log
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )

        # Filter for old logs only
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        logs, total = SystemAuditLogService.list_logs(db, end_date=end_date)
        assert total == 1
        assert logs[0].action == AuditAction.LOGIN

    def test_filter_by_date_range(self, db: Session, test_user: User):
        """Test filtering logs within a date range."""
        # Create three logs with different timestamps
        log1 = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        log1.created_at = datetime.now(timezone.utc) - timedelta(days=5)
        db.commit()

        log2 = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )
        log2.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        db.commit()

        log3 = SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        log3.created_at = datetime.now(timezone.utc) + timedelta(days=5)
        db.commit()

        # Filter for logs within last 3 days
        start_date = datetime.now(timezone.utc) - timedelta(days=3)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)

        logs, total = SystemAuditLogService.list_logs(db, start_date=start_date, end_date=end_date)
        assert total == 1
        assert logs[0].action == AuditAction.LOGOUT


class TestSystemAuditLogGetById:
    """Test suite for getting audit log by ID."""

    def test_get_by_id_found(self, db: Session, test_user: User):
        """Test getting existing log by ID."""
        created_log = SystemAuditLogService.log_action(
            db,
            user_id=str(test_user.id),
            action=AuditAction.LOGIN,
            status="success"
        )

        retrieved_log = SystemAuditLogService.get_by_id(db, created_log.id)

        assert retrieved_log is not None
        assert retrieved_log.id == created_log.id
        assert retrieved_log.action == AuditAction.LOGIN

    def test_get_by_id_not_found(self, db: Session):
        """Test getting non-existent log returns None."""
        log = SystemAuditLogService.get_by_id(db, "non-existent-id")
        assert log is None


class TestSystemAuditLogMultipleFilters:
    """Test suite for combining multiple filters."""

    def test_filter_by_action_and_status(self, db: Session, test_user: User):
        """Test filtering by both action and status."""
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN_FAILED, status="failure"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )

        # Filter for successful logins only
        logs, total = SystemAuditLogService.list_logs(
            db, action=AuditAction.LOGIN, status="success"
        )
        assert total == 2

        # Filter for failed logins
        logs, total = SystemAuditLogService.list_logs(
            db, action=AuditAction.LOGIN_FAILED, status="failure"
        )
        assert total == 1

    def test_filter_by_user_and_action(self, db: Session, test_user: User, admin_user: User):
        """Test filtering by both user and action."""
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(admin_user.id), action=AuditAction.LOGIN, status="success"
        )
        SystemAuditLogService.log_action(
            db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
        )

        logs, total = SystemAuditLogService.list_logs(
            db, user_id=str(test_user.id), action=AuditAction.LOGIN
        )
        assert total == 1

    def test_filter_with_pagination(self, db: Session, test_user: User):
        """Test combining filters with pagination."""
        # Create mixed logs
        for i in range(5):
            SystemAuditLogService.log_action(
                db, user_id=str(test_user.id), action=AuditAction.LOGIN, status="success"
            )
        for i in range(3):
            SystemAuditLogService.log_action(
                db, user_id=str(test_user.id), action=AuditAction.LOGOUT, status="success"
            )

        # Get first page of logins
        logs, total = SystemAuditLogService.list_logs(
            db, action=AuditAction.LOGIN, skip=0, limit=2
        )
        assert total == 5
        assert len(logs) == 2
