from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, JSON, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime
import enum


class AccessMode(enum.Enum):
    """Enumeration of access control modes."""
    ANY = "any"  # Public access, no authentication required
    RBAC = "rbac"  # Role-based access control, requires authentication + permissions


class AuditResult(enum.Enum):
    """Enumeration of audit log results."""
    ALLOWED = "allowed"
    DENIED = "denied"


class ACLRule(Base):
    """ACLRule model representing access control rules for resources.

    Rules define how resources can be accessed, with support for public access
    or role-based access control with conditional constraints.
    """
    __tablename__ = "acl_rules"
    __table_args__ = (
        Index('ix_acl_rule_resource_id', 'resource_id'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String, nullable=False, index=True)
    resource_name = Column(String, nullable=False)
    access_mode = Column(Enum(AccessMode), nullable=False, default=AccessMode.RBAC)
    conditions = Column(JSON)  # Conditional constraints: rate limits, IP whitelist, time windows, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    role_bindings = relationship("ACLRuleRole", back_populates="acl_rule", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="acl_rule")


class ACLRuleRole(Base):
    """ACLRuleRole model representing role-based permissions for ACL rules.

    This junction table defines which roles have what permissions on a resource
    when RBAC mode is enabled.
    """
    __tablename__ = "acl_rule_roles"
    __table_args__ = (
        Index('ix_acl_rule_role_role_id', 'role_id'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acl_rule_id = Column(String(36), ForeignKey('acl_rules.id'), nullable=False)
    role_id = Column(String(36), ForeignKey('roles.id'), nullable=False)
    permissions = Column(JSON)  # List of permissions: ["read", "write", "execute"]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    acl_rule = relationship("ACLRule", back_populates="role_bindings")


class AuditLog(Base):
    """AuditLog model for tracking access control decisions.

    Maintains a comprehensive audit trail of all access attempts and decisions
    for security monitoring and compliance.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('ix_audit_log_timestamp', 'timestamp'),
        Index('ix_audit_log_user_id', 'user_id'),
        Index('ix_audit_log_resource_id', 'resource_id'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(String)  # Nullable for anonymous access attempts
    username = Column(String)  # Nullable for anonymous access attempts
    resource_id = Column(String, nullable=False)
    acl_rule_id = Column(String(36), ForeignKey('acl_rules.id'))
    access_mode = Column(Enum(AccessMode), nullable=False)
    result = Column(Enum(AuditResult), nullable=False)
    ip_address = Column(String)
    request_id = Column(String)  # For tracing requests through the system
    details = Column(JSON)  # Additional context about the access attempt

    # Relationships
    acl_rule = relationship("ACLRule", back_populates="audit_logs")
