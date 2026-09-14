"""MCP (Model Context Protocol) Service for calling MCP servers.

This module provides the business logic for calling MCP servers via langchain_mcp_adapters:
- SSE: Server-Sent Events HTTP endpoint
- HTTPSTREAM: HTTP-based streaming protocol for MCP (bidirectional streaming)

Uses MultiServerMCPClient for connection management and caching.

Cache keying: each MCP resource's headers/config are resolved with the calling
user's own token (see ``_replace_tokens``), so the cache is keyed per
(resource_name, user_id) pair, never by resource_name alone. Sharing an entry
across users would mean every user after the first silently reuses whichever
user's token happened to warm the cache.
"""
import asyncio
import logging
import re
import time
from typing import Any, Optional, Dict
from sqlalchemy.orm import Session

from models.resource import Resource, ResourceType
from models.user import User
from schemas.resource import MCPConfig, MCPServerType
from core.exceptions import ValidationException, ExternalServiceException
from config import settings

logger = logging.getLogger(__name__)


class MCPService:
    """Service for calling MCP (Model Context Protocol) servers.

    This service uses MultiServerMCPClient from langchain_mcp_adapters
    to manage connections and cache MCP tools for efficient reuse.
    """

    # Class-level cache for MCP clients and tools, keyed by "{resource_name}::{user_id}".
    # Structure: {cache_key: {"client": MultiServerMCPClient, "tools": dict, "config": dict, "created_at": float}}
    _mcp_cache: Dict[str, Dict[str, Any]] = {}

    # One lock per cache key so a slow connect/handshake for one (resource, user)
    # pair doesn't block unrelated resources or users. Creating/looking up a lock
    # here never awaits, so no guard is needed around this dict in asyncio's
    # single-threaded event loop.
    _key_locks: Dict[str, asyncio.Lock] = {}

    @staticmethod
    def _cache_key(resource_name: str, user_id: str) -> str:
        return f"{resource_name}::{user_id}"

    @staticmethod
    def _get_key_lock(cache_key: str) -> asyncio.Lock:
        lock = MCPService._key_locks.get(cache_key)
        if lock is None:
            lock = asyncio.Lock()
            MCPService._key_locks[cache_key] = lock
        return lock

    @staticmethod
    def _is_expired(entry: Dict[str, Any]) -> bool:
        ttl = settings.MCP_CACHE_TTL_SECONDS
        if ttl <= 0:
            return False
        return (time.monotonic() - entry["created_at"]) > ttl

    @staticmethod
    def _evict_if_needed() -> None:
        """Drop the oldest entries once the cache exceeds its configured size.

        Bounds total connections held (resources x users), since without this
        the cache would otherwise grow forever.
        """
        max_entries = settings.MCP_CACHE_MAX_ENTRIES
        overflow = len(MCPService._mcp_cache) - max_entries
        if max_entries <= 0 or overflow <= 0:
            return

        oldest_keys = sorted(
            MCPService._mcp_cache.keys(),
            key=lambda k: MCPService._mcp_cache[k]["created_at"],
        )[:overflow]
        for key in oldest_keys:
            MCPService._mcp_cache.pop(key, None)
            lock = MCPService._key_locks.get(key)
            if lock is not None and not lock.locked():
                MCPService._key_locks.pop(key, None)

    @staticmethod
    def parse_mcp_config(ext: dict) -> MCPConfig:
        """Parse and validate MCP config from resource ext.

        Args:
            ext: Resource ext dictionary containing MCP configuration

        Returns:
            Validated MCPConfig object

        Raises:
            ValidationException: If MCP config is invalid
        """
        if not ext:
            raise ValidationException("MCP resources must have ext configuration")

        # Handle both direct ext config and nested mcp_config
        if 'mcp_config' in ext:
            config_dict = ext['mcp_config']
        else:
            config_dict = ext

        return MCPConfig(**config_dict)

    @staticmethod
    def _replace_tokens(db: Session, value: Any, user_id: str) -> Any:
        """Replace ${token:name} placeholders with actual token values.

        This supports both string values and dict values (for env vars).

        Args:
            db: Database session
            value: String or dict that may contain token placeholders

        Returns:
            String or dict with tokens replaced

        Raises:
            ValidationException: If referenced token is not found
        """
        from models.mtoken import MToken

        # Handle dict case (for env vars)
        if isinstance(value, dict):
            result = {}
            for key, val in value.items():
                if isinstance(val, str) and "${token:" in val:
                    # Extract token name: ${token:api_name} -> api_name
                    match = re.search(r'\$\{token:([^}]+)\}', val)
                    if match:
                        key_name = match.group(1)
                        # Look up token by key_name
                        token = db.query(MToken).filter(
                            MToken.key_name == key_name,
                            MToken.created_by == user_id
                        ).first()
                        if token:
                            val = val.replace(f'${{token:{key_name}}}', token.value)
                        else:
                            raise ValidationException(f"Token not found: {key_name}")
                result[key] = val
            return result

        # Handle string case (for endpoint URLs)
        if isinstance(value, str) and "${token:" in value:
            # Extract token name: ${token:api_name} -> api_name
            match = re.search(r'\$\{token:([^}]+)\}', value)
            if match:
                key_name = match.group(1)
                # Look up token by key_name
                token = db.query(MToken).filter(
                    MToken.key_name == key_name,
                    MToken.created_by == user_id
                ).first()
                if token:
                    value = value.replace(f'${{token:{key_name}}}', token.value)
                else:
                    raise ValidationException(f"Token not found: {key_name}")

        return value

    @staticmethod
    def _convert_config_to_mcp_client_format(
        resource_name: str,
        config: MCPConfig,
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """Convert MCPConfig to MultiServerMCPClient format.

        Args:
            resource_name: Name of the resource (used as server name)
            config: MCPConfig object
            db: Optional database session for token replacement

        Returns:
            Config dict in format expected by MultiServerMCPClient

        Raises:
            ValidationException: If transport is not supported
        """
        # config.transport is a string (Literal type)
        if config.transport == MCPServerType.STDIO or config.transport == "stdio":
            raise ValidationException(
                "STDIO transport is not supported. Please use SSE or HTTPSTREAM."
            )
        elif config.transport == MCPServerType.WS or config.transport == "ws":
            raise ValidationException(
                "WebSocket transport is not supported. Please use SSE or HTTPSTREAM."
            )
        elif config.transport not in (MCPServerType.SSE, MCPServerType.HTTPSTREAM, "sse", "httpstream"):
            raise ValidationException(f"Unsupported transport: {config.transport}")

        # Build base configuration
        mcp_config = {
            "url": config.endpoint,
            "transport": "streamable_http" if config.transport == 'httpstream' else config.transport
        }

        # Add headers if provided
        if config.headers:
            # Replace tokens in header values if db session provided
            if db and user_id:
                headers = MCPService._replace_tokens(db, config.headers, user_id)
            else:
                headers = config.headers
            mcp_config["headers"] = headers

        return {
            resource_name: mcp_config
        }

    @staticmethod
    async def _get_or_create_client(
        resource_name: str,
        config: MCPConfig,
        db: Optional[Session] = None,
        user_id: Optional[str] = None
    ) -> tuple[Any, dict]:
        """Get or create an MCP client scoped to this resource AND this user.

        Args:
            resource_name: Name of the resource
            config: MCPConfig object
            db: Database session, used to resolve this user's own tokens
            user_id: The calling user's id — required, since headers/config are
                resolved with this user's tokens and must never be shared with
                another user's cached client

        Returns:
            Tuple of (MultiServerMCPClient, tools_dict)

        Raises:
            ValidationException: If transport is not supported or user_id is missing
            ExternalServiceException: If connection fails
        """
        if not user_id:
            raise ValidationException("user_id is required to resolve MCP credentials")

        cache_key = MCPService._cache_key(resource_name, user_id)
        lock = MCPService._get_key_lock(cache_key)

        async with lock:
            # Check if a still-fresh client exists in cache for this resource+user
            cached = MCPService._mcp_cache.get(cache_key)
            if cached is not None and not MCPService._is_expired(cached):
                logger.info(f"Using cached MCP client for resource={resource_name} user={user_id}")
                return cached["client"], cached["tools"]

            # Create new client, resolving tokens for the current user
            try:
                from langchain_mcp_adapters.client import MultiServerMCPClient

                mcp_config = MCPService._convert_config_to_mcp_client_format(
                    resource_name, config, db, user_id
                )

                logger.info(f"Creating MCP client for resource={resource_name} user={user_id}")
                logger.debug(f"MCP config: {mcp_config}")

                if settings.SKIP_VERIFY:
                    import httpx
                    for server_cfg in mcp_config.values():
                        server_cfg["httpx_client_factory"] = lambda **kw: httpx.AsyncClient(verify=False, **kw)

                client = MultiServerMCPClient(mcp_config)

                # Load tools with timeout
                try:
                    tools = await asyncio.wait_for(
                        client.get_tools(server_name=resource_name),
                        timeout=config.timeout / 1000
                    )

                    # Create tools lookup dict {method_name: tool}
                    tools_dict = {}
                    for tool in tools:
                        tools_dict[tool.name] = tool

                    logger.info(
                        f"Loaded {len(tools)} tools from MCP server: {resource_name}"
                    )

                    # Cache the client and tools, scoped to this resource+user
                    MCPService._mcp_cache[cache_key] = {
                        "client": client,
                        "tools": tools_dict,
                        "config": mcp_config,
                        "created_at": time.monotonic(),
                    }
                    MCPService._evict_if_needed()

                    return client, tools_dict

                except asyncio.TimeoutError:
                    logger.error(f"Timeout loading MCP tools for: {resource_name}")
                    raise ExternalServiceException(
                        f"Timeout connecting to MCP server: {resource_name}"
                    )

            except ImportError:
                raise ExternalServiceException(
                    "langchain_mcp_adapters package is required. "
                    "Install it with: pip install langchain-mcp-adapters"
                )
            except Exception as e:
                logger.error(f"Failed to create MCP client for {resource_name}: {e}")
                raise ExternalServiceException(
                    f"Failed to connect to MCP server: {str(e)}"
                )

    @staticmethod
    async def call_mcp_resource(
        db: Session,
        resource_name: str,
        method: str,
        params: dict[str, Any],
        user: User
    ) -> dict[str, Any]:
        """Call an MCP server resource.

        Args:
            db: Database session
            resource_name: Resource name
            method: JSON-RPC method name (tool name)
            params: JSON-RPC parameters (tool arguments)

        Returns:
            Tool execution result

        Raises:
            ValidationException: If resource not found, invalid, or transport not supported
            ExternalServiceException: If MCP server call fails
        """
        print(f"[MCPService] call_mcp_resource: resource_name={resource_name}, method={method}")

        resource = db.query(Resource).filter(Resource.name == resource_name).first()
        if not resource:
            raise ValidationException(f"Resource '{resource_name}' not found")

        # Enforce the same visibility/ACL checks as standard resource access.
        from services.resource_service import ResourceService
        ResourceService.get_accessible(db, resource.id, user)

        if resource.type != ResourceType.MCP:
            raise ValidationException("Resource is not an MCP resource")

        config = MCPService.parse_mcp_config(resource.ext)

        # Get or create MCP client
        client, tools_dict = await MCPService._get_or_create_client(
            resource_name,
            config,
            db,
            str(user.id)
        )

        # Find the tool by method name
        if method not in tools_dict:
            available_tools = list(tools_dict.keys())
            logger.error(
                f"Method '{method}' not found in MCP server '{resource_name}'. "
                f"Available tools: {available_tools}"
            )
            raise ValidationException(
                f"Method '{method}' not found. Available tools: {available_tools}"
            )

        tool = tools_dict[method]

        # Invoke the tool
        try:
            print(f"[MCPService] Invoking tool: {method} with params: {params}")
            result = await tool.ainvoke(params)
            #print(f"[MCPService] Tool result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error invoking tool {method}: {e}")
            raise ExternalServiceException(
                f"Error calling MCP method '{method}': {str(e)}"
            )

    @staticmethod
    async def list_tools(
        db: Session,
        resource_name: str,
        user: User
    ) -> list[dict[str, Any]]:
        """List available tools/methods from an MCP resource.

        Args:
            db: Database session
            resource_name: Resource name

        Returns:
            List of available tools with their schemas

        Raises:
            ValidationException: If resource not found or invalid
            ExternalServiceException: If connection fails
        """
        resource = db.query(Resource).filter(Resource.name == resource_name).first()
        if not resource:
            raise ValidationException(f"Resource '{resource_name}' not found")

        # Enforce the same visibility/ACL checks as standard resource access.
        from services.resource_service import ResourceService
        ResourceService.get_accessible(db, resource.id, user)

        if resource.type != ResourceType.MCP:
            raise ValidationException("Resource is not an MCP resource")

        config = MCPService.parse_mcp_config(resource.ext)

        # Get or create MCP client
        client, tools_dict = await MCPService._get_or_create_client(
            resource_name,
            config,
            db,
            str(user.id)
        )

        # Return tool information
        tools_info = []
        for tool_name, tool in tools_dict.items():
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "args_schema": str(tool.args_schema) if hasattr(tool, 'args_schema') else None
            })

        return tools_info

    @staticmethod
    def invalidate_resource(resource_name: str) -> None:
        """Drop every cached MCP client for this resource, across all users.

        Synchronous and safe to call from non-async code (e.g. resource
        update/delete in ``ResourceService``): the dict/lock mutations here
        contain no ``await`` points, so nothing can interleave with them on
        asyncio's single-threaded event loop. Call this whenever a resource's
        ``ext`` config (endpoint, headers, token placeholders) or name changes,
        or the resource is deleted — otherwise a stale cached client keeps
        using the old config/token indefinitely.
        """
        prefix = f"{resource_name}::"
        stale_keys = [k for k in MCPService._mcp_cache if k.startswith(prefix)]
        for key in stale_keys:
            MCPService._mcp_cache.pop(key, None)
            lock = MCPService._key_locks.get(key)
            if lock is not None and not lock.locked():
                MCPService._key_locks.pop(key, None)
        if stale_keys:
            logger.info(f"Invalidated {len(stale_keys)} cached MCP client(s) for resource: {resource_name}")

    @staticmethod
    async def clear_cache(resource_name: Optional[str] = None, user_id: Optional[str] = None):
        """Clear cached MCP clients.

        Args:
            resource_name: Specific resource to clear (all users, unless
                user_id is also given). None clears everything.
            user_id: Combined with resource_name, clears only that resource's
                cache entry for this specific user.
        """
        if resource_name and user_id:
            cache_key = MCPService._cache_key(resource_name, user_id)
            MCPService._mcp_cache.pop(cache_key, None)
            MCPService._key_locks.pop(cache_key, None)
            logger.info(f"Cleared MCP cache for resource={resource_name} user={user_id}")
        elif resource_name:
            MCPService.invalidate_resource(resource_name)
        else:
            MCPService._mcp_cache.clear()
            MCPService._key_locks.clear()
            logger.info("Cleared all MCP caches")

    @staticmethod
    def get_cached_resources() -> list[str]:
        """Get cache keys ("{resource_name}::{user_id}") with active clients."""
        return list(MCPService._mcp_cache.keys())
