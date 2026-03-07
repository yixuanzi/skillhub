"""Resource model for managing different types of system resources.

This module defines the Resource model which represents various system resources
including build resources, gateway resources, third-party resources, and MCP servers.
"""
from sqlalchemy import Column, String, Text, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base
import uuid
from datetime import timezone, datetime
import enum
import json


class ResourceType(str, enum.Enum):
    """Enumeration of resource types."""
    #BUILD = "build"      # 构建资源
    GATEWAY = "gateway"  # 网关资源
    THIRD = "third"      # 第三方资源
    MCP = "mcp"          # MCP (Model Context Protocol) 服务器资源


class Resource(Base):
    """Resource model for managing different types of system resources.

    Resources represent various system entities such as build configurations,
    gateway configurations, third-party service integrations, and MCP servers.
    """
    __tablename__ = "resources"

    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本字段
    name = Column(String(255), unique=True, nullable=False, index=True)
    desc = Column(Text, nullable=True)
    type = Column(Enum(ResourceType), nullable=False, index=True)
    url = Column(String(2048), nullable=True)
    view_scope = Column(String(50), nullable=False, default="private", index=True)
    owner_id = Column(String(36), nullable=True, index=True)  # Owner user ID for private resources
    api_description = Column(Text, nullable=True)  # API documentation for gateway/third resources
    _ext = Column("ext", Text, nullable=True)  # JSON stored as TEXT

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    # 索引
    __table_args__ = (
        Index('ix_resource_type', 'type'),
        Index('ix_resource_view_scope', 'view_scope'),
        Index('ix_resource_owner_id', 'owner_id'),
    )

    @hybrid_property
    def ext(self):
        """Get ext as dictionary."""
        if self._ext is None:
            return None
        try:
            return json.loads(self._ext)
        except (json.JSONDecodeError, TypeError):
            return None

    @ext.setter
    def ext(self, value):
        """Set ext from dictionary."""
        if value is None:
            self._ext = None
        else:
            self._ext = json.dumps(value)
