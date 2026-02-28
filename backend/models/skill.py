from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import timezone, datetime
import enum


class SkillType(enum.Enum):
    """Enumeration of skill types."""
    BUSINESS_LOGIC = "business_logic"
    API_PROXY = "api_proxy"
    AI_LLM = "ai_llm"
    DATA_PROCESSING = "data_processing"


class SkillRuntime(enum.Enum):
    """Enumeration of supported runtimes."""
    NODEJS = "nodejs"
    PYTHON = "python"
    GO = "go"


class SkillStatus(enum.Enum):
    """Enumeration of skill version statuses."""
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"
    PUBLISHED = "published"


class Skill(Base):
    """Skill model representing AI agent skills.

    Skills are reusable units of functionality that can be built, published,
    and called through the platform. Each skill can have multiple versions.
    """
    __tablename__ = "skills"
    __table_args__ = (
        Index('ix_skill_created_by', 'created_by'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    skill_type = Column(Enum(SkillType), nullable=False)
    runtime = Column(Enum(SkillRuntime), nullable=False)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")


class SkillVersion(Base):
    """SkillVersion model representing specific versions of skills.

    Each version contains build artifacts, status information, and metadata
    about a specific build of a skill.
    """
    __tablename__ = "skill_versions"
    __table_args__ = (
        Index('ix_skill_version_skill_id', 'skill_id'),
        Index('ix_skill_version_status', 'status'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_id = Column(String(36), ForeignKey('skills.id'), nullable=False)
    version = Column(String, nullable=False)
    status = Column(Enum(SkillStatus), default=SkillStatus.BUILDING)
    artifact_path = Column(String)  # Path to build artifact (Docker image or ZIP)
    build_log = Column(Text)  # Build output log
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    skill = relationship("Skill", back_populates="versions")
