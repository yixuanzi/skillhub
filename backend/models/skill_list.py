"""SkillList model for managing AI agent skills in the skill market.

This module defines the SkillList model which represents skills in the skill market,
including metadata, documentation, categorization, and version tracking.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime


class SkillList(Base):
    """SkillList model for managing AI agent skills in the skill market.

    Skills in the market represent reusable AI agent capabilities with documentation,
    categorization, and version tracking.
    """
    __tablename__ = "skill_list"

    # Primary Key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic Fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Markdown documentation
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Additional Features
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    version = Column(String(50), default="1.0.0")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = relationship("User", backref="skill_lists")
