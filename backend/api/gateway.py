"""Gateway API endpoints for resource invocation.

This module provides FastAPI endpoints for calling resources through the gateway
with automatic ACL permission checking and resource invocation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from database import get_db
from schemas.gateway import GatewayResponse, GatewayCallRequest
from services.gateway_service import GatewayService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/gateway", tags=["Gateway"])


@router.post("/{resource_name}", response_model=GatewayResponse)
async def call_resource(
    resource_name: str,
    request_data: GatewayCallRequest | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Call a resource through the gateway with ACL permission checking.

    This endpoint acts as a gateway to invoke various resources (build, gateway, third-party)
    with automatic permission verification before making the actual call.

    Args:
        resource_name: Name of the resource to call (path parameter)
        request_data: Optional request data (method, headers, params, body)
        request: FastAPI Request object for additional context
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error

    Raises:
        HTTPException 403: If permission denied
        HTTPException 404: If resource not found
        HTTPException 500: If internal error occurs
    """
    # Set default request data if not provided
    if request_data is None:
        request_data = GatewayCallRequest()

    # Extract additional context from the request
    client_host = None
    if request and request.client:
        client_host = request.client.host

    # Add client IP to headers for audit purposes
    headers = request_data.headers or {}
    if client_host:
        headers["X-Forwarded-For"] = client_host
        headers["X-Real-IP"] = client_host

    # Call the resource
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method=request_data.method or "GET",
        headers=headers if headers else None,
        params=request_data.params,
        body=request_data.body
    )

    # Check for specific error types
    if not result["success"]:
        error = result.get("error", "Unknown error")
        error_type = result.get("error_type", "internal_error")

        if error_type == "permission_denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        elif error_type == "resource_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )

    return GatewayResponse(**result)


@router.get("/{resource_name}", response_model=GatewayResponse)
async def call_resource_get(
    resource_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """GET shortcut for calling a resource through the gateway.

    This is a convenience endpoint that automatically uses GET method.
    Query parameters from the URL will be passed to the backend resource.

    Args:
        resource_name: Name of the resource to call (path parameter)
        request: FastAPI Request object
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = dict(request.query_params)

    # Call the resource with GET method
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="GET",
        params=params if params else None
    )

    # Check for errors
    if not result["success"]:
        error = result.get("error", "Unknown error")
        error_type = result.get("error_type", "internal_error")

        if error_type == "permission_denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        elif error_type == "resource_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )

    return GatewayResponse(**result)


@router.post("/{resource_name}/post", response_model=GatewayResponse)
async def call_resource_post(
    resource_name: str,
    body: Dict[str, Any] | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """POST shortcut for calling a resource through the gateway.

    This is a convenience endpoint that automatically uses POST method.
    The request body will be passed as JSON to the backend resource.

    Args:
        resource_name: Name of the resource to call (path parameter)
        body: Request body to send
        request: FastAPI Request object for additional context
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = {}
    if request:
        params = dict(request.query_params)

    # Call the resource with POST method
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="POST",
        params=params if params else None,
        body=body
    )

    # Check for errors
    if not result["success"]:
        error = result.get("error", "Unknown error")
        error_type = result.get("error_type", "internal_error")

        if error_type == "permission_denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error
            )
        elif error_type == "resource_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error
            )

    return GatewayResponse(**result)
