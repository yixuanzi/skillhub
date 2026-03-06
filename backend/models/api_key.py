from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime


class APIKey(Base):
    """User-scoped API key for authentication.

    API keys provide programmatic access to the SkillHub API.
    Each key is scoped to a specific user and has limited permissions
    based on configured scopes.
    """
    __tablename__ = "api_keys"
    __table_args__ = (
        Index('ix_api_keys_user_id', 'user_id'),
        Index('ix_api_keys_key_hash', 'key_hash'),
        Index('ix_api_keys_is_active', 'is_active'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)
    scopes = Column(JSON, nullable=False, default=list)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"
