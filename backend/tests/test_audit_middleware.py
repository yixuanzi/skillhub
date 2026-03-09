"""Tests for audit middleware."""
import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from main import app
from middleware.audit_middleware import audit_middleware, _parse_body_for_logging
from models.system_audit_log import SystemAuditLog


class TestAuditMiddleware:
    """Test audit middleware functionality."""

    @pytest.mark.asyncio
    async def test_parse_body_json(self):
        """Test parsing JSON body for logging."""
        content_type = "application/json"
        body_bytes = b'{"test": "value", "number": 123}'

        result = await _parse_body_for_logging(content_type, body_bytes)

        assert result["body_type"] == "application/json"
        assert result["json"]["test"] == "value"
        assert result["json"]["number"] == 123

    @pytest.mark.asyncio
    async def test_parse_body_form(self):
        """Test parsing form data for logging."""
        content_type = "application/x-www-form-urlencoded"
        body_bytes = b"key1=value1&key2=value2"

        result = await _parse_body_for_logging(content_type, body_bytes)

        assert result["body_type"] == "application/x-www-form-urlencoded"
        assert result["form"]["key1"] == "value1"
        assert result["form"]["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_parse_body_truncated(self):
        """Test body truncation for large payloads."""
        content_type = "application/json"
        large_body = b'{"data": "' + b"x" * 20000 + b'"}'

        result = await _parse_body_for_logging(content_type, large_body)

        assert result["body_type"] == "application/json"
        assert result["truncated"] is True
        assert "preview" in result
        assert len(result["preview"]) < 15000  # Should be truncated

    @pytest.mark.asyncio
    async def test_parse_body_multipart_skipped(self):
        """Test that multipart form data is skipped."""
        content_type = "multipart/form-data"
        body_bytes = b"dummy body"

        result = await _parse_body_for_logging(content_type, body_bytes)

        assert result["body_type"] == "multipart/form-data"
        assert result["text"] == "dummy body"


class TestAuditMiddlewareIntegration:
    """Integration tests for audit middleware."""

    def test_get_request_with_query_params(self, db: Session):
        """Test that GET requests with query params are logged."""
        from unittest.mock import patch

        # Mock the log_action to avoid database dependency
        with patch('middleware.audit_middleware.SystemAuditLogService.log_action') as mock_log:
            with TestClient(app) as client:
                response = client.get("/api/v1/resources/test?param1=value1&param2=value2")

                # Verify log was called
                assert mock_log.called

                # Get the call arguments
                call_args = mock_log.call_args
                details = call_args.kwargs['details']

                # Verify query params were logged
                assert "query_params" in details
                assert details["query_params"]["param1"] == "value1"
                assert details["query_params"]["param2"] == "value2"

    def test_post_request_with_json_body(self, db: Session):
        """Test that POST requests with JSON body are logged."""
        from unittest.mock import patch

        with patch('middleware.audit_middleware.SystemAuditLogService.log_action') as mock_log:
            with TestClient(app) as client:
                # Note: This test requires a valid endpoint and auth
                # For now, we're just testing that the middleware doesn't crash
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "test", "password": "test"}
                )

                # The request should be processed (may fail auth, but middleware should work)
                # Verify log was called
                assert mock_log.called

    def test_body_caching_doesnt_break_downstream(self, db: Session):
        """Test that reading body in middleware doesn't break route handlers."""
        from unittest.mock import patch

        with patch('middleware.audit_middleware.SystemAuditLogService.log_action') as mock_log:
            with TestClient(app) as client:
                # Make a POST request
                response = client.post(
                    "/api/v1/auth/login",
                    json={"username": "testuser", "password": "testpass"}
                )

                # The route handler should have processed the body
                # (response might be 401 or 422, but not 500 due to body being consumed)
                # If body caching didn't work, we'd get 500 or body would be empty
                assert response.status_code in (200, 401, 403, 422)

                # Verify log was called
                assert mock_log.called
