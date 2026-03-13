"""System Audit Log model for comprehensive system-wide audit logging.

This model tracks all system actions including API requests, user actions,
and administrative operations for security monitoring and compliance.
Note: This is separate from ACL-specific audit logs in models.acl.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base
import uuid
from datetime import timezone, datetime
from typing import Optional


class SystemAuditLog(Base):
    """Comprehensive audit log for all system actions.

    Tracks user actions, API requests, and system events for security
    monitoring, compliance, and debugging purposes.
    """
    __tablename__ = "system_audit_logs"
    __table_args__ = (
        Index('ix_system_audit_logs_user_id', 'user_id'),
        Index('ix_system_audit_logs_action', 'action'),
        Index('ix_system_audit_logs_created_at', 'created_at'),
        Index('ix_system_audit_logs_resource_type', 'resource_type'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User")

    @hybrid_property
    def username(self) -> Optional[str]:
        """Get the username of the user who performed the action.

        Returns:
            Username if user exists, None otherwise
        """
        # Access the username through the relationship
        # Note: This requires the user relationship to be loaded
        # For better performance, use joinedload when querying
        if self.user:
            return self.user.username
        return None

    def __repr__(self):
        return f"<SystemAuditLog(id={self.id}, action={self.action}, status={self.status})>"
