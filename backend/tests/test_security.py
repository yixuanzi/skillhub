"""Tests for security module functions."""
import pytest
from core.security import (
    pwd_context,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_token_last32,
    verify_token
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = get_password_hash(password)

    # Hash should be different from password
    assert hashed != password

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify wrong password
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Test JWT access token creation."""
    data = {"sub": "user-id-123", "username": "testuser"}
    token = create_access_token(data)

    # Token should be a non-empty string
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 32

    # Token should have 3 parts (header.payload.signature)
    parts = token.split(".")
    assert len(parts) == 3


def test_create_refresh_token():
    """Test JWT refresh token creation."""
    data = {"sub": "user-id-123", "username": "testuser"}
    token = create_refresh_token(data)

    # Token should be a non-empty string
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 32


def test_get_token_last32():
    """Test extracting last 32 characters of token."""
    data = {"sub": "user-id-123"}
    token = create_access_token(data)
    last32 = get_token_last32(token)

    # Should return exactly 32 characters
    assert len(last32) == 32

    # Should match last 32 of full token
    assert last32 == token[-32:]


def test_verify_token_success():
    """Test successful token verification."""
    data = {"sub": "user-id-123", "username": "testuser"}
    token = create_access_token(data)

    payload = verify_token(token)

    # Should return decoded payload
    assert payload is not None
    assert payload["sub"] == "user-id-123"
    assert payload["username"] == "testuser"


def test_verify_token_invalid():
    """Test token verification with invalid token."""
    # Invalid token
    payload = verify_token("invalid.token.here")
    assert payload is None

    # Truncated token (32 chars)
    payload = verify_token("a" * 32)
    assert payload is None


def test_verify_token_expired():
    """Test token verification with expired token."""
    from datetime import timedelta, timezone, datetime
    from jose import jwt

    # Create expired token
    expired_data = {
        "sub": "user-id-123",
        "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()
    }
    expired_token = jwt.encode(expired_data, "your-secret-key-change-in-production", algorithm="HS256")

    payload = verify_token(expired_token)
    assert payload is None


def test_access_token_contains_exp():
    """Test that access token has expiration claim."""
    data = {"sub": "user-id-123"}
    token = create_access_token(data)

    payload = verify_token(token)
    assert payload is not None
    assert "exp" in payload
