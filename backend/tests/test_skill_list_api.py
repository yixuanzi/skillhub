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


def skill_content(name: str, description: str = "Test skill description") -> str:
    """Build valid skill content.

    The skill service derives the skill name from the ``content`` YAML
    frontmatter and rejects content without it.
    """
    return f"---\nname: {name}\ndescription: {description}\n---\n\nSkill body for {name}."


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
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        # Clean up all data after each test using a fresh session
        cleanup_session = SessionLocal()
        try:
            cleanup_session.query(SkillList).delete()
            cleanup_session.query(RefreshToken).delete()
            cleanup_session.query(User).delete()
            cleanup_session.query(Permission).delete()
            cleanup_session.query(Role).delete()
            cleanup_session.commit()
        except Exception:
            cleanup_session.rollback()
        finally:
            cleanup_session.close()


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
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == "testuser").first()
    if existing_user:
        return existing_user

    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    AuthService.register(db, user_data)
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    user.is_active = True
    db.commit()
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
    AuthService.register(db, user_data)
    user = db.query(User).filter(User.username == "testuser2").first()
    assert user is not None
    user.is_active = True
    db.commit()
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}, user


class TestCreateSkill:
    """Tests for POST /api/v1/skills endpoint."""

    def test_create_skill_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test successful skill creation."""
        content = skill_content("test-skill")
        skill_data = {
            "name": "test-skill",
            "description": "Test skill description",
            "content": content,
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
        assert data["content"] == content
        # created_by is taken from the authenticated user, not from the payload
        assert data["created_by"] == test_user.username
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
            "content": skill_content("duplicate-skill"),
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
            "content": skill_content("unauthorized-skill"),
            "created_by": test_user.id
        }

        response = client.post("/api/v1/skills/", json=skill_data)

        # HTTPBearer returns 401 when no credentials provided
        assert response.status_code == 401

    def test_create_skill_minimal_data(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test creating skill with minimal required fields."""
        skill_data = {
            "name": "minimal-skill",
            "content": skill_content("minimal-skill"),
            "created_by": test_user.id
        }

        response = client.post("/api/v1/skills/", json=skill_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "minimal-skill"
        assert data["created_by"] == test_user.username
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
        skill2 = SkillList(name="author-skill-2", created_by=user2.id, tags="test,published")
        db.add_all([skill1, skill2])
        db.commit()

        response = client.get(f"/api/v1/skills/?author={user2.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["created_by"] == user2.id

    def test_list_skills_unauthenticated_only_returns_public(
        self, client: TestClient, db: SessionLocal, test_user: User
    ):
        """Unauthenticated callers are restricted to public skills."""
        db.add_all([
            SkillList(
                name="public-list-skill",
                created_by=test_user.id,
                tags="public,featured",
            ),
            SkillList(
                name="private-list-skill",
                created_by=test_user.id,
                tags="private",
            ),
            SkillList(
                name="publicity-list-skill",
                created_by=test_user.id,
                tags="publicity",
            ),
        ])
        db.commit()

        # No tags defaults to published, but anonymous visibility still wins.
        for url in ("/api/v1/skills/", "/api/v1/skills/?tags=private"):
            response = client.get(url)

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert [item["name"] for item in data["items"]] == [
                "public-list-skill"
            ]

    def test_list_skills_authenticated_visibility_and_explicit_tags(
        self,
        client: TestClient,
        auth_headers: dict,
        auth_headers_user2: tuple,
        test_user: User,
        db: SessionLocal,
    ):
        """Regular users see published skills or their own skills only."""
        _, user2 = auth_headers_user2
        db.add_all([
            SkillList(
                name="published-by-other",
                created_by=user2.id,
                tags="published",
            ),
            SkillList(
                name="draft-by-me",
                created_by=test_user.id,
                tags="draft",
            ),
            SkillList(
                name="draft-by-me-username",
                created_by=test_user.username,
                tags="draft",
            ),
            SkillList(
                name="draft-by-other",
                created_by=user2.id,
                tags="draft",
            ),
            SkillList(
                name="unpublished-by-other",
                created_by=user2.id,
                tags="unpublished",
            ),
        ])
        db.commit()

        response = client.get("/api/v1/skills/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert {item["name"] for item in data["items"]} == {
            "published-by-other",
            "draft-by-me",
            "draft-by-me-username",
        }

        # An explicit tag filter is combined with the visibility rule.
        response = client.get(
            "/api/v1/skills/?tags=draft", headers=auth_headers
        )
        assert response.status_code == 200
        assert {item["name"] for item in response.json()["items"]} == {
            "draft-by-me",
            "draft-by-me-username",
        }

        # Explicit published filtering does not include the user's draft.
        response = client.get(
            "/api/v1/skills/?tags=published", headers=auth_headers
        )
        assert response.status_code == 200
        assert [item["name"] for item in response.json()["items"]] == [
            "published-by-other"
        ]

    @pytest.mark.parametrize("role_name", ["admin", "super_admin"])
    def test_list_skills_admin_visibility(
        self,
        client: TestClient,
        db: SessionLocal,
        test_user: User,
        role_name: str,
    ):
        """Admins can list all skills, including unpublished skills."""
        admin_username = f"{role_name}-list-user"
        AuthService.register(
            db,
            UserCreate(
                username=admin_username,
                email=f"{admin_username}@example.com",
                password="adminpassword123",
            ),
        )
        admin_user = db.query(User).filter(User.username == admin_username).first()
        assert admin_user is not None
        admin_user.is_active = True
        admin_role = Role(name=role_name, description=f"{role_name} role")
        db.add(admin_role)
        db.commit()
        admin_user.roles.append(admin_role)
        db.commit()

        db.add_all([
            SkillList(
                name=f"{role_name}-draft",
                created_by=test_user.id,
                tags="draft",
            ),
            SkillList(
                name=f"{role_name}-private",
                created_by=test_user.id,
                tags="private",
            ),
        ])
        db.commit()

        token = create_access_token(
            data={"sub": admin_user.id, "username": admin_user.username}
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/skills/", headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 2

        response = client.get("/api/v1/skills/?tags=draft", headers=headers)
        assert response.status_code == 200
        assert [item["name"] for item in response.json()["items"]] == [
            f"{role_name}-draft"
        ]

    def test_list_skills_tags_default_is_published(self, client: TestClient):
        """The OpenAPI contract exposes published as the tags default."""
        schema = client.get("/openapi.json").json()
        parameters = schema["paths"]["/api/v1/skills/"]["get"]["parameters"]
        tags_parameter = next(parameter for parameter in parameters if parameter["name"] == "tags")
        assert tags_parameter["schema"]["default"] == "published"

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
            content=skill_content("get-test-skill"),
            created_by=test_user.username,
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
            content=skill_content("update-test-skill"),
            created_by=test_user.username
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
        skill1 = SkillList(
            name="update-original-1",
            content=skill_content("update-original-1"),
            created_by=test_user.username,
        )
        skill2 = SkillList(
            name="update-original-2",
            content=skill_content("update-original-2"),
            created_by=test_user.username,
        )
        db.add_all([skill1, skill2])
        db.commit()
        db.refresh(skill2)

        # Try to rename skill2 to skill1's name. The name follows the content
        # frontmatter, so the rename is expressed through new content.
        update_data = {"content": skill_content("update-original-1")}
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
            content=skill_content("all-fields-skill"),
            created_by=test_user.username,
            category="original",
            tags="original",
            version="1.0.0"
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)

        # Update all fields. The new name comes from the content frontmatter;
        # the "name" key in the payload is ignored by the service.
        new_content = skill_content("updated-all-fields-skill", "Updated description")
        update_data = {
            "name": "ignored-name",
            "description": "Updated description",
            "content": new_content,
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
        assert data["content"] == new_content
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
            content=skill_content("delete-test-skill"),
            created_by=test_user.username
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

        # HTTPBearer returns 401 when no credentials provided
        assert response.status_code == 401

        # Verify skill still exists
        deleted_skill = db.query(SkillList).filter(SkillList.id == skill.id).first()
        assert deleted_skill is not None
