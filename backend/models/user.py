from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime

# Many-to-many junction tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
    """User model representing application users."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    """Role model representing user roles with associated permissions."""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Permission(Base):
    """Permission model representing fine-grained access control permissions."""
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    description = Column(String)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class RefreshToken(Base):
    """RefreshToken model for storing JWT refresh tokens."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index('ix_refresh_token_user_id', 'user_id'),
        Index('ix_refresh_token_expires_at', 'expires_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_hash = Column(String, nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="refresh_tokens")
