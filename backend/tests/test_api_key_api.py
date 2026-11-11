"""Integration tests for API Key API endpoints.

This test suite covers:
- POST /api-keys/ - Create API key
- GET /api-keys/ - List API keys
- GET /api-keys/{id}/ - Get API key by ID
- PUT /api-keys/{id}/ - Update API key
- DELETE /api-keys/{id}/ - Delete API key
- POST /api-keys/{id}/rotate - Rotate API key
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from models.user import User
from models.api_key import APIKey
from schemas.api_key import APIKeyCreate
from services.api_key_service import APIKeyService
from core.security import create_access_token


def active_user_headers(user: User) -> dict[str, str]:
    """Build JWT headers for an active test user."""
    token = create_access_token(data={"sub": user.id, "username": user.username})
    return {"Authorization": f"Bearer {token}"}


class TestAPIKeyCreateEndpoint:
    """Test suite for POST /api-keys/ endpoint."""

    def test_create_api_key_success(self, client: TestClient, test_user: User):
        """Test successful API key creation."""
        # Login as test user
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test Key"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201

        data = response.json()
        assert "key" in data  # Full key only returned once
        assert data["key"].startswith("sk_")
        assert data["api_key"]["name"] == "Test Key"
        assert data["api_key"]["key_prefix"] == data["key"][:10]
        assert data["api_key"]["is_active"] is True
        assert "scopes" not in data["api_key"]

    def test_create_api_key_with_expiration(self, client: TestClient, test_user: User):
        """Test creating API key with expiration date."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Expiring Key",
                "expires_at": expires_at
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["api_key"]["expires_at"] is not None

    def test_create_api_key_unauthorized(self, client: TestClient):
        """Test creating API key without authentication fails."""
        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test Key"
            }
        )

        assert response.status_code == 401

    def test_create_api_key_empty_name(self, client: TestClient, test_user: User):
        """Test creating API key with empty name fails."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": ""
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422  # Validation error


class TestAPIKeyListEndpoint:
    """Test suite for GET /api-keys/ endpoint."""

    def test_list_api_keys_empty(self, client: TestClient, test_user: User):
        """Test listing API keys when user has none."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_api_keys_with_keys(self, client: TestClient, test_user: User, db: Session):
        """Test listing API keys returns user's keys only."""
        # Create some keys
        for i in range(3):
            data = APIKeyCreate(name=f"Key {i}")
            APIKeyService.create(db, test_user, data)

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        keys = response.json()
        assert len(keys) == 3

    def test_list_api_keys_pagination(self, client: TestClient, test_user: User, db: Session):
        """Test pagination of API key listing."""
        # Create 5 keys
        for i in range(5):
            data = APIKeyCreate(name=f"Key {i}")
            APIKeyService.create(db, test_user, data)

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # First page
        response = client.get(
            "/api/v1/api-keys/?skip=0&limit=3",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 3

        # Second page
        response = client.get(
            "/api/v1/api-keys/?skip=3&limit=3",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_api_keys_unauthorized(self, client: TestClient):
        """Test listing API keys without authentication fails."""
        response = client.get("/api/v1/api-keys/")
        assert response.status_code == 401


class TestAPIKeyGetEndpoint:
    """Test suite for GET /api-keys/{id}/ endpoint."""

    def test_get_api_key_found(self, client: TestClient, test_user: User, db: Session):
        """Test getting API key by ID."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            f"/api/v1/api-keys/{created_key.id}/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_key.id
        assert data["name"] == "Test Key"
        assert "key" not in data  # Full key not returned

    def test_get_api_key_not_found(self, client: TestClient, test_user: User):
        """Test getting non-existent API key returns 404."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/api-keys/non-existent-id/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_get_api_key_unauthorized(self, client: TestClient, test_user: User, db: Session):
        """Test getting API key without authentication fails."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key")
        )

        response = client.get(f"/api/v1/api-keys/{created_key.id}/")
        assert response.status_code == 401


class TestAPIKeyUpdateEndpoint:
    """Test suite for PUT /api-keys/{id}/ endpoint."""

    def test_update_api_key_name(self, client: TestClient, test_user: User, db: Session):
        """Test updating API key name."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Old Name")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    def test_update_api_key_deactivate(self, client: TestClient, test_user: User, db: Session):
        """Test deactivating API key via update."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_api_key_not_found(self, client: TestClient, test_user: User):
        """Test updating non-existent API key returns 404."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            "/api/v1/api-keys/non-existent-id/",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestAPIKeyToggleEndpoint:
    """Test suite for enabling and disabling API keys."""

    def test_toggle_api_key_active_state(self, client: TestClient, create_user, db: Session):
        """Test disabling a key and enabling it again through the API."""
        user = create_user("api-key-toggle", "api-key-toggle@example.com")
        created_key, _ = APIKeyService.create(
            db, user,
            APIKeyCreate(name="Toggle Key")
        )
        headers = active_user_headers(user)

        disable_response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"is_active": False},
            headers=headers
        )
        enable_response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"is_active": True},
            headers=headers
        )

        assert disable_response.status_code == 200
        assert disable_response.json()["is_active"] is False
        assert enable_response.status_code == 200
        assert enable_response.json()["is_active"] is True


class TestAPIKeyDeleteEndpoint:
    """Test suite for DELETE /api-keys/{id}/ endpoint."""

    def test_delete_api_key(self, client: TestClient, create_user, db: Session):
        """Test permanently deleting an API key."""
        user = create_user("api-key-delete", "api-key-delete@example.com")
        created_key, _ = APIKeyService.create(
            db, user,
            APIKeyCreate(name="Test Key")
        )

        response = client.delete(
            f"/api/v1/api-keys/{created_key.id}/",
            headers=active_user_headers(user)
        )

        assert response.status_code == 204
        assert response.content == b""
        assert db.query(APIKey).filter(APIKey.id == created_key.id).first() is None

    def test_delete_api_key_not_found(self, client: TestClient, create_user):
        """Test deleting a non-existent API key returns 404."""
        user = create_user("api-key-delete-missing", "api-key-delete-missing@example.com")

        response = client.delete(
            "/api/v1/api-keys/non-existent-id/",
            headers=active_user_headers(user)
        )

        assert response.status_code == 404


class TestAPIKeyRotateEndpoint:
    """Test suite for POST /api-keys/{id}/rotate endpoint."""

    def test_rotate_api_key(self, client: TestClient, test_user: User, db: Session):
        """Test rotating an API key."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.post(
            f"/api/v1/api-keys/{created_key.id}/rotate",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["key"].startswith("sk_")
        assert data["api_key"]["key_prefix"] == data["key"][:10]
        assert data["api_key"]["name"] == "Test Key"

    def test_rotate_api_key_not_found(self, client: TestClient, test_user: User):
        """Test rotating non-existent API key returns 404."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/api-keys/non-existent-id/rotate",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestAPIKeyUserIsolation:
    """Test suite for user isolation in API key operations."""

    def test_user_cannot_see_others_keys(self, client: TestClient, test_user: User, admin_user: User, db: Session):
        """Test users can only see their own API keys."""
        # Create key for admin user
        admin_key, _ = APIKeyService.create(
            db, admin_user,
            APIKeyCreate(name="Admin Key")
        )

        # Login as test user
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Try to get admin's key
        response = client.get(
            f"/api/v1/api-keys/{admin_key.id}/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_user_cannot_update_others_keys(self, client: TestClient, test_user: User, admin_user: User, db: Session):
        """Test users cannot update other users' API keys."""
        admin_key, _ = APIKeyService.create(
            db, admin_user,
            APIKeyCreate(name="Admin Key")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/api-keys/{admin_key.id}/",
            json={"name": "Hacked Name"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_user_cannot_delete_others_keys(self, client: TestClient, test_user: User, admin_user: User, db: Session):
        """Test users cannot delete other users' API keys."""
        admin_key, _ = APIKeyService.create(
            db, admin_user,
            APIKeyCreate(name="Admin Key")
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.delete(
            f"/api/v1/api-keys/{admin_key.id}/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestAPIKeyIsItsOwner:
    """A key carries no permissions of its own: a request made with it is its user."""

    def test_key_has_no_scopes(self, client: TestClient, auth_headers: dict):
        """Scopes are gone; a payload from an older client that still sends them is accepted."""
        response = client.post(
            "/api/v1/api-keys/",
            json={"name": "Legacy Client Key", "scopes": ["skills:read"]},
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert "scopes" not in response.json()["api_key"]

        listed = client.get("/api/v1/api-keys/", headers=auth_headers).json()
        assert all("scopes" not in key for key in listed)

    def test_key_reaches_what_its_user_reaches(self, client: TestClient, test_user: User, admin_user: User, db: Session):
        """The same request succeeds or fails depending only on whose key it is."""
        _, admin_key = APIKeyService.create(db, admin_user, APIKeyCreate(name="Admin Key"))
        _, user_key = APIKeyService.create(db, test_user, APIKeyCreate(name="User Key"))

        as_admin = client.get("/api/v1/admin/users/list/", headers={"Authorization": f"Bearer {admin_key}"})
        as_user = client.get("/api/v1/admin/users/list/", headers={"Authorization": f"Bearer {user_key}"})

        assert as_admin.status_code == 200
        assert as_user.status_code == 403

    def test_key_identifies_its_user(self, client: TestClient, test_user: User, db: Session):
        _, key = APIKeyService.create(db, test_user, APIKeyCreate(name="Me"))

        response = client.get("/api/v1/auth/me/", headers={"Authorization": f"Bearer {key}"})

        assert response.status_code == 200
        assert response.json()["username"] == test_user.username


class TestLegacyScopesColumn:
    """database.drop_api_key_scopes: upgrading a database created before scopes were removed."""

    def test_column_is_dropped_and_rows_are_kept(self, tmp_path):
        from sqlalchemy import create_engine, inspect, text
        from database import drop_api_key_scopes

        legacy = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
        with legacy.begin() as connection:
            # NOT NULL with no default, as the old model created it: without
            # the drop, inserting a key without scopes would fail.
            connection.execute(text(
                "CREATE TABLE api_keys (id VARCHAR(36) PRIMARY KEY, name VARCHAR(255) NOT NULL, scopes JSON NOT NULL)"
            ))
            connection.execute(text("INSERT INTO api_keys VALUES ('k1', 'old key', '[\"skills:read\"]')"))

        assert drop_api_key_scopes(legacy) is True

        assert [column["name"] for column in inspect(legacy).get_columns("api_keys")] == ["id", "name"]
        with legacy.begin() as connection:
            assert connection.execute(text("SELECT id, name FROM api_keys")).all() == [("k1", "old key")]
            connection.execute(text("INSERT INTO api_keys (id, name) VALUES ('k2', 'new key')"))

        # Nothing left to do the second time.
        assert drop_api_key_scopes(legacy) is False
