"""Tests for MCP Service.

This module contains tests for the MCP service including config parsing,
token replacement, and transport handlers.
"""
import pytest
from pydantic import ValidationError

from services.mcp_service import MCPService
from schemas.resource import MCPConfig, MCPServerType
from core.exceptions import ValidationException


class TestMCPConfigParsing:
    """Test MCP configuration parsing."""

    def test_parse_mcp_config_stdio(self):
        """Test parsing stdio MCP config."""
        ext = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-example"],
            "timeout": 30000
        }
        config = MCPService.parse_mcp_config(ext)

        assert config.transport == MCPServerType.STDIO
        assert config.command == "npx"
        assert config.args == ["-y", "@modelcontextprotocol/server-example"]
        assert config.timeout == 30000

    def test_parse_mcp_config_sse(self):
        """Test parsing SSE MCP config."""
        ext = {
            "transport": "sse",
            "endpoint": "http://localhost:3000/sse",
            "timeout": 30000
        }
        config = MCPService.parse_mcp_config(ext)

        assert config.transport == MCPServerType.SSE
        assert config.endpoint == "http://localhost:3000/sse"

    def test_parse_mcp_config_ws(self):
        """Test parsing WebSocket MCP config."""
        ext = {
            "transport": "ws",
            "endpoint": "ws://localhost:3000/ws",
            "timeout": 30000
        }
        config = MCPService.parse_mcp_config(ext)

        assert config.transport == MCPServerType.WS
        assert config.endpoint == "ws://localhost:3000/ws"

    def test_parse_mcp_config_httpstream(self):
        """Test parsing HTTPSTREAM MCP config."""
        ext = {
            "transport": "httpstream",
            "endpoint": "http://localhost:3000/stream",
            "timeout": 30000
        }
        config = MCPService.parse_mcp_config(ext)

        assert config.transport == MCPServerType.HTTPSTREAM
        assert config.endpoint == "http://localhost:3000/stream"

    def test_parse_mcp_config_empty_raises_error(self):
        """Test that empty config raises error."""
        with pytest.raises(ValidationException):
            MCPService.parse_mcp_config({})

    def test_parse_mcp_config_none_raises_error(self):
        """Test that None config raises error."""
        with pytest.raises(ValidationException):
            MCPService.parse_mcp_config(None)


class TestMCPConfigValidation:
    """Test MCP config validation."""

    def test_stdio_requires_command(self):
        """Test that stdio transport requires command."""
        with pytest.raises(ValidationError) as exc_info:
            MCPConfig(
                transport=MCPServerType.STDIO,
                timeout=30000
            )
        assert "command is required" in str(exc_info.value)

    def test_stdio_with_command_valid(self):
        """Test that stdio with command is valid."""
        config = MCPConfig(
            transport=MCPServerType.STDIO,
            command="npx",
            timeout=30000
        )
        assert config.command == "npx"

    def test_sse_requires_endpoint(self):
        """Test that SSE transport requires endpoint."""
        with pytest.raises(ValidationError) as exc_info:
            MCPConfig(
                transport=MCPServerType.SSE,
                timeout=30000
            )
        assert "endpoint is required" in str(exc_info.value)

    def test_sse_with_endpoint_valid(self):
        """Test that SSE with endpoint is valid."""
        config = MCPConfig(
            transport=MCPServerType.SSE,
            endpoint="http://localhost:3000/sse",
            timeout=30000
        )
        assert config.endpoint == "http://localhost:3000/sse"

    def test_ws_requires_endpoint(self):
        """Test that WS transport requires endpoint."""
        with pytest.raises(ValidationError) as exc_info:
            MCPConfig(
                transport=MCPServerType.WS,
                timeout=30000
            )
        assert "endpoint is required" in str(exc_info.value)

    def test_ws_with_endpoint_valid(self):
        """Test that WS with endpoint is valid."""
        config = MCPConfig(
            transport=MCPServerType.WS,
            endpoint="ws://localhost:3000/ws",
            timeout=30000
        )
        assert config.endpoint == "ws://localhost:3000/ws"

    def test_httpstream_requires_endpoint(self):
        """Test that HTTPSTREAM transport requires endpoint."""
        with pytest.raises(ValidationError) as exc_info:
            MCPConfig(
                transport=MCPServerType.HTTPSTREAM,
                timeout=30000
            )
        assert "endpoint is required" in str(exc_info.value)

    def test_httpstream_with_endpoint_valid(self):
        """Test that HTTPSTREAM with endpoint is valid."""
        config = MCPConfig(
            transport=MCPServerType.HTTPSTREAM,
            endpoint="http://localhost:3000/stream",
            timeout=30000
        )
        assert config.endpoint == "http://localhost:3000/stream"

    def test_timeout_bounds(self):
        """Test timeout validation bounds."""
        # Below minimum
        with pytest.raises(ValidationError):
            MCPConfig(
                transport=MCPServerType.STDIO,
                command="test",
                timeout=500  # Too low
            )

        # Above maximum
        with pytest.raises(ValidationError):
            MCPConfig(
                transport=MCPServerType.STDIO,
                command="test",
                timeout=500000  # Too high
            )

        # Valid bounds
        config = MCPConfig(
            transport=MCPServerType.STDIO,
            command="test",
            timeout=10000  # Valid
        )
        assert config.timeout == 10000


