"""MToken model for managing third-party token storage.

This module defines the MToken model which represents stored third-party API tokens
for integration with external services like GitHub, OpenAI, etc.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime


class MToken(Base):
    """MToken model for managing third-party token storage.

    MTokens represent externally sourced API tokens and credentials that users
    want to store securely for use with integrations and automations.
    """
    __tablename__ = "mtoken"

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic Fields
    app_name = Column(String(255), nullable=False, index=True)  # 应用名称 (如 "GitHub", "OpenAI")
    key_name = Column(String(255), nullable=False, index=True)  # 密钥名称 (如 "API Key", "Access Token")
    value = Column(Text, nullable=False)  # 密钥值 (敏感信息)
    desc = Column(Text, nullable=True)  # 描述信息

    # User Reference
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User", backref="mtokens")

    # Indexes
    __table_args__ = (
        Index('ix_mtoken_app_key', 'app_name', 'key_name'),
        Index('ix_mtoken_created_by', 'created_by'),
    )
