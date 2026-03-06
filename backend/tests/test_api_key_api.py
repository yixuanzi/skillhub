"""Integration tests for API Key API endpoints.

This test suite covers:
- POST /api-keys/ - Create API key
- GET /api-keys/ - List API keys
- GET /api-keys/{id}/ - Get API key by ID
- PUT /api-keys/{id}/ - Update API key
- DELETE /api-keys/{id}/ - Revoke API key
- POST /api-keys/{id}/rotate - Rotate API key
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from models.user import User
from models.api_key import APIKey
from schemas.api_key import APIScope
from services.api_key_service import APIKeyService


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
                "name": "Test Key",
                "scopes": [APIScope.SKILLS_READ, APIScope.RESOURCES_READ]
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
        assert len(data["api_key"]["scopes"]) == 2

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
                "scopes": [APIScope.SKILLS_READ],
                "expires_at": expires_at
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["api_key"]["expires_at"] is not None

    def test_create_api_key_invalid_scope(self, client: TestClient, test_user: User):
        """Test creating API key with invalid scope fails."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Invalid Key",
                "scopes": ["invalid:scope"]
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "Invalid scopes" in response.json()["detail"]

    def test_create_api_key_unauthorized(self, client: TestClient):
        """Test creating API key without authentication fails."""
        response = client.post(
            "/api/v1/api-keys/",
            json={
                "name": "Test Key",
                "scopes": [APIScope.SKILLS_READ]
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
                "name": "",
                "scopes": [APIScope.SKILLS_READ]
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
            data = APIKeyCreate(name=f"Key {i}", scopes=[APIScope.SKILLS_READ])
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
            data = APIKeyCreate(name=f"Key {i}", scopes=[APIScope.SKILLS_READ])
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
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
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
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        response = client.get(f"/api/v1/api-keys/{created_key.id}/")
        assert response.status_code == 401


class TestAPIKeyUpdateEndpoint:
    """Test suite for PUT /api-keys/{id}/ endpoint."""

    def test_update_api_key_name(self, client: TestClient, test_user: User, db: Session):
        """Test updating API key name."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Old Name", scopes=[APIScope.SKILLS_READ])
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

    def test_update_api_key_scopes(self, client: TestClient, test_user: User, db: Session):
        """Test updating API key scopes."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"scopes": [APIScope.SKILLS_READ, APIScope.SKILLS_CALL]},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["scopes"]) == 2

    def test_update_api_key_deactivate(self, client: TestClient, test_user: User, db: Session):
        """Test deactivating API key via update."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
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

    def test_update_api_key_invalid_scopes(self, client: TestClient, test_user: User, db: Session):
        """Test updating with invalid scopes fails."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.put(
            f"/api/v1/api-keys/{created_key.id}/",
            json={"scopes": ["invalid:scope"]},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400

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


class TestAPIKeyRevokeEndpoint:
    """Test suite for DELETE /api-keys/{id}/ endpoint."""

    def test_revoke_api_key(self, client: TestClient, test_user: User, db: Session):
        """Test revoking an API key."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
        )

        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.delete(
            f"/api/v1/api-keys/{created_key.id}/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_revoke_api_key_not_found(self, client: TestClient, test_user: User):
        """Test revoking non-existent API key returns 404."""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.delete(
            "/api/v1/api-keys/non-existent-id/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestAPIKeyRotateEndpoint:
    """Test suite for POST /api-keys/{id}/rotate endpoint."""

    def test_rotate_api_key(self, client: TestClient, test_user: User, db: Session):
        """Test rotating an API key."""
        created_key, _ = APIKeyService.create(
            db, test_user,
            APIKeyCreate(name="Test Key", scopes=[APIScope.SKILLS_READ])
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
            APIKeyCreate(name="Admin Key", scopes=[APIScope.SKILLS_READ])
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
            APIKeyCreate(name="Admin Key", scopes=[APIScope.SKILLS_READ])
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

    def test_user_cannot_revoke_others_keys(self, client: TestClient, test_user: User, admin_user: User, db: Session):
        """Test users cannot revoke other users' API keys."""
        admin_key, _ = APIKeyService.create(
            db, admin_user,
            APIKeyCreate(name="Admin Key", scopes=[APIScope.SKILLS_READ])
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
