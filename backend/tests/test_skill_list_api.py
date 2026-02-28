"""Integration tests for Skill List API endpoints.

This module contains tests for skill market CRUD operations including:
- Creating skills (POST /api/v1/skills)
- Listing skills with pagination and filtering (GET /api/v1/skills)
- Getting skills by ID (GET /api/v1/skills/{id})
- Updating skills (PUT /api/v1/skills/{id})
- Deleting skills (DELETE /api/v1/skills/{id})
"""
import pytest
from fastapi.testclient import TestClient
from database import Base, engine, SessionLocal
from models.user import User, RefreshToken, Role, Permission
from models.skill_list import SkillList
from schemas.auth import UserCreate
from schemas.skill_list import SkillListCreate, SkillListUpdate
from services.auth_service import AuthService
from core.security import create_access_token
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before running tests"""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        # Clean up all data after each test
        session = SessionLocal()
        session.query(SkillList).delete()
        session.query(RefreshToken).delete()
        session.query(User).delete()
        session.query(Permission).delete()
        session.query(Role).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    from database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: SessionLocal):
    """Create a test user fixture."""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = AuthService.register(db, user_data)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User):
    """Create authentication headers for test user."""
    access_token = create_access_token(
        data={"sub": test_user.id, "username": test_user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_headers_user2(db: SessionLocal):
    """Create authentication headers for second test user."""
    user_data = UserCreate(
        username="testuser2",
        email="test2@example.com",
        password="testpassword123"
    )
    user = AuthService.register(db, user_data)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}, user


class TestCreateSkill:
    """Tests for POST /api/v1/skills endpoint."""

    def test_create_skill_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test successful skill creation."""
        skill_data = {
            "name": "test-skill",
            "description": "Test skill description",
            "content": "Test skill content",
            "created_by": test_user.id,
            "category": "data-processing",
            "tags": "test,api,automation",
            "version": "1.0.0"
        }

        response = client.post("/api/v1/skills/", json=skill_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-skill"
        assert data["description"] == "Test skill description"
        assert data["content"] == "Test skill content"
        assert data["created_by"] == test_user.id
        assert data["category"] == "data-processing"
        assert data["tags"] == "test,api,automation"
        assert data["version"] == "1.0.0"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_skill_duplicate_name(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test that duplicate skill names are rejected."""
        skill_data = {
            "name": "duplicate-skill",
            "created_by": test_user.id
        }

        # Create first skill
        response1 = client.post("/api/v1/skills/", json=skill_data, headers=auth_headers)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/v1/skills/", json=skill_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_skill_unauthorized(self, client: TestClient, test_user: User):
        """Test that creating skill without authentication fails."""
        skill_data = {
            "name": "unauthorized-skill",
            "created_by": test_user.id
        }

        response = client.post("/api/v1/skills/", json=skill_data)

        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    def test_create_skill_minimal_data(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test creating skill with minimal required fields."""
        skill_data = {
            "name": "minimal-skill",
            "created_by": test_user.id
        }

        response = client.post("/api/v1/skills/", json=skill_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "minimal-skill"
        assert data["created_by"] == test_user.id
        assert data["version"] == "1.0.0"  # Default version


class TestListSkills:
    """Tests for GET /api/v1/skills endpoint."""

    def test_list_skills_success(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test successful skill listing."""
        # Create test skills
        for i in range(3):
            skill = SkillList(
                name=f"list-test-{i}",
                description=f"Test skill {i}",
                created_by=test_user.id,
                category="test"
            )
            db.add(skill)
        db.commit()

        response = client.get("/api/v1/skills/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) >= 3
        assert data["page"] == 1
        assert data["size"] == 20

    def test_list_skills_pagination(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test skill listing with pagination."""
        # Create 25 skills
        for i in range(25):
            skill = SkillList(
                name=f"page-skill-{i}",
                created_by=test_user.id
            )
            db.add(skill)
        db.commit()

        # Get first page
        response1 = client.get("/api/v1/skills/?page=1&size=10", headers=auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 10
        assert data1["page"] == 1
        assert data1["size"] == 10
        assert data1["total"] >= 25

        # Get second page
        response2 = client.get("/api/v1/skills/?page=2&size=10", headers=auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 10
        assert data2["page"] == 2

    def test_list_skills_category_filter(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test filtering skills by category."""
        # Create skills in different categories
        skill1 = SkillList(name="cat-skill-1", created_by=test_user.id, category="data-processing")
        skill2 = SkillList(name="cat-skill-2", created_by=test_user.id, category="data-processing")
        skill3 = SkillList(name="cat-skill-3", created_by=test_user.id, category="ai-llm")
        db.add_all([skill1, skill2, skill3])
        db.commit()

        response = client.get("/api/v1/skills/?category=data-processing", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["category"] == "data-processing"

    def test_list_skills_tags_filter(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test filtering skills by tags."""
        # Create skills with different tags
        skill1 = SkillList(name="tag-skill-1", created_by=test_user.id, tags="python,api")
        skill2 = SkillList(name="tag-skill-2", created_by=test_user.id, tags="python,automation")
        skill3 = SkillList(name="tag-skill-3", created_by=test_user.id, tags="javascript,api")
        db.add_all([skill1, skill2, skill3])
        db.commit()

        response = client.get("/api/v1/skills/?tags=python", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Should match skills with "python" in tags
        assert len(data["items"]) == 2

    def test_list_skills_author_filter(self, client: TestClient, auth_headers: dict, auth_headers_user2: tuple, db: SessionLocal):
        """Test filtering skills by author (created_by)."""
        headers_user2, user2 = auth_headers_user2

        # Create skills by different users
        skill1 = SkillList(name="author-skill-1", created_by="user-1-id", tags="test")
        skill2 = SkillList(name="author-skill-2", created_by=user2.id, tags="test")
        db.add_all([skill1, skill2])
        db.commit()

        response = client.get(f"/api/v1/skills/?author={user2.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["created_by"] == user2.id

    def test_list_skills_unauthorized(self, client: TestClient):
        """Test that listing skills without authentication fails."""
        response = client.get("/api/v1/skills/")

        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    def test_list_empty_skills(self, client: TestClient, auth_headers: dict):
        """Test listing skills when none exist."""
        response = client.get("/api/v1/skills/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestGetSkill:
    """Tests for GET /api/v1/skills/{id} endpoint."""

    def test_get_skill_found(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test getting an existing skill."""
        # Create skill
        skill = SkillList(
            name="get-test-skill",
            description="Test description",
            created_by=test_user.id,
            category="test"
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        response = client.get(f"/api/v1/skills/{skill.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == skill.id
        assert data["name"] == "get-test-skill"
        assert data["description"] == "Test description"
        assert data["category"] == "test"

    def test_get_skill_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent skill."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/skills/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_skill_invalid_id(self, client: TestClient, auth_headers: dict):
        """Test getting skill with invalid ID format."""
        response = client.get("/api/v1/skills/invalid-id", headers=auth_headers)

        # Should return 404 or 422 depending on validation
        assert response.status_code in [404, 422]


class TestUpdateSkill:
    """Tests for PUT /api/v1/skills/{id} endpoint."""

    def test_update_skill_success(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test successful skill update."""
        # Create skill
        skill = SkillList(
            name="update-test-skill",
            description="Original description",
            created_by=test_user.id
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        # Update skill
        update_data = {
            "description": "Updated description",
            "category": "updated-category",
            "tags": "updated,tags"
        }
        response = client.put(
            f"/api/v1/skills/{skill.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == skill.id
        assert data["name"] == "update-test-skill"  # Name unchanged
        assert data["description"] == "Updated description"
        assert data["category"] == "updated-category"
        assert data["tags"] == "updated,tags"

    def test_update_skill_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating a non-existent skill."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"description": "Updated"}

        response = client.put(
            f"/api/v1/skills/{fake_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_skill_duplicate_name(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test updating skill to duplicate name."""
        # Create two skills
        skill1 = SkillList(name="update-original-1", created_by=test_user.id)
        skill2 = SkillList(name="update-original-2", created_by=test_user.id)
        db.add_all([skill1, skill2])
        db.commit()
        db.refresh(skill2)

        # Try to update skill2 to have same name as skill1
        update_data = {"name": "update-original-1"}
        response = client.put(
            f"/api/v1/skills/{skill2.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_update_skill_all_fields(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test updating all skill fields."""
        # Create skill
        skill = SkillList(
            name="all-fields-skill",
            description="Original",
            content="Original content",
            created_by=test_user.id,
            category="original",
            tags="original",
            version="1.0.0"
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        # Update all fields
        update_data = {
            "name": "updated-all-fields-skill",
            "description": "Updated description",
            "content": "Updated content",
            "category": "updated",
            "tags": "updated,tags",
            "version": "2.0.0"
        }
        response = client.put(
            f"/api/v1/skills/{skill.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-all-fields-skill"
        assert data["description"] == "Updated description"
        assert data["content"] == "Updated content"
        assert data["category"] == "updated"
        assert data["tags"] == "updated,tags"
        assert data["version"] == "2.0.0"


class TestDeleteSkill:
    """Tests for DELETE /api/v1/skills/{id} endpoint."""

    def test_delete_skill_success(self, client: TestClient, auth_headers: dict, test_user: User, db: SessionLocal):
        """Test successful skill deletion."""
        # Create skill
        skill = SkillList(
            name="delete-test-skill",
            created_by=test_user.id
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        # Delete skill
        response = client.delete(f"/api/v1/skills/{skill.id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

        # Verify skill is deleted
        deleted_skill = db.query(SkillList).filter(SkillList.id == skill.id).first()
        assert deleted_skill is None

    def test_delete_skill_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting a non-existent skill."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/skills/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_skill_unauthorized(self, client: TestClient, test_user: User, db: SessionLocal):
        """Test that deleting skill without authentication fails."""
        # Create skill
        skill = SkillList(
            name="unauthorized-delete-skill",
            created_by=test_user.id
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        # Try to delete without auth
        response = client.delete(f"/api/v1/skills/{skill.id}")

        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

        # Verify skill still exists
        deleted_skill = db.query(SkillList).filter(SkillList.id == skill.id).first()
        assert deleted_skill is not None