class TestTokenReplacement:
    """Test token placeholder replacement in env vars."""

    def test_replace_tokens_single_placeholder(self, db):
        """Test replacing single token placeholder."""
        from models.mtoken import MToken
        import uuid

        # Create test token
        user_id = str(uuid.uuid4())
        token = MToken(
            app_name="test_app",
            key_name="test_api",
            value="secret_key_123",
            desc="Test API token",
            created_by=user_id
        )
        db.add(token)
        db.commit()

        env = {"API_KEY": "${token:test_api}"}
        result = MCPService._replace_tokens(db, env)

        assert result["API_KEY"] == "secret_key_123"

    def test_replace_tokens_multiple_placeholders(self, db):
        """Test replacing multiple token placeholders."""
        from models.mtoken import MToken
        import uuid

        user_id = str(uuid.uuid4())
        token1 = MToken(
            app_name="app1",
            key_name="api1",
            value="key1",
            desc="API 1",
            created_by=user_id
        )
        token2 = MToken(
            app_name="app2",
            key_name="api2",
            value="key2",
            desc="API 2",
            created_by=user_id
        )
        db.add_all([token1, token2])
        db.commit()

        env = {
            "API1_KEY": "${token:api1}",
            "API2_KEY": "${token:api2}",
            "STATIC": "no_change"
        }
        result = MCPService._replace_tokens(db, env)

        assert result["API1_KEY"] == "key1"
        assert result["API2_KEY"] == "key2"
        assert result["STATIC"] == "no_change"

    def test_replace_tokens_missing_token_raises_error(self, db):
        """Test that missing token raises error."""
        env = {"API_KEY": "${token:nonexistent}"}

        with pytest.raises(ValidationException) as exc_info:
            MCPService._replace_tokens(db, env)
        assert "Token not found" in str(exc_info.value)

    def test_replace_tokens_non_dict_env(self, db):
        """Test handling non-dict env values."""
        env = {"KEY": "value without placeholder"}
        result = MCPService._replace_tokens(db, env)

        assert result["KEY"] == "value without placeholder"


class TestMCPServiceIntegration:
    """Integration tests for MCP service (would require actual MCP servers)."""

    @pytest.mark.skip("Requires actual MCP server running")
    async def test_call_stdio_mcp_server(self, db):
        """Test calling actual stdio MCP server."""
        # This would require an actual MCP server to be running
        pass

    @pytest.mark.skip("Requires actual MCP server running")
    async def test_call_sse_mcp_server(self, db):
        """Test calling actual SSE MCP server."""
        # This would require an actual MCP server to be running
        pass

    @pytest.mark.skip("Requires actual MCP server running")
    async def test_call_ws_mcp_server(self, db):
        """Test calling actual WebSocket MCP server."""
        # This would require an actual MCP server to be running
        pass
