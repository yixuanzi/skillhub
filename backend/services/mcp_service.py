"""MCP (Model Context Protocol) Service for calling MCP servers.

This module provides the business logic for calling MCP servers via various transports:
- STDIO: Subprocess communication via stdin/stdout
- SSE: Server-Sent Events HTTP endpoint
- WS: WebSocket endpoint
- HTTPSTREAM: HTTP-based streaming protocol for MCP (bidirectional streaming)
"""
import asyncio
import json
import re
from typing import Any, Optional
from sqlalchemy.orm import Session

from models.resource import Resource, ResourceType
from schemas.resource import MCPConfig, MCPServerType
from core.exceptions import ValidationException, ExternalServiceException


class MCPService:
    """Service for calling MCP (Model Context Protocol) servers."""

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
        return MCPConfig(**ext)

    @staticmethod
    async def call_mcp_resource(
        db: Session,
        resource_id: str,
        method: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Call an MCP server resource.

        Args:
            db: Database session
            resource_id: Resource ID
            method: JSON-RPC method name
            params: JSON-RPC parameters

        Returns:
            JSON-RPC response result

        Raises:
            ValidationException: If resource not found or invalid
            ExternalServiceException: If MCP server call fails
        """
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise ValidationException("Resource not found")

        if resource.type != ResourceType.MCP:
            raise ValidationException("Resource is not an MCP resource")

        config = MCPService.parse_mcp_config(resource.ext)

        # Replace token placeholders in env vars
        if config.env:
            config.env = MCPService._replace_tokens(db, config.env)

        if config.transport == MCPServerType.STDIO:
            return await MCPService._call_stdio(config, method, params)
        elif config.transport == MCPServerType.SSE:
            return await MCPService._call_sse(config, method, params)
        elif config.transport == MCPServerType.WS:
            return await MCPService._call_ws(config, method, params)
        elif config.transport == MCPServerType.HTTPSTREAM:
            return await MCPService._call_httpstream(config, method, params)
        else:
            raise ValidationException(f"Unsupported transport: {config.transport}")

    @staticmethod
    def _replace_tokens(db: Session, env: dict[str, str]) -> dict[str, str]:
        """Replace ${token:name} placeholders with actual token values.

        Args:
            db: Database session
            env: Environment variables dict with potential token placeholders

        Returns:
            Environment variables with tokens replaced

        Raises:
            ValidationException: If referenced token is not found
        """
        from models.mtoken import MToken

        result = {}

        for key, value in env.items():
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
            result[key] = value

        return result

    @staticmethod
    async def _call_stdio(config: MCPConfig, method: str, params: dict) -> dict:
        """
        Execute MCP server via STDIO transport.

        Spawns subprocess and communicates via JSON-RPC over stdin/stdout.

        Args:
            config: MCP configuration
            method: JSON-RPC method name
            params: JSON-RPC parameters

        Returns:
            JSON-RPC response result

        Raises:
            ExternalServiceException: If subprocess fails or times out
        """
        # Build command
        cmd = [config.command]
        if config.args:
            cmd.extend(config.args)

        # Prepare JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(config.env)} if config.env else None
            )

            # Send request
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            # Read response (with timeout)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout / 1000
                )
            except asyncio.TimeoutError:
                process.kill()
                raise ExternalServiceException("MCP server timeout")

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise ExternalServiceException(f"MCP server error: {error_msg}")

            # Parse response
            response = json.loads(stdout.decode().strip())

            if "error" in response:
                raise ExternalServiceException(f"MCP error: {response['error']}")

            return response.get("result", {})

        except FileNotFoundError:
            raise ExternalServiceException(f"Command not found: {config.command}")
        except json.JSONDecodeError:
            raise ExternalServiceException("Invalid JSON response from MCP server")

    @staticmethod
    async def _call_sse(config: MCPConfig, method: str, params: dict) -> dict:
        """
        Execute MCP server via Server-Sent Events transport.

        Connects to SSE endpoint and sends JSON-RPC request.

        Args:
            config: MCP configuration
            method: JSON-RPC method name
            params: JSON-RPC parameters

        Returns:
            JSON-RPC response result

        Raises:
            ExternalServiceException: If HTTP request fails
        """
        try:
            import httpx
        except ImportError:
            raise ExternalServiceException("httpx package required for SSE transport")

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            async with httpx.AsyncClient(timeout=config.timeout / 1000) as client:
                response = await client.post(
                    config.endpoint,
                    json=request,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                result = response.json()

                if "error" in result:
                    raise ExternalServiceException(f"MCP error: {result['error']}")

                return result.get("result", {})

        except httpx.HTTPError as e:
            raise ExternalServiceException(f"SSE connection error: {e}")

    @staticmethod
    async def _call_ws(config: MCPConfig, method: str, params: dict) -> dict:
        """
        Execute MCP server via WebSocket transport.

        Connects to WebSocket endpoint and sends JSON-RPC request.

        Args:
            config: MCP configuration
            method: JSON-RPC method name
            params: JSON-RPC parameters

        Returns:
            JSON-RPC response result

        Raises:
            ExternalServiceException: If WebSocket connection fails
        """
        try:
            import websockets
        except ImportError:
            raise ExternalServiceException("websockets package required for WS transport")

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            async with websockets.connect(
                config.endpoint,
                close_timeout=config.timeout / 1000
            ) as ws:
                await ws.send(json.dumps(request))

                response_str = await asyncio.wait_for(
                    ws.recv(),
                    timeout=config.timeout / 1000
                )

                response = json.loads(response_str)

                if "error" in response:
                    raise ExternalServiceException(f"MCP error: {response['error']}")

                return response.get("result", {})

        except asyncio.TimeoutError:
            raise ExternalServiceException("WebSocket timeout")
        except Exception as e:
            raise ExternalServiceException(f"WebSocket error: {e}")

    @staticmethod
    async def _call_httpstream(config: MCPConfig, method: str, params: dict) -> dict:
        """
        Execute MCP server via HTTP-based streaming transport.

        HTTPSTREAM is similar to SSE but supports bidirectional streaming.
        Uses HTTP POST with streaming response for server-to-client communication.

        Args:
            config: MCP configuration
            method: JSON-RPC method name
            params: JSON-RPC parameters

        Returns:
            JSON-RPC response result

        Raises:
            ExternalServiceException: If HTTP request fails
        """
        try:
            import httpx
        except ImportError:
            raise ExternalServiceException("httpx package required for HTTPSTREAM transport")

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            async with httpx.AsyncClient(timeout=config.timeout / 1000) as client:
                # Use streaming POST request
                async with client.stream(
                    "POST",
                    config.endpoint,
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/x-ndjson"
                    }
                ) as response:
                    response.raise_for_status()

                    # Read streaming response (NDJSON format)
                    result_data = None
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "result" in data:
                                    result_data = data["result"]
                                if "error" in data:
                                    raise ExternalServiceException(f"MCP error: {data['error']}")
                                # Check for completion marker
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue

                    return result_data or {}

        except httpx.HTTPError as e:
            raise ExternalServiceException(f"HTTPSTREAM connection error: {e}")
