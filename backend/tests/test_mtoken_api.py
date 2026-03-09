"""Integration tests for mtoken API endpoints.

Tests the FastAPI endpoints for token CRUD operations.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app


client = TestClient(app)


class TestCreateMToken:
    """Tests for POST /api/v1/mtokens"""

    def test_create_mtoken_success(self, db: Session, auth_headers: dict):
        """Test successful token creation."""
        data = {
            "app_name": "GitHub",
            "key_name": "Personal Access Token",
            "value": "ghp_xxxxxxxxxxxxxxxxxxxx",
            "desc": "My GitHub token for API access"
        }

        response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["app_name"] == "GitHub"
        assert result["key_name"] == "Personal Access Token"
        assert result["value"] == "ghp_xxxxxxxxxxxxxxxxxxxx"
        assert result["created_by"] is not None
        assert "id" in result

    def test_create_mtoken_unauthorized(self, db: Session):
        """Test that creating token without auth returns 401/403."""
        data = {
            "app_name": "GitHub",
            "key_name": "Token",
            "value": "ghp_xxx"
        }

        response = client.post("/api/v1/mtokens/", json=data)

        assert response.status_code in [401, 403]


class TestListMTokens:
    """Tests for GET /api/v1/mtokens"""

    def test_list_mtokens_success(self, db: Session, auth_headers: dict):
        """Test successful token listing."""
        # Create some tokens first
        for i in range(3):
            data = {
                "app_name": f"App{i}",
                "key_name": f"Key{i}",
                "value": f"value{i}"
            }
            client.post("/api/v1/mtokens/", json=data, headers=auth_headers)

        response = client.get("/api/v1/mtokens/", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert result["total"] >= 3

    def test_list_mtokens_with_pagination(self, db: Session, auth_headers: dict):
        """Test listing tokens with pagination parameters."""
        response = client.get("/api/v1/mtokens/?page=1&size=10", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["page"] == 1
        assert result["size"] == 10

    def test_list_mtokens_with_app_filter(self, db: Session, auth_headers: dict):
        """Test filtering tokens by app name."""
        # Create tokens with different app names
        data1 = {
            "app_name": "GitHub",
            "key_name": "Token1",
            "value": "value1"
        }
        data2 = {
            "app_name": "OpenAI",
            "key_name": "Token2",
            "value": "value2"
        }
        client.post("/api/v1/mtokens/", json=data1, headers=auth_headers)
        client.post("/api/v1/mtokens/", json=data2, headers=auth_headers)

        response = client.get("/api/v1/mtokens/?app_name=GitHub", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert all(token["app_name"] == "GitHub" for token in result["items"])

    def test_list_mtokens_unauthorized(self, db: Session):
        """Test that listing tokens without auth returns 401/403."""
        response = client.get("/api/v1/mtokens/")
        assert response.status_code in [401, 403]

    def test_list_mtokens_user_isolation(self, db: Session, auth_headers_user1: dict, auth_headers_user2: dict, user1, user2):
        """Test that users only see their own tokens."""
        # Create token for user 1
        data1 = {
            "app_name": "GitHub",
            "key_name": "User1 Token",
            "value": "user1_value"
        }
        client.post("/api/v1/mtokens/", json=data1, headers=auth_headers_user1)

        # Create token for user 2
        data2 = {
            "app_name": "GitHub",
            "key_name": "User2 Token",
            "value": "user2_value"
        }
        client.post("/api/v1/mtokens/", json=data2, headers=auth_headers_user2)

        # User 1 lists their tokens
        response1 = client.get("/api/v1/mtokens/", headers=auth_headers_user1)
        tokens1 = response1.json()["items"]

        # User 2 lists their tokens
        response2 = client.get("/api/v1/mtokens/", headers=auth_headers_user2)
        tokens2 = response2.json()["items"]

        # User 1 should only see their token (created_by matches user1.id)
        assert all(token["created_by"] == str(user1.id) for token in tokens1)

        # User 2 should only see their token (created_by matches user2.id)
        assert all(token["created_by"] == str(user2.id) for token in tokens2)


class TestGetMToken:
    """Tests for GET /api/v1/mtokens/{id}"""

    def test_get_mtoken_found(self, db: Session, auth_headers: dict):
        """Test getting existing token by ID."""
        # Create a token first
        data = {
            "app_name": "GitHub",
            "key_name": "Test Token",
            "value": "ghp_test"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers)
        token_id = create_response.json()["id"]

        # Get the token
        response = client.get(f"/api/v1/mtokens/{token_id}", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == token_id
        assert result["app_name"] == "GitHub"

    def test_get_mtoken_not_found(self, db: Session, auth_headers: dict):
        """Test getting non-existent token returns 404."""
        response = client.get("/api/v1/mtokens/non-existent-id", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_mtoken_wrong_user(self, db: Session, auth_headers_user1: dict, auth_headers_user2: dict):
        """Test getting token created by another user."""
        # Create token for user 1
        data = {
            "app_name": "GitHub",
            "key_name": "User1 Token",
            "value": "user1_value"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers_user1)
        token_id = create_response.json()["id"]

        # User 2 tries to get user 1's token
        response = client.get(f"/api/v1/mtokens/{token_id}", headers=auth_headers_user2)

        assert response.status_code == 404


class TestUpdateMToken:
    """Tests for PUT /api/v1/mtokens/{id}"""

    def test_update_mtoken_success(self, db: Session, auth_headers: dict):
        """Test successful token update."""
        # Create a token first
        data = {
            "app_name": "GitHub",
            "key_name": "Old Name",
            "value": "old_value",
            "desc": "Old description"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers)
        token_id = create_response.json()["id"]

        # Update the token
        update_data = {
            "key_name": "New Name",
            "value": "new_value",
            "desc": "New description"
        }
        response = client.put(f"/api/v1/mtokens/{token_id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["key_name"] == "New Name"
        assert result["value"] == "new_value"
        assert result["desc"] == "New description"

    def test_update_mtoken_not_found(self, db: Session, auth_headers: dict):
        """Test updating non-existent token returns 404."""
        update_data = {"value": "new_value"}
        response = client.put("/api/v1/mtokens/non-existent-id", json=update_data, headers=auth_headers)

        assert response.status_code == 404

    def test_update_mtoken_wrong_user(self, db: Session, auth_headers_user1: dict, auth_headers_user2: dict):
        """Test updating token created by another user."""
        # Create token for user 1
        data = {
            "app_name": "GitHub",
            "key_name": "User1 Token",
            "value": "user1_value"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers_user1)
        token_id = create_response.json()["id"]

        # User 2 tries to update user 1's token
        update_data = {"value": "hacked_value"}
        response = client.put(f"/api/v1/mtokens/{token_id}", json=update_data, headers=auth_headers_user2)

        assert response.status_code == 404


class TestDeleteMToken:
    """Tests for DELETE /api/v1/mtokens/{id}"""

    def test_delete_mtoken_success(self, db: Session, auth_headers: dict):
        """Test successful token deletion."""
        # Create a token first
        data = {
            "app_name": "GitHub",
            "key_name": "Test Token",
            "value": "ghp_test"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers)
        token_id = create_response.json()["id"]

        # Delete the token
        response = client.delete(f"/api/v1/mtokens/{token_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/mtokens/{token_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_mtoken_not_found(self, db: Session, auth_headers: dict):
        """Test deleting non-existent token returns 404."""
        response = client.delete("/api/v1/mtokens/non-existent-id", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_mtoken_wrong_user(self, db: Session, auth_headers_user1: dict, auth_headers_user2: dict):
        """Test deleting token created by another user."""
        # Create token for user 1
        data = {
            "app_name": "GitHub",
            "key_name": "User1 Token",
            "value": "user1_value"
        }
        create_response = client.post("/api/v1/mtokens/", json=data, headers=auth_headers_user1)
        token_id = create_response.json()["id"]

        # User 2 tries to delete user 1's token
        response = client.delete(f"/api/v1/mtokens/{token_id}", headers=auth_headers_user2)

        assert response.status_code == 404
