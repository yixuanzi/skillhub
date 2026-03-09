"""Pydantic schemas for resource management API.

This module defines the request/response schemas used by the resource API endpoints,
including base models for create, update, and response operations.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
from models.resource import ResourceType


class ViewScope(str, Enum):
    """Resource visibility scope options."""
    PUBLIC = "public"
    PRIVATE = "private"


class MCPServerType(str):
    """MCP server transport types."""
    STDIO = "stdio"
    SSE = "sse"
    WS = "ws"
    HTTPSTREAM = "httpstream"


# Valid MCP transport types
MCPTransportType = Literal["stdio", "sse", "ws", "httpstream"]


class MCPConfig(BaseModel):
    """Configuration for MCP (Model Context Protocol) servers.

    Supports multiple transport types with transport-specific configuration:
    - STDIO: Command execution via subprocess (requires command, optional args/env)
    - SSE: Server-Sent Events HTTP endpoint (requires endpoint)
    - WS: WebSocket endpoint (requires endpoint)
    - HTTPSTREAM: HTTP-based streaming (requires endpoint)
    """
    transport: MCPTransportType = Field(..., description="Transport type")
    timeout: int = Field(default=30000, ge=1000, le=300000,
                         description="Timeout in milliseconds (1s - 5min)")

    # STDIO-specific fields
    command: Optional[str] = Field(None, description="Command for STDIO transport")
    args: Optional[list[str]] = Field(default=None, description="Arguments for STDIO command")
    env: Optional[dict[str, str]] = Field(default=None, description="Environment variables for STDIO")

    # Network transport fields (SSE, WS, HTTPSTREAM)
    endpoint: Optional[str] = Field(None, description="Endpoint URL for network transports")
    headers: Optional[dict[str, str]] = Field(default=None, description="HTTP headers for network transports (SSE, HTTPSTREAM)")

    @model_validator(mode='after')
    def validate_transport_config(self):
        """Validate transport-specific configuration requirements."""
        if self.transport == 'stdio' and not self.command:
            raise ValueError('command is required for stdio transport')
        if self.transport in ('sse', 'ws', 'httpstream') and not self.endpoint:
            raise ValueError(f'endpoint is required for {self.transport} transport')
        return self


# 基础 Schema
class ResourceBase(BaseModel):
    """Base schema for resource data."""
    name: str = Field(..., min_length=1, max_length=255)
    desc: Optional[str] = None
    type: ResourceType
    url: Optional[str] = Field(None, max_length=2048)
    view_scope: ViewScope = Field(default=ViewScope.PRIVATE, description="Resource visibility scope")
    api_description: Optional[str] = Field(None, description="API documentation (markdown)")
    ext: Optional[dict] = None


# 创建 Schema
class ResourceCreate(ResourceBase):
    """Schema for creating a new resource."""
    pass


# 更新 Schema
class ResourceUpdate(BaseModel):
    """Schema for updating an existing resource."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    desc: Optional[str] = None
    type: Optional[ResourceType] = None
    url: Optional[str] = Field(None, max_length=2048)
    view_scope: Optional[ViewScope] = Field(None, description="Resource visibility scope")
    api_description: Optional[str] = Field(None, description="API documentation (markdown)")
    ext: Optional[dict] = None


# 响应 Schema
class ResourceResponse(ResourceBase):
    """Schema for resource response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 列表响应 Schema（分页）
class ResourceListResponse(BaseModel):
    """Schema for paginated resource list response."""
    items: list[ResourceResponse]
    total: int
    page: int
    size: int
