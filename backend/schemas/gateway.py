"""Pydantic schemas for gateway API.

This module defines the request/response schemas used by the gateway API endpoints
for calling resources through the gateway with ACL permission checking.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class GatewayCallRequest(BaseModel):
    """Schema for gateway call request data."""
    method: Optional[str] = Field(
        default="GET",
        description="HTTP method to use for the backend call"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional headers to include in the backend call"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters for the backend call"
    )
    body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Request body for POST/PUT requests"
    )


class GatewayResponse(BaseModel):
    """Schema for gateway call response."""
    success: bool = Field(..., description="Whether the call was successful")
    resource_name: str = Field(..., description="Name of the resource that was called")
    resource_type: str = Field(..., description="Type of the resource (build, gateway, third)")
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code from the backend call"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response data from the backend call"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the call failed"
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Execution time in milliseconds"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="Timestamp of the gateway call"
    )


class GatewayPermissionDenied(BaseModel):
    """Schema for permission denied response."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message explaining why access was denied")
    required_permission: Optional[str] = Field(
        default=None,
        description="Required permission for access"
    )
    resource_name: str = Field(..., description="Name of the resource")


class GatewayResourceNotFound(BaseModel):
    """Schema for resource not found response."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message explaining why resource was not found")
    resource_name: str = Field(..., description="Name of the resource that was not found")
