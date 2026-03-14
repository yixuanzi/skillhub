# API Key Authentication Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace tmpkey authentication with API key authentication in the main authentication flow

**Architecture:** Modify `get_current_user()` in `core/deps.py` to check API keys (sk_ prefix) before JWT, remove all tmpkey-related code

**Tech Stack:** FastAPI, SQLAlchemy, Python 3.12+, pytest

---

## Task 1: Add API key tests to core/deps.py

**Files:**
- Test: `tests/test_deps.py` (create)
- Modify: `core/deps.py:1-93`

**Step 1: Write the failing test - API key authentication**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_deps.py::test_get_current_user_with_api_key -v`
Expected: FAIL with "module 'core.deps' has no attribute 'APIKeyService'" or similar

---

## Task 2: Import APIKeyService in core/deps.py

**Files:**
- Modify: `core/deps.py:1-10`

**Step 1: Add APIKeyService import**

```python
"""FastAPI dependency functions for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from core.security import verify_token
# from core.tmpkey_manager import get_user_id_by_tmpkey  # REMOVE THIS LINE
from services.api_key_service import APIKeyService  # ADD THIS LINE
```

**Step 2: Run test to verify it still fails**

Run: `pytest tests/test_deps.py::test_get_current_user_with_api_key -v`
Expected: FAIL with "no sk_ prefix handling" or similar

---

## Task 3: Implement API key authentication in get_current_user()

**Files:**
- Modify: `core/deps.py:13-76`

**Step 1: Rewrite get_current_user() to support API key auth**

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from API key or JWT token.

    支持两种认证方式:
    1. API Key (以 sk_ 开头)
    2. JWT token (标准Bearer token)

    Args:
        credentials: HTTP Bearer credentials (API key or JWT token)
        db: Database session

    Returns:
        Authenticated user object with auth_type attribute

    Raises:
        HTTPException 401: If token/api_key is invalid or user not found
    """
    token = credentials.credentials
    user = None
    auth_type = "unknown"

    # 首先尝试 API Key 认证 (sk_ 开头)
    if token.startswith("sk_"):
        api_key = APIKeyService.authenticate(db, token)
        if api_key:
            user = db.query(User).filter(User.id == api_key.user_id).first()
            if user:
                auth_type = "api_key"
                # 设置 API key 相关属性
                setattr(user, "auth_type", auth_type)
                setattr(user, "api_key_id", api_key.id)
                setattr(user, "api_key_scopes", api_key.scopes)
                setattr(user, "access_token", token)

                # 检查用户是否激活
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Inactive user",
                    )
                return user

    # 然后尝试 JWT token 认证
    if user is None:
        payload = verify_token(token)
        if payload is not None:
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                auth_type = "jwt"
                setattr(user, "auth_type", auth_type)
                setattr(user, "access_token", token)

                # 检查用户是否激活
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Inactive user",
                    )
                return user

    # 两种验证都失败
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_deps.py::test_get_current_user_with_api_key -v`
Expected: PASS

---

## Task 4: Add more API key test cases

**Files:**
- Test: `tests/test_deps.py`

**Step 1: Write tests for invalid API key**

```python
def test_get_current_user_with_invalid_api_key(db_session, create_user):
    """Test authentication with invalid API key falls back to JWT."""
    user = create_user(username="testuser", email="test@example.com")
    invalid_api_key = "sk_invalid_key"

    with patch('core.deps.APIKeyService') as mock_api_service:
        mock_api_service.authenticate.return_value = None  # Invalid key

        # Mock verify_token to return valid payload
        with patch('core.deps.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": str(user.id)}

            with patch('core.deps.security') as mock_security:
                mock_creds = Mock()
                mock_creds.credentials = invalid_api_key
                result = get_current_user(mock_creds, db_session)

                assert result.id == user.id
                assert result.auth_type == "jwt"
```

**Step 2: Write test for API key with inactive user**

```python
def test_get_current_user_api_key_inactive_user(db_session, create_user):
    """Test API key authentication with inactive user."""
    user = create_user(username="testuser", email="test@example.com")
    user.is_active = False
    db_session.commit()

    api_key = "sk_test1234567890abcdefghijklmnopqrstuvwxyz"

    with patch('core.deps.APIKeyService') as mock_api_service:
        mock_api_key = Mock()
        mock_api_key.user_id = str(user.id)
        mock_api_key.id = "api-key-id-123"
        mock_api_key.scopes = ["read"]
        mock_api_service.authenticate.return_value = mock_api_key

        with pytest.raises(HTTPException) as exc_info:
            with patch('core.deps.security') as mock_security:
                mock_creds = Mock()
                mock_creds.credentials = api_key
                get_current_user(mock_creds, db_session)

        assert exc_info.value.status_code == 403
        assert "Inactive user" in str(exc_info.value.detail)
```

**Step 3: Run all tests**

Run: `pytest tests/test_deps.py -v`
Expected: ALL PASS

---

## Task 5: Remove tmpkey import from auth_service.py

**Files:**
- Modify: `services/auth_service.py:1-263`

**Step 1: Remove tmpkey import and usage**

Find and remove:
```python
from core.tmpkey_manager import generate_tmpkey, store_tmpkey
```

Remove from `create_tokens()` method (around lines 152-154):
```python
# Generate and store tmpkey
tmpkey = generate_tmpkey()
store_tmpkey(tmpkey, str(user.id))
```

**Step 2: Remove tmpkey from TokenResponse return**

Modify the return statement in `create_tokens()` (around line 157):
```python
return TokenResponse(
    access_token=access_token,
    refresh_token=refresh_token,
    # tmpkey=tmpkey,  # REMOVE THIS LINE
    token_type="bearer",
    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
)
```

**Step 3: Commit**

```bash
git add services/auth_service.py
git commit -m "refactor: remove tmpkey generation and storage from auth service"
```

---

## Task 6: Update TokenResponse schema

**Files:**
- Modify: `schemas/auth.py`

**Step 1: Remove tmpkey field from TokenResponse**

```python
class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    # tmpkey: str  # REMOVE THIS LINE
    token_type: str = "bearer"
    expires_in: int
```

**Step 2: Run tests to verify**

Run: `pytest tests/ -v -k "token"`
Expected: Tests may fail if they reference tmpkey (fix in next steps)

**Step 3: Commit**

```bash
git add schemas/auth.py
git commit -m "refactor: remove tmpkey from TokenResponse schema"
```

---

## Task 7: Delete tmpkey_manager.py

**Files:**
- Delete: `core/tmpkey_manager.py`

**Step 1: Delete the file**

```bash
rm ~/Documents/workspace/skillhub/backend/core/tmpkey_manager.py
```

**Step 2: Check for any remaining imports**

Run: `grep -r "tmpkey_manager" backend/`
Expected: No results (or update remaining files)

**Step 3: Commit**

```bash
git add core/tmpkey_manager.py
git commit -m "refactor: remove tmpkey_manager module"
```

---

## Task 8: Update auth API endpoint response

**Files:**
- Modify: `api/auth.py`

**Step 1: Remove tmpkey from login response if hardcoded**

Check if there's any tmpkey-related code in the auth endpoints and remove it.

**Step 2: Run integration tests**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add api/auth.py
git commit -m "refactor: remove tmpkey references from auth API"
```

---

## Task 9: Integration test - End-to-end API key flow

**Files:**
- Test: `tests/integration/test_api_key_auth.py` (create)

**Step 1: Write integration test**

```python
# tests/integration/test_api_key_auth.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_key_authentication_flow(db_session, create_user):
    """Complete flow: create API key, use it to authenticate."""
    # Create user
    user = create_user(username="apiuser", email="api@example.com")

    # Create API key
    from services.api_key_service import APIKeyService
    from schemas.api_key import APIKeyCreate

    api_key_data = APIKeyCreate(
        name="Test Key",
        scopes=["read", "write"]
    )
    api_key_obj, full_key = APIKeyService.create(db_session, user, api_key_data)

    # Test authentication with API key
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {full_key}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "apiuser"
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_api_key_auth.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_api_key_auth.py
git commit -m "test: add API key authentication integration test"
```

---

## Task 10: Verify and cleanup

**Files:**
- All

**Step 1: Search for any remaining tmpkey references**

Run: `grep -r "tmpkey" backend/ --include="*.py"`
Expected: No results in production code (comments OK)

**Step 2: Run full test suite**

Run: `pytest tests/ -v --cov=backend`
Expected: All tests pass, coverage acceptable

**Step 3: Final commit**

```bash
git add .
git commit -m "feat: replace tmpkey authentication with API key authentication

- Add API key authentication to get_current_user()
- API keys (sk_ prefix) are checked before JWT
- Remove tmpkey generation, storage, and validation
- Update TokenResponse schema
- Add comprehensive tests for new auth flow

BREAKING CHANGE: tmpkey mechanism removed, use API keys or JWT

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary of Changes

1. **Modified**: `core/deps.py` - Added API key authentication to `get_current_user()`
2. **Modified**: `services/auth_service.py` - Removed tmpkey generation/storage
3. **Deleted**: `core/tmpkey_manager.py` - Entire file removed
4. **Modified**: `schemas/auth.py` - Removed `tmpkey` from `TokenResponse`
5. **Added**: `tests/test_deps.py` - API key authentication tests
6. **Added**: `tests/integration/test_api_key_auth.py` - Integration tests

## Authentication Order

1. Check if token starts with `sk_` → API key authentication
2. If API key fails → JWT authentication
3. If both fail → HTTP 401

## User Object Attributes

- `auth_type`: `"api_key"` or `"jwt"`
- `api_key_id`: API key UUID (only for API key auth)
- `api_key_scopes`: List of scopes (only for API key auth)
