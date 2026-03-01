"""Gateway service for resource invocation with ACL permission checking.

This module provides the business logic for calling resources through the gateway,
including permission verification, resource lookup, and actual HTTP invocation.
"""
from sqlalchemy.orm import Session
from models.resource import Resource, ResourceType
from models.user import User
from schemas.acl_resource import PermissionCheckRequest
from services.acl_resource_service import ACLResourceService
from services.mtoken_service import MTokenService
from core.exceptions import NotFoundException, ValidationException
from typing import Optional, Dict, Any
import httpx
import asyncio
import time
import json
import logging
import re

logger = logging.getLogger(__name__)


class GatewayService:
    """Service class for gateway operations."""

    @staticmethod
    def _replace_token_placeholders(db: Session, user_id: str, config: Any) -> Any:
        """Replace token placeholders in config with actual token values from mtoken.

        This function recursively traverses the config dictionary and replaces
        any string values containing {key} pattern with the corresponding token value
        from the user's mtoken storage.

        Args:
            db: Database session
            user_id: ID of the current user
            config: Configuration dictionary (may contain nested dicts/lists/strings)

        Returns:
            New config dictionary with placeholders replaced

        Example:
            Input:  {"headers": {"Authorization": "Bearer {github_token}"}}
            Output: {"headers": {"Authorization": "Bearer ghp_xxx"}}
        """
        # Handle string case - process for placeholders
        if isinstance(config, str):
            pattern = r'\{([a-zA-Z0-9_]+)\}'
            matches = re.findall(pattern, config)

            if matches:
                new_value = config
                for placeholder in matches:
                    token_key = placeholder
                    # Find token from user's mtoken storage
                    mtokens = MTokenService.list_all(db, user_id, limit=1000)
                    found = False

                    for mtoken in mtokens:
                        if mtoken.app_name == token_key:
                            new_value = new_value.replace(f"{{{placeholder}}}", mtoken.value)
                            found = True
                            logger.info(f"Replaced token placeholder: {{{placeholder}}} -> ***")
                            break

                    if not found:
                        logger.warning(f"Token placeholder {{{placeholder}}} not found in user's mtokens")

                return new_value
            return config

        # Handle list case - process each item
        if isinstance(config, list):
            new_list = []
            for item in config:
                if isinstance(item, (dict, list, str)):
                    new_list.append(GatewayService._replace_token_placeholders(db, user_id, item))
                else:
                    new_list.append(item)
            return new_list

        # Handle dict case - process each value
        if isinstance(config, dict):
            new_config = {}
            for key, value in config.items():
                if isinstance(value, (dict, list, str)):
                    new_config[key] = GatewayService._replace_token_placeholders(db, user_id, value)
                else:
                    new_config[key] = value
            return new_config

        # Return other types as-is
        return config

    @staticmethod
    def _build_url(base_url: str, path: str) -> str:
        """Build a complete URL by intelligently joining base_url and path.

        This function handles slash placement to ensure a properly formed URL:
        - Removes trailing slash from base_url
        - Ensures path starts with a slash (unless empty)

        Args:
            base_url: The base URL (e.g., "https://api.example.com" or "https://api.example.com/")
            path: The path to append (e.g., "/users" or "users" or "")

        Returns:
            Properly joined URL string

        Examples:
            >>> GatewayService._build_url("https://api.example.com", "/users")
            "https://api.example.com/users"
            >>> GatewayService._build_url("https://api.example.com/", "users")
            "https://api.example.com/users"
            >>> GatewayService._build_url("https://api.example.com/", "/v1/data")
            "https://api.example.com/v1/data"
            >>> GatewayService._build_url("https://api.example.com", "")
            "https://api.example.com"
        """
        # Remove trailing slash from base_url
        base = base_url.rstrip("/")

        # Ensure path starts with slash (unless empty)
        if path and not path.startswith("/"):
            path = "/" + path
        elif not path:
            path = ""

        return base + path

    @staticmethod
    async def call_resource(
        db: Session,
        resource_name: str,
        user: User,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        path: str = ""
    ) -> Dict[str, Any]:
        """Call a resource through the gateway with ACL permission checking.

        Args:
            db: Database session
            resource_name: Name of the resource to call
            user: Current authenticated user
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Additional headers to include
            params: Query parameters
            body: Request body for POST/PUT
            path: Additional path to append to resource URL (for gateway type resources)

        Returns:
            Gateway response dict with success, data, error, etc.

        Raises:
            NotFoundException: If resource not found
            ValidationException: If permission denied
        """
        start_time = time.time()

        try:
            # Step 1: Get resource by name
            resource = db.query(Resource).filter(Resource.name == resource_name).first()
            if not resource:
                raise NotFoundException(f"Resource '{resource_name}' not found")

            # Step 2: Check ACL permission
            # check_data = PermissionCheckRequest(
            #     user_id=str(user.id),
            #     required_permission="execute"  # Default permission for gateway calls
            # )
            permission_result = ACLResourceService.check_permission(
                db, resource.id, user
            )

            if not permission_result.allowed:
                logger.warning(
                    f"Gateway access denied for user '{user.username}' "
                    f"to resource '{resource_name}': {permission_result.reason}"
                )
                raise ValidationException(
                    f"Permission denied"
                )

            # Step 3: Invoke resource based on type
            result = await GatewayService._invoke_resource(
                user, resource, method, headers, params, body, path
            )

            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            return {
                "success": True,
                "resource_name": resource.name,
                "resource_type": resource.type.value,
                "status_code": result.get("status_code"),
                "data": result.get("data"),
                "execution_time_ms": execution_time,
                "error": None
            }

        except (NotFoundException, ValidationException) as e:
            execution_time = (time.time() - start_time) * 1000
            error_type = "resource_not_found" if isinstance(e, NotFoundException) else "permission_denied"

            return {
                "success": False,
                "resource_name": resource_name,
                "resource_type": None,
                "status_code": None,
                "data": None,
                "error": str(e),
                "error_type": error_type,
                "execution_time_ms": execution_time
            }
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Gateway call error for resource '{resource_name}': {str(e)}")

            return {
                "success": False,
                "resource_name": resource_name,
                "resource_type": None,
                "status_code": None,
                "data": None,
                "error": f"Internal error: {str(e)}",
                "execution_time_ms": execution_time
            }

    @staticmethod
    async def _invoke_resource(
        user: User,
        resource: Resource,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        path: str = ""
    ) -> Dict[str, Any]:
        """Invoke a resource based on its type.

        Args:
            user: Current user for auth headers
            resource: Resource model
            method: HTTP method
            headers: Additional headers
            params: Query parameters
            body: Request body
            path: Additional path to append to resource URL (for gateway type)

        Returns:
            Response dict with status_code and data

        Raises:
            Exception: If invocation fails
        """
        resource_type = resource.type

        if resource_type == ResourceType.BUILD:
            return await GatewayService._invoke_build_resource(
                user, resource, method, headers, params, body
            )
        elif resource_type == ResourceType.GATEWAY:
            return await GatewayService._invoke_gateway_resource(
                user,resource, method, headers, params, body, path
            )
        elif resource_type == ResourceType.THIRD:
            return await GatewayService._invoke_third_party_resource(
                user,resource, method, headers, params, body
            )
        else:
            raise Exception(f"Unsupported resource type: {resource_type}")

    @staticmethod
    async def _invoke_build_resource(
        user:User,
        resource: Resource,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke a build-type resource.

        Build resources are typically internal services or microservices.
        The ext field may contain additional configuration.
        """
        if not resource.url:
            raise Exception("Build resource has no URL configured")

        # Parse ext for additional configuration
        ext_config = resource.ext or {}

        # Replace token placeholders with actual token values from user's mtoken
        from database import get_db
        db = next(get_db())
        try:
            ext_config = GatewayService._replace_token_placeholders(
                db, str(user.id), ext_config
            )
        finally:
            db.close()

        timeout = ext_config.get("timeout", 30)
        auth_headers = ext_config.get("headers", {})

        # Merge headers
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        if auth_headers:
            merged_headers.update(auth_headers)
        # get access token from user and add to headers
        merged_headers["Authorization"] = f"Bearer {user.access_token}"

        # Make HTTP call
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(
                        resource.url,
                        headers=merged_headers if merged_headers else None,
                        params=params
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        resource.url,
                        headers=merged_headers if merged_headers else None,
                        params=params,
                        json=body
                    )
                elif method.upper() == "PUT":
                    response = await client.put(
                        resource.url,
                        headers=merged_headers if merged_headers else None,
                        params=params,
                        json=body
                    )
                elif method.upper() == "DELETE":
                    response = await client.delete(
                        resource.url,
                        headers=merged_headers if merged_headers else None,
                        params=params
                    )
                else:
                    raise Exception(f"Unsupported HTTP method: {method}")

                # Try to parse response as JSON
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"content": response.text}

                return {
                    "status_code": response.status_code,
                    "data": response_data
                }

            except httpx.TimeoutException:
                raise Exception(f"Request timed out after {timeout}s")
            except httpx.HTTPError as e:
                raise Exception(f"HTTP error: {str(e)}")

    @staticmethod
    async def _invoke_gateway_resource(
        user:User,
        resource: Resource,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        path: str = ""
    ) -> Dict[str, Any]:
        """Invoke a gateway-type resource.

        Gateway resources are typically external API gateways or proxies.
        This method supports additional path appending for flexible routing.

        Args:
            resource: Resource model
            method: HTTP method
            headers: Additional headers
            params: Query parameters
            body: Request body
            path: Additional path to append to the resource URL

        Returns:
            Response dict with status_code and data
        """
        if not resource.url:
            raise Exception("Gateway resource has no URL configured")

        # Build full URL with path
        full_url = GatewayService._build_url(resource.url, path)

        # Parse ext for additional configuration
        ext_config = resource.ext or {}

        # Replace token placeholders with actual token values from user's mtoken
        from database import get_db
        db = next(get_db())
        try:
            ext_config = GatewayService._replace_token_placeholders(
                db, str(user.id), ext_config
            )
        finally:
            db.close()

        timeout = ext_config.get("timeout", 30)
        auth_headers = ext_config.get("headers", {})

        # Merge headers
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        if auth_headers:
            merged_headers.update(auth_headers)

        # Make HTTP call
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(
                        full_url,
                        headers=merged_headers if merged_headers else None,
                        params=params
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        full_url,
                        headers=merged_headers if merged_headers else None,
                        params=params,
                        json=body
                    )
                elif method.upper() == "PUT":
                    response = await client.put(
                        full_url,
                        headers=merged_headers if merged_headers else None,
                        params=params,
                        json=body
                    )
                elif method.upper() == "DELETE":
                    response = await client.delete(
                        full_url,
                        headers=merged_headers if merged_headers else None,
                        params=params
                    )
                else:
                    raise Exception(f"Unsupported HTTP method: {method}")

                # Try to parse response as JSON
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"content": response.text}

                return {
                    "status_code": response.status_code,
                    "data": response_data
                }

            except httpx.TimeoutException:
                raise Exception(f"Request timed out after {timeout}s")
            except httpx.HTTPError as e:
                raise Exception(f"HTTP error: {str(e)}")

    @staticmethod
    async def _invoke_third_party_resource(
        user:User,
        resource: Resource,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke a third-party resource.

        Third-party resources are external APIs or services.
        """
        # For now, similar to build resources
        # In the future, this might have specific third-party integration logic
        return await GatewayService._invoke_build_resource(
            resource, method, headers, params, body
        )
