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


def _add_token(db, user_id: str, key_name: str, value: str):
    from models.mtoken import MToken

    db.add(MToken(app_name="test_app", key_name=key_name, value=value, created_by=user_id))
    db.commit()


class TestTokenReplacement:
    """MCP headers use the same {token_name} syntax as gateway/third/composio."""

    def test_replace_tokens_single_placeholder(self, db):
        import uuid

        user_id = str(uuid.uuid4())
        _add_token(db, user_id, "test_api", "secret_key_123")

        headers = {"Authorization": "Bearer {test_api}"}
        result = MCPService._replace_tokens(db, headers, user_id)

        assert result["Authorization"] == "Bearer secret_key_123"

    def test_replace_tokens_multiple_keys(self, db):
        import uuid

        user_id = str(uuid.uuid4())
        _add_token(db, user_id, "api1", "key1")
        _add_token(db, user_id, "api2", "key2")

        headers = {
            "API1_KEY": "{api1}",
            "API2_KEY": "{api2}",
            "STATIC": "no_change",
        }
        result = MCPService._replace_tokens(db, headers, user_id)

        assert result["API1_KEY"] == "key1"
        assert result["API2_KEY"] == "key2"
        assert result["STATIC"] == "no_change"

    def test_multiple_placeholders_in_one_value(self, db):
        """Regression: the old ${token:} implementation only replaced the first."""
        import uuid

        user_id = str(uuid.uuid4())
        _add_token(db, user_id, "api1", "key1")
        _add_token(db, user_id, "api2", "key2")

        headers = {"X-Auth": "{api1}:{api2}"}
        result = MCPService._replace_tokens(db, headers, user_id)

        assert result["X-Auth"] == "key1:key2"

    def test_replace_tokens_missing_token_raises_error(self, db):
        import uuid

        user_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer {nonexistent}"}

        with pytest.raises(ValidationException) as exc_info:
            MCPService._replace_tokens(db, headers, user_id)
        assert "Token not found" in str(exc_info.value)

    def test_legacy_syntax_is_rejected_loudly(self, db):
        """${token:name} is no longer supported and must not pass through."""
        import uuid

        user_id = str(uuid.uuid4())
        _add_token(db, user_id, "test_api", "secret_key_123")

        headers = {"Authorization": "Bearer ${token:test_api}"}

        with pytest.raises(ValidationException) as exc_info:
            MCPService._replace_tokens(db, headers, user_id)
        message = str(exc_info.value)
        assert "no longer supported" in message
        assert "{test_api}" in message  # tells the user what to migrate to

    def test_tokens_resolve_only_against_calling_user(self, db):
        """A user must never pick up another user's token of the same name."""
        import uuid

        owner_id = str(uuid.uuid4())
        other_id = str(uuid.uuid4())
        _add_token(db, owner_id, "shared_name", "OWNER_SECRET")

        headers = {"Authorization": "Bearer {shared_name}"}

        assert MCPService._replace_tokens(db, headers, owner_id)["Authorization"] == "Bearer OWNER_SECRET"

        with pytest.raises(ValidationException) as exc_info:
            MCPService._replace_tokens(db, headers, other_id)
        assert "Token not found" in str(exc_info.value)

    def test_replace_tokens_without_placeholder(self, db):
        import uuid

        user_id = str(uuid.uuid4())
        headers = {"KEY": "value without placeholder"}
        result = MCPService._replace_tokens(db, headers, user_id)

        assert result["KEY"] == "value without placeholder"


class TestTokenReplacementScope:
    """Substitution applies to headers only - not the endpoint URL."""

    def test_headers_are_substituted_endpoint_is_not(self, db):
        import uuid

        user_id = str(uuid.uuid4())
        _add_token(db, user_id, "api_key", "SECRET_A")

        config = MCPConfig(
            transport="sse",
            endpoint="https://mcp.example.com/sse?k={api_key}",
            headers={"Authorization": "Bearer {api_key}"},
        )
        out = MCPService._convert_config_to_mcp_client_format("r", config, db, user_id)["r"]

        assert out["headers"]["Authorization"] == "Bearer SECRET_A"
        assert out["url"] == "https://mcp.example.com/sse?k={api_key}"

    def test_no_db_or_user_skips_substitution(self, db):
        """Callers without a user context get the raw headers, unchanged."""
        config = MCPConfig(
            transport="sse",
            endpoint="https://mcp.example.com/sse",
            headers={"Authorization": "Bearer {api_key}"},
        )
        out = MCPService._convert_config_to_mcp_client_format("r", config)["r"]

        assert out["headers"]["Authorization"] == "Bearer {api_key}"


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
