"""Integration tests for authentication API endpoints.

This test suite covers the complete authentication flow through HTTP endpoints:
- User registration
- User login with JWT tokens
- Token refresh
- User logout
- Current user info retrieval
"""
import pytest
from fastapi.testclient import TestClient
from models.user import User, RefreshToken
from database import SessionLocal
from sqlalchemy.orm import Session


class TestRegistrationEndpoints:
    """Test suite for user registration endpoint."""

    def test_register_user(self, client: TestClient, db: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be in response

        # Verify user was created in database
        user = db.query(User).filter(User.username == "newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Already exists
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_short_password(self, client: TestClient):
        """Test registration fails with short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "shortpass",
                "email": "shortpass@example.com",
                "password": "short"  # Less than 8 characters
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client: TestClient):
        """Test registration fails with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "invalidemail",
                "email": "notanemail",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client: TestClient):
        """Test registration fails with missing required fields."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "incomplete"
                # Missing email and password
            }
        )

        assert response.status_code == 422  # Validation error


class TestLoginEndpoints:
    """Test suite for login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert len(data["access_token"]) > 32  # Full JWT token
        assert len(data["refresh_token"]) > 32  # Full JWT token

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login fails with incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid username or password" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails with non-existent username."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "invalid username or password" in response.json()["detail"].lower()

    def test_login_missing_fields(self, client: TestClient):
        """Test login fails with missing fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser"
                # Missing password
            }
        )

        assert response.status_code == 422  # Validation error


class TestCurrentUserEndpoint:
    """Test suite for current user endpoint."""

    def test_get_current_user(self, client: TestClient, test_user: User):
        """Test getting current user info with valid token."""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Now get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without token returns 403."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken123456789012345678"}
        )

        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, client: TestClient):
        """Test getting current user with malformed authorization header."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat token123"}
        )

        assert response.status_code == 403


class TestTokenRefreshEndpoint:
    """Test suite for token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First, login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Now refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert len(data["access_token"]) > 32  # Full JWT token

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh fails with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalidtoken123456789012345678"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()

    def test_refresh_token_expired(self, client: TestClient, db: Session):
        """Test refresh fails with expired token."""
        # Create a user
        from schemas.auth import UserCreate
        from services.auth_service import AuthService
        from datetime import datetime, timedelta, timezone
        from core.security import verify_token

        user_data = UserCreate(
            username="expiretest",
            email="expire@example.com",
            password="password123"
        )
        user = AuthService.register(db, user_data)

        # Create tokens
        tokens = AuthService.create_tokens(db, user)

        # Get jti from refresh token
        payload = verify_token(tokens.refresh_token)
        jti = payload.get("jti")

        # Manually expire the refresh token in database by jti
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.id == jti
        ).first()

        # Set token to expired
        refresh_token_record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()

        # Try to refresh with expired token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens.refresh_token}
        )

        # Should fail with 401
        assert response.status_code == 401

    def test_refresh_token_missing_field(self, client: TestClient):
        """Test refresh fails with missing refresh_token field."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={}  # Missing refresh_token
        )

        assert response.status_code == 422  # Validation error


class TestLogoutEndpoint:
    """Test suite for logout endpoint."""

    def test_logout_success(self, client: TestClient, test_user: User, db: Session):
        """Test successful logout invalidates token."""
        # First, login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Verify token exists in database (using string id)
        token_count_before = db.query(RefreshToken).filter(
            RefreshToken.user_id == str(test_user.id)
        ).count()
        assert token_count_before == 1

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 204
        assert response.content == b""  # No content response

        # Verify token was removed from database
        token_count_after = db.query(RefreshToken).filter(
            RefreshToken.user_id == str(test_user.id)
        ).count()
        assert token_count_after == 0

    def test_logout_invalid_token(self, client: TestClient):
        """Test logout with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "nonexistenttoken123456789012"}
        )

        assert response.status_code == 401

    def test_logout_missing_field(self, client: TestClient):
        """Test logout fails with missing refresh_token field."""
        response = client.post(
            "/api/v1/auth/logout",
            json={}  # Missing refresh_token
        )

        assert response.status_code == 422  # Validation error

    def test_logout_then_refresh_fails(self, client: TestClient, test_user: User):
        """Test that refresh fails after logout."""
        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token}
        )
        assert logout_response.status_code == 204

        # Try to refresh with logged out token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        # Should fail - token was deleted
        assert refresh_response.status_code == 401


class TestCompleteAuthFlow:
    """Integration tests for complete authentication flows."""

    def test_complete_registration_login_flow(self, client: TestClient):
        """Test complete registration -> login -> get current user flow."""
        # 1. Register new user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "flowuser",
                "email": "flow@example.com",
                "password": "flowpassword123"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["username"] == "flowuser"

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "flowuser",
                "password": "flowpassword123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # 3. Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["username"] == "flowuser"
        assert me_data["email"] == "flow@example.com"

    def test_complete_login_refresh_logout_flow(self, client: TestClient, test_user: User):
        """Test complete login -> refresh -> logout flow."""
        # 1. Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 2. Use access token to access protected endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 200

        # 3. Refresh access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

        # 4. Use new access token
        me_response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert me_response2.status_code == 200

        # 5. Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert logout_response.status_code == 204

        # 6. Verify refresh token no longer works
        refresh_after_logout = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_after_logout.status_code == 401

    def test_multiple_sessions_same_user(self, client: TestClient, test_user: User, db: Session):
        """Test that user can have multiple active sessions."""
        # 1. Create first session
        login1_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login1_response.status_code == 200
        tokens1 = login1_response.json()

        # 2. Create second session
        login2_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login2_response.status_code == 200
        tokens2 = login2_response.json()

        # 3. Verify both tokens work
        me1_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens1['access_token']}"}
        )
        assert me1_response.status_code == 200

        me2_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens2['access_token']}"}
        )
        assert me2_response.status_code == 200

        # 4. Verify 2 refresh tokens in database (using string id)
        token_count = db.query(RefreshToken).filter(
            RefreshToken.user_id == str(test_user.id)
        ).count()
        assert token_count == 2

        # 5. Logout first session
        logout1_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens1["refresh_token"]}
        )
        assert logout1_response.status_code == 204

        # 6. Verify second session still works
        me_after_logout = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens2['access_token']}"}
        )
        assert me_after_logout.status_code == 200

        # 7. Verify 1 refresh token remains
        token_count_after = db.query(RefreshToken).filter(
            RefreshToken.user_id == str(test_user.id)
        ).count()
        assert token_count_after == 1


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_login_with_case_sensitive_username(self, client: TestClient, test_user: User):
        """Test that username is case sensitive."""
        # Try login with different case
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "TestUser",  # Different case
                "password": "testpassword123"
            }
        )

        # Should fail (username is case sensitive)
        assert response.status_code == 401

    def test_register_with_username_validation(self, client: TestClient):
        """Test username validation (min length)."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Less than 3 characters
                "email": "test@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_multiple_failed_logins(self, client: TestClient, test_user: User):
        """Test multiple failed login attempts."""
        # Attempt multiple failed logins
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": "testuser",
                    "password": f"wrongpassword{i}"
                }
            )
            assert response.status_code == 401

        # Verify correct password still works
        # (no rate limiting in MVP, but good to verify)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
