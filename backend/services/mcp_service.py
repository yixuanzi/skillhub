"""MCP (Model Context Protocol) Service for calling MCP servers.

This module provides the business logic for calling MCP servers via langchain_mcp_adapters:
- SSE: Server-Sent Events HTTP endpoint
- HTTPSTREAM: HTTP-based streaming protocol for MCP (bidirectional streaming)

Uses MultiServerMCPClient for connection management and caching.
"""
import asyncio
import logging
import re
from typing import Any, Optional, Dict
from sqlalchemy.orm import Session

from models.resource import Resource, ResourceType
from schemas.resource import MCPConfig, MCPServerType
from core.exceptions import ValidationException, ExternalServiceException

logger = logging.getLogger(__name__)


class MCPService:
    """Service for calling MCP (Model Context Protocol) servers.

    This service uses MultiServerMCPClient from langchain_mcp_adapters
    to manage connections and cache MCP tools for efficient reuse.
    """

    # Class-level cache for MCP clients and tools
    # Structure: {resource_name: {"client": MultiServerMCPClient, "tools": dict, "config": dict}}
    _mcp_cache: Dict[str, Dict[str, Any]] = {}
    _cache_lock = asyncio.Lock()

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
    def _replace_tokens(db: Session, value: Any) -> Any:
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
                            MToken.key_name == key_name
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
                    MToken.key_name == key_name
                ).first()
                if token:
                    value = value.replace(f'${{token:{key_name}}}', token.value)
                else:
                    raise ValidationException(f"Token not found: {key_name}")

        return value

    @staticmethod
    def _convert_config_to_mcp_client_format(resource_name: str, config: MCPConfig, db: Optional[Session] = None) -> dict:
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
            if db:
                headers = MCPService._replace_tokens(db, config.headers)
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
        db: Optional[Session] = None
    ) -> tuple[Any, dict]:
        """Get or create MCP client for the resource.

        Args:
            resource_name: Name of the resource
            config: MCPConfig object

        Returns:
            Tuple of (MultiServerMCPClient, tools_dict)

        Raises:
            ValidationException: If transport is not supported
            ExternalServiceException: If connection fails
        """
        async with MCPService._cache_lock:
            # Check if client exists in cache
            if resource_name in MCPService._mcp_cache:
                cached = MCPService._mcp_cache[resource_name]
                logger.info(f"Using cached MCP client for resource: {resource_name}")
                return cached["client"], cached["tools"]

            # Create new client
            try:
                from langchain_mcp_adapters.client import MultiServerMCPClient

                mcp_config = MCPService._convert_config_to_mcp_client_format(
                    resource_name, config, db
                )

                logger.info(f"Creating MCP client for resource: {resource_name}")
                logger.debug(f"MCP config: {mcp_config}")

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

                    # Cache the client and tools
                    MCPService._mcp_cache[resource_name] = {
                        "client": client,
                        "tools": tools_dict,
                        "config": mcp_config
                    }

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
        params: dict[str, Any]
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

        if resource.type != ResourceType.MCP:
            raise ValidationException("Resource is not an MCP resource")

        config = MCPService.parse_mcp_config(resource.ext)

        # Get or create MCP client
        client, tools_dict = await MCPService._get_or_create_client(resource_name, config, db)

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
        resource_name: str
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

        if resource.type != ResourceType.MCP:
            raise ValidationException("Resource is not an MCP resource")

        config = MCPService.parse_mcp_config(resource.ext)

        # Get or create MCP client
        client, tools_dict = await MCPService._get_or_create_client(resource_name, config, db)

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
    async def clear_cache(resource_name: Optional[str] = None):
        """Clear cached MCP clients.

        Args:
            resource_name: Specific resource to clear, or None to clear all
        """
        async with MCPService._cache_lock:
            if resource_name:
                if resource_name in MCPService._mcp_cache:
                    del MCPService._mcp_cache[resource_name]
                    logger.info(f"Cleared MCP cache for: {resource_name}")
            else:
                MCPService._mcp_cache.clear()
                logger.info("Cleared all MCP caches")

    @staticmethod
    def get_cached_resources() -> list[str]:
        """Get list of resources with cached MCP clients.

        Returns:
            List of resource names with active caches
        """
        return list(MCPService._mcp_cache.keys())
