# tests/test_deps.py
import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from core.deps import get_current_user
from models.user import User


def test_get_current_user_with_api_key(db_session, create_user):
    """Test authentication with valid API key."""
    user = create_user(username="testuser", email="test@example.com")
    api_key = "sk_test1234567890abcdefghijklmnopqrstuvwxyz"

    with patch('core.deps.APIKeyService') as mock_api_service:
        mock_api_key = Mock()
        mock_api_key.user_id = str(user.id)
        mock_api_key.id = "api-key-id-123"
        mock_api_key.scopes = ["read", "write"]
        mock_api_service.authenticate.return_value = mock_api_key

        # Mock credentials
        with patch('core.deps.security') as mock_security:
            mock_creds = Mock()
            mock_creds.credentials = api_key
            result = get_current_user(mock_creds, db_session)

            assert result.id == user.id
            assert result.auth_type == "api_key"
            assert result.api_key_id == "api-key-id-123"
            assert result.api_key_scopes == ["read", "write"]
