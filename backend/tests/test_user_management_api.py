"""Tests for admin user management API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User, Role


class TestUserManagementEndpoints:
    """Test user management endpoints."""

    def test_create_user_as_admin_success(self, client: TestClient, db: Session, admin_user: User):
        """Test admin can create user successfully."""
        # Login as admin
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpassword123"
        })
        assert response.status_code == 200
        admin_token = response.json()["access_token"]

        # Get a role from database to assign
        role = db.query(Role).first()
        role_id = role.id if role else None

        response = client.post(
            "/api/v1/admin/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123",
                "role_ids": [role_id] if role_id else [],
                "is_active": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
