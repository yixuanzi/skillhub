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
from services.mcp_service import MCPService
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
        request_data: Optional request data (method, headers, params, body, path)
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
        body=request_data.body,
        path=request_data.path or ""
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


@router.get("/{resource_name}/get", response_model=GatewayResponse)
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


from pydantic import BaseModel, Field

class MCPCallRequest(BaseModel):
    """Request schema for MCP resource call."""
    method: str = Field(..., description="JSON-RPC method name (e.g., 'tools/call', 'resources/list')")
    params: dict[str, Any] = Field(default_factory=dict, description="JSON-RPC parameters")


@router.post("/{resource_name}/mcp")
async def call_mcp_resource(
    resource_name: str,
    request: MCPCallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Call an MCP server resource.

    Executes a JSON-RPC method call on the MCP server configured in the resource.

    Args:
        resource_name: Resource name (must be of type MCP)
        request: MCP call request with method and params
        db: Database session
        current_user: Authenticated user

    Returns:
        MCP server response result

    Raises:
        HTTPException 400: If resource is not MCP or config is invalid
        HTTPException 404: If resource is not found
        HTTPException 502: If MCP server call fails
    """
    from core.exceptions import ValidationException, ExternalServiceException

    try:
        result = await MCPService.call_mcp_resource(
            db=db,
            resource_name=resource_name,
            method=request.method,
            params=request.params
        )
        return result

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ExternalServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"MCP server error: {str(e)}"
        )


class MCPToolsResponse(BaseModel):
    """Response schema for MCP tools list."""
    tools: list[dict[str, Any]] = Field(description="List of available tools/methods")


@router.get("/{resource_name}/mcp/tools", response_model=MCPToolsResponse)
async def list_mcp_tools(
    resource_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List available tools from an MCP server resource.

    Returns the list of available methods/tools that can be called on the MCP server.

    Args:
        resource_name: Resource name (must be of type MCP)
        db: Database session
        current_user: Authenticated user

    Returns:
        List of available tools with their names and descriptions

    Raises:
        HTTPException 400: If resource is not MCP or config is invalid
        HTTPException 404: If resource is not found
        HTTPException 502: If MCP server connection fails
    """
    from core.exceptions import ValidationException, ExternalServiceException

    try:
        tools = await MCPService.list_tools(db=db, resource_name=resource_name)
        return MCPToolsResponse(tools=tools)

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ExternalServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"MCP server error: {str(e)}"
        )


# New routes with path support for gateway-type resources
@router.get("/{resource_name}/{path:path}", response_model=GatewayResponse)
async def call_resource_with_path_get(
    resource_name: str,
    path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """GET method for calling a gateway resource with additional path.

    This endpoint allows calling gateway-type resources with an additional path
    that will be appended to the resource's base URL.

    Example:
        GET /api/v1/gateway/my-api/users/123
        -> Calls resource 'my-api' with path '/users/123'

    Args:
        resource_name: Name of the resource to call
        path: Additional path to append to the resource URL
        request: FastAPI Request object
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = dict(request.query_params)

    # Call the resource with GET method and path
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="GET",
        params=params if params else None,
        path=path
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


@router.post("/{resource_name}/{path:path}", response_model=GatewayResponse)
async def call_resource_with_path_post(
    resource_name: str,
    path: str,
    body: Dict[str, Any] | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """POST method for calling a gateway resource with additional path.

    This endpoint allows calling gateway-type resources with an additional path
    that will be appended to the resource's base URL.

    Example:
        POST /api/v1/gateway/my-api/users
        -> Calls resource 'my-api' with path '/users'

    Args:
        resource_name: Name of the resource to call
        path: Additional path to append to the resource URL
        body: Request body to send
        request: FastAPI Request object
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = {}
    if request:
        params = dict(request.query_params)

    # Call the resource with POST method and path
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="POST",
        params=params if params else None,
        body=body,
        path=path
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


@router.put("/{resource_name}/{path:path}", response_model=GatewayResponse)
async def call_resource_with_path_put(
    resource_name: str,
    path: str,
    body: Dict[str, Any] | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """PUT method for calling a gateway resource with additional path.

    This endpoint allows calling gateway-type resources with an additional path
    that will be appended to the resource's base URL.

    Example:
        PUT /api/v1/gateway/my-api/users/123
        -> Calls resource 'my-api' with path '/users/123'

    Args:
        resource_name: Name of the resource to call
        path: Additional path to append to the resource URL
        body: Request body to send
        request: FastAPI Request object
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = {}
    if request:
        params = dict(request.query_params)

    # Call the resource with PUT method and path
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="PUT",
        params=params if params else None,
        body=body,
        path=path
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


@router.delete("/{resource_name}/{path:path}", response_model=GatewayResponse)
async def call_resource_with_path_delete(
    resource_name: str,
    path: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """DELETE method for calling a gateway resource with additional path.

    This endpoint allows calling gateway-type resources with an additional path
    that will be appended to the resource's base URL.

    Example:
        DELETE /api/v1/gateway/my-api/users/123
        -> Calls resource 'my-api' with path '/users/123'

    Args:
        resource_name: Name of the resource to call
        path: Additional path to append to the resource URL
        request: FastAPI Request object
        db: Database session
        current_user: Authenticated user

    Returns:
        Gateway response with success status, resource info, and data/error
    """
    # Extract query parameters
    params = dict(request.query_params)

    # Call the resource with DELETE method and path
    result = await GatewayService.call_resource(
        db=db,
        resource_name=resource_name,
        user=current_user,
        method="DELETE",
        params=params if params else None,
        path=path
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