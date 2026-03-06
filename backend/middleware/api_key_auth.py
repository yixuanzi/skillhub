"""API Key authentication middleware.

This module provides middleware for authenticating API keys from the
Authorization header. API keys use the format: Authorization: Bearer sk_xxx

The middleware integrates with the existing authentication system by setting
user information in the request state.
"""
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.api_key_service import APIKeyService
from models.api_key import APIKey


async def get_api_key_user(request: Request) -> Optional[dict]:
    """Extract and authenticate API key from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        Dict with user_id and api_key_id if valid, None otherwise

    Raises:
        HTTPException 401: If API key is invalid or expired
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer sk_"):
        return None

    key = auth_header[7:]  # Remove "Bearer "

    # Get DB session
    db: Session = next(get_db())

    # Authenticate key
    api_key: Optional[APIKey] = APIKeyService.authenticate(db, key)

    if api_key:
        return {
            "user_id": api_key.user_id,
            "api_key_id": api_key.id,
            "api_key_scopes": api_key.scopes,
            "auth_method": "api_key"
        }

    # Invalid key - raise exception
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


class APIKeyAuthChecker:
    """Helper class for checking API key scopes in endpoints."""

    @staticmethod
    def require_scope(required_scope: str):
        """Create a dependency that checks for required API key scope.

        Args:
            required_scope: The scope required for access

        Returns:
            Dependency function that validates scope

        Example:
            @router.get("/protected")
            async def protected_endpoint(
                _: None = Depends(APIKeyAuthChecker.require_scope("skills:call"))
            ):
                ...
        """
        async def check_scope(request: Request) -> bool:
            # Get scopes from request state (set by auth)
            if not hasattr(request.state, "api_key_scopes"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key authentication required for this endpoint"
                )

            scopes = request.state.api_key_scopes
            if required_scope not in scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key missing required scope: {required_scope}"
                )

            return True

        return check_scope

    @staticmethod
    def has_any_scope(request: Request, required_scopes: list[str]) -> bool:
        """Check if API key has any of the required scopes.

        Args:
            request: FastAPI request object
            required_scopes: List of scopes, at least one is required

        Returns:
            True if key has at least one required scope

        Raises:
            HTTPException 403: If no matching scope found
        """
        if not hasattr(request.state, "api_key_scopes"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key authentication required"
            )

        scopes = request.state.api_key_scopes
        if not any(scope in scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key missing required scope. Need one of: {', '.join(required_scopes)}"
            )

        return True
