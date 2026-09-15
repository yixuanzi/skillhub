"""Unit tests for SkillListService module.

This module contains tests for skill CRUD operations including:
- Creating skills
- Retrieving skills by ID and name
- Listing skills with pagination and filtering
- Updating skills
- Deleting skills
- Handling duplicate names
- Testing count operations
"""
import pytest
from models.skill_list import SkillList
from models.user import User
from schemas.skill_list import SkillListCreate, SkillListUpdate
from services.skill_list_service import SkillListService
from core.exceptions import ValidationException, NotFoundException
from database import SessionLocal


def skill_content(name: str, description: str = "Test skill description") -> str:
    """Build valid skill content.

    ``SkillListService.create``/``update`` now derive the skill name from the
    YAML frontmatter of ``content`` and reject content without it, so every
    skill created in these tests needs a well-formed frontmatter block.
    """
    return f"---\nname: {name}\ndescription: {description}\n---\n\nSkill body for {name}."


@pytest.fixture(scope="function")
def user123():
    """A non-admin user used as the ``current_user`` for skill operations.

    ``created_by`` is taken from ``current_user.username`` by the service, so
    the payload's own ``created_by`` value is ignored.
    """
    return User(username="user123", email="user123@example.com", hashed_password="x")


@pytest.fixture(scope="function")
def user456():
    """A second non-admin user, for author-filtering tests."""
    return User(username="user456", email="user456@example.com", hashed_password="x")


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        # Clean up all data after each test using a fresh session
        cleanup_db = SessionLocal()
        try:
            cleanup_db.query(SkillList).delete()
            cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
        finally:
            cleanup_db.close()


class TestSkillListServiceCreate:
    """Tests for skill creation operations."""

    def test_create_skill(self, db, user123):
        """Test successful skill creation."""
        content = skill_content("test-skill")
        skill_data = SkillListCreate(
            name="test-skill",
            description="Test skill description",
            content=content,
            created_by="ignored",
            category="data-processing",
            tags="python,etl",
            version="1.0.0"
        )

        skill = SkillListService.create(db, skill_data, user123)

        assert skill.id is not None
        assert skill.name == "test-skill"
        assert skill.description == "Test skill description"
        assert skill.content == content
        # created_by comes from the authenticated user, not from the payload
        assert skill.created_by == "user123"
        assert skill.category == "data-processing"
        assert skill.tags == "python,etl"
        assert skill.version == "1.0.0"

    def test_create_skill_minimal(self, db, user123):
        """Test skill creation with minimal required fields."""
        skill_data = SkillListCreate(
            name="minimal-skill",
            content=skill_content("minimal-skill")
        )

        skill = SkillListService.create(db, skill_data, user123)

        assert skill.id is not None
        assert skill.name == "minimal-skill"
        assert skill.created_by == "user123"
        assert skill.version == "1.0.0"  # Default version

    def test_create_skill_name_comes_from_content(self, db, user123):
        """The frontmatter name wins over the name given in the payload."""
        skill_data = SkillListCreate(
            name="payload-name",
            content=skill_content("frontmatter-name")
        )

        skill = SkillListService.create(db, skill_data, user123)

        assert skill.name == "frontmatter-name"

    def test_create_skill_invalid_content(self, db, user123):
        """Content without YAML frontmatter is rejected."""
        skill_data = SkillListCreate(
            name="bad-skill",
            content="Test skill content"
        )

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.create(db, skill_data, user123)

        assert "frontmatter" in str(exc_info.value).lower()

    def test_create_skill_duplicate_name(self, db, user123):
        """Test that duplicate skill names are rejected."""
        skill_data = SkillListCreate(
            name="duplicate-skill",
            content=skill_content("duplicate-skill")
        )

        # Create first skill
        SkillListService.create(db, skill_data, user123)

        # Try to create duplicate
        with pytest.raises(ValidationException) as exc_info:
            SkillListService.create(db, skill_data, user123)

        assert "already exists" in str(exc_info.value)
        assert "duplicate-skill" in str(exc_info.value)

    def test_create_skill_with_tags(self, db, user123):
        """Test skill creation with various tags."""
        skill_data = SkillListCreate(
            name="tagged-skill",
            content=skill_content("tagged-skill"),
            tags="machine-learning,ai,python,data-science"
        )

        skill = SkillListService.create(db, skill_data, user123)

        assert skill.tags == "machine-learning,ai,python,data-science"


class TestSkillListServiceGet:
    """Tests for skill retrieval operations."""

    def test_get_by_id_found(self, db, user123):
        """Test getting a skill by ID when it exists."""
        # Create skill first
        skill_data = SkillListCreate(
            name="get-test-skill",
            description="Get test skill",
            content=skill_content("get-test-skill"),
            category="test"
        )
        created = SkillListService.create(db, skill_data, user123)

        # Get by ID
        skill = SkillListService.get_by_id(db, created.id)

        assert skill is not None
        assert skill.id == created.id
        assert skill.name == "get-test-skill"
        assert skill.description == "Get test skill"
        assert skill.category == "test"

    def test_get_by_id_not_found(self, db):
        """Test getting a skill by ID when it doesn't exist."""
        skill = SkillListService.get_by_id(db, "non-existent-id")
        assert skill is None

    def test_get_by_name_found(self, db, user123):
        """Test getting a skill by name when it exists."""
        # Create skill first
        skill_data = SkillListCreate(
            name="name-test-skill",
            content=skill_content("name-test-skill")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Get by name
        skill = SkillListService.get_by_name(db, "name-test-skill")

        assert skill is not None
        assert skill.id == created.id
        assert skill.name == "name-test-skill"

    def test_get_by_name_not_found(self, db):
        """Test getting a skill by name when it doesn't exist."""
        skill = SkillListService.get_by_name(db, "non-existent-name")
        assert skill is None


class TestSkillListServiceList:
    """Tests for skill listing and filtering operations."""

    def test_list_all_empty(self, db):
        """Test listing all skills when database is empty."""
        skills = SkillListService.list_all(db)
        assert len(skills) == 0

    def test_list_all_multiple(self, db, user123):
        """Test listing all skills with multiple entries."""
        # Create 3 skills
        for i in range(3):
            skill_data = SkillListCreate(
                name=f"list-skill-{i}",
                content=skill_content(f"list-skill-{i}")
            )
            SkillListService.create(db, skill_data, user123)

        # List all
        skills = SkillListService.list_all(db)
        assert len(skills) >= 3

    def test_list_all_pagination(self, db, user123):
        """Test listing skills with pagination."""
        # Create 5 skills
        for i in range(5):
            skill_data = SkillListCreate(
                name=f"page-skill-{i}",
                content=skill_content(f"page-skill-{i}")
            )
            SkillListService.create(db, skill_data, user123)

        # Get first page
        page1 = SkillListService.list_all(db, skip=0, limit=3)
        assert len(page1) == 3

        # Get second page
        page2 = SkillListService.list_all(db, skip=3, limit=3)
        assert len(page2) == 2

    def test_list_by_category(self, db, user123):
        """Test listing skills by category."""
        # Create skills in different categories
        for name, category in [
            ("cat-skill-1", "data-processing"),
            ("cat-skill-2", "data-processing"),
            ("cat-skill-3", "ai-llm"),
        ]:
            SkillListService.create(db, SkillListCreate(
                name=name, content=skill_content(name), category=category
            ), user123)

        # List by data-processing category
        data_skills, data_total = SkillListService.list_with_filters(
            db, category="data-processing"
        )
        assert len(data_skills) == 2
        assert data_total == 2

        # List by ai-llm category
        ai_skills, ai_total = SkillListService.list_with_filters(db, category="ai-llm")
        assert len(ai_skills) == 1
        assert ai_total == 1

    def test_list_by_author(self, db, user123, user456):
        """Test listing skills by creator/author."""
        # Create skills by different authors
        SkillListService.create(db, SkillListCreate(
            name="author-skill-1", content=skill_content("author-skill-1")
        ), user123)
        SkillListService.create(db, SkillListCreate(
            name="author-skill-2", content=skill_content("author-skill-2")
        ), user123)
        SkillListService.create(db, SkillListCreate(
            name="author-skill-3", content=skill_content("author-skill-3")
        ), user456)

        # List by user123
        user123_skills, _ = SkillListService.list_with_filters(db, author="user123")
        assert len(user123_skills) == 2

        # List by user456
        user456_skills, _ = SkillListService.list_with_filters(db, author="user456")
        assert len(user456_skills) == 1

    def test_list_by_tags_single(self, db, user123):
        """Test listing skills by a single tag."""
        # Create skills with different tags
        for name, tags in [
            ("tag-skill-1", "python"),
            ("tag-skill-2", "python,etl"),
            ("tag-skill-3", "javascript"),
        ]:
            SkillListService.create(db, SkillListCreate(
                name=name, content=skill_content(name), tags=tags
            ), user123)

        # List by python tag (should match skill-1 and skill-2)
        python_skills, _ = SkillListService.list_with_filters(db, tags="python")
        assert len(python_skills) == 2

        # List by javascript tag
        js_skills, _ = SkillListService.list_with_filters(db, tags="javascript")
        assert len(js_skills) == 1

    def test_list_by_tags_multiple(self, db, user123):
        """Test listing skills by multiple tags (OR logic)."""
        # Create skills
        for name, tags in [
            ("multi-tag-1", "python,etl"),
            ("multi-tag-2", "javascript,api"),
            ("multi-tag-3", "python,ml"),
        ]:
            SkillListService.create(db, SkillListCreate(
                name=name, content=skill_content(name), tags=tags
            ), user123)

        # List by multiple tags (should match any skill with python OR etl)
        skills, _ = SkillListService.list_with_filters(db, tags="python,etl")
        assert len(skills) == 2  # multi-tag-1 and multi-tag-3

    def test_list_by_tags_empty(self, db):
        """Test listing skills with empty tag string."""
        skills, total = SkillListService.list_with_filters(db, tags="")
        assert len(skills) == 0
        assert total == 0

    def test_count_all(self, db, user123):
        """Test counting all skills."""
        # Initial count
        initial_count = SkillListService.count_all(db)

        # Create 3 skills
        for i in range(3):
            skill_data = SkillListCreate(
                name=f"count-skill-{i}",
                content=skill_content(f"count-skill-{i}")
            )
            SkillListService.create(db, skill_data, user123)

        # Check count increased
        new_count = SkillListService.count_all(db)
        assert new_count == initial_count + 3

    def test_count_by_category(self, db, user123):
        """Test counting skills by category."""
        # Create skills in different categories
        for name, category in [
            ("count-cat-1", "data-processing"),
            ("count-cat-2", "data-processing"),
            ("count-cat-3", "ai-llm"),
        ]:
            SkillListService.create(db, SkillListCreate(
                name=name, content=skill_content(name), category=category
            ), user123)

        # Count by data-processing category
        data_count = SkillListService.count_by_category(db, "data-processing")
        assert data_count == 2

        # Count by ai-llm category
        ai_count = SkillListService.count_by_category(db, "ai-llm")
        assert ai_count == 1

    def test_count_by_author(self, db, user123, user456):
        """Test counting skills by creator/author."""
        # Create skills by different authors
        SkillListService.create(db, SkillListCreate(
            name="count-auth-1", content=skill_content("count-auth-1")
        ), user123)
        SkillListService.create(db, SkillListCreate(
            name="count-auth-2", content=skill_content("count-auth-2")
        ), user123)
        SkillListService.create(db, SkillListCreate(
            name="count-auth-3", content=skill_content("count-auth-3")
        ), user456)

        # Count by user123
        user123_count = SkillListService.count_by_author(db, "user123")
        assert user123_count == 2

        # Count by user456
        user456_count = SkillListService.count_by_author(db, "user456")
        assert user456_count == 1

    def test_count_by_tags(self, db, user123):
        """Test counting skills by tags."""
        # Create skills with different tags
        for name, tags in [
            ("count-tag-1", "python"),
            ("count-tag-2", "python,etl"),
            ("count-tag-3", "javascript"),
        ]:
            SkillListService.create(db, SkillListCreate(
                name=name, content=skill_content(name), tags=tags
            ), user123)

        # Count by python tag
        python_count = SkillListService.count_by_tags(db, "python")
        assert python_count == 2

        # Count by javascript tag
        js_count = SkillListService.count_by_tags(db, "javascript")
        assert js_count == 1


class TestSkillListServiceUpdate:
    """Tests for skill update operations."""

    def test_update_description(self, db, user123):
        """Test updating skill description."""
        # Create skill first
        skill_data = SkillListCreate(
            name="update-desc-skill",
            description="Original description",
            content=skill_content("update-desc-skill")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Update description
        update_data = SkillListUpdate(description="Updated description")
        updated = SkillListService.update(db, created.id, update_data, user123)

        assert updated.description == "Updated description"
        assert updated.name == "update-desc-skill"  # Name unchanged

    def test_update_name(self, db, user123):
        """Test updating skill name.

        The name is no longer taken from the update payload; it follows the
        ``name`` field of the new content frontmatter.
        """
        # Create skill first
        skill_data = SkillListCreate(
            name="old-name-skill",
            content=skill_content("old-name-skill")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Update name via new content frontmatter
        update_data = SkillListUpdate(content=skill_content("new-name-skill"))
        updated = SkillListService.update(db, created.id, update_data, user123)

        assert updated.name == "new-name-skill"

    def test_update_name_in_payload_is_ignored(self, db, user123):
        """A ``name`` in the update payload does not rename the skill."""
        created = SkillListService.create(db, SkillListCreate(
            name="payload-rename-skill",
            content=skill_content("payload-rename-skill")
        ), user123)

        updated = SkillListService.update(
            db, created.id, SkillListUpdate(name="some-other-name"), user123
        )

        assert updated.name == "payload-rename-skill"

    def test_update_multiple_fields(self, db, user123):
        """Test updating multiple fields at once."""
        # Create skill
        skill_data = SkillListCreate(
            name="multi-update-skill",
            description="Original",
            content=skill_content("multi-update-skill"),
            category="original-category",
            tags="original-tags",
            version="1.0.0"
        )
        created = SkillListService.create(db, skill_data, user123)

        # Update multiple fields
        update_data = SkillListUpdate(
            description="Updated description",
            category="updated-category",
            tags="updated-tags",
            version="2.0.0"
        )
        updated = SkillListService.update(db, created.id, update_data, user123)

        assert updated.description == "Updated description"
        assert updated.category == "updated-category"
        assert updated.tags == "updated-tags"
        assert updated.version == "2.0.0"
        assert updated.name == "multi-update-skill"  # Name unchanged

    def test_update_content(self, db, user123):
        """Test updating skill content."""
        # Create skill
        skill_data = SkillListCreate(
            name="content-skill",
            content=skill_content("content-skill", "Original description")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Update content
        new_content = skill_content("content-skill", "Updated description")
        update_data = SkillListUpdate(content=new_content)
        updated = SkillListService.update(db, created.id, update_data, user123)

        assert updated.content == new_content

    def test_update_invalid_content(self, db, user123):
        """Updating with content that has no frontmatter is rejected."""
        created = SkillListService.create(db, SkillListCreate(
            name="invalid-content-skill",
            content=skill_content("invalid-content-skill")
        ), user123)

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.update(
                db, created.id, SkillListUpdate(content="Updated content"), user123
            )

        assert "frontmatter" in str(exc_info.value).lower()

    def test_update_duplicate_name(self, db, user123):
        """Test that updating to a duplicate name is rejected."""
        # Create two skills
        SkillListService.create(db, SkillListCreate(
            name="skill-1", content=skill_content("skill-1")
        ), user123)
        skill2 = SkillListService.create(db, SkillListCreate(
            name="skill-2", content=skill_content("skill-2")
        ), user123)

        # Try to update skill2 to have the same name as skill1
        update_data = SkillListUpdate(content=skill_content("skill-1"))
        with pytest.raises(ValidationException) as exc_info:
            SkillListService.update(db, skill2.id, update_data, user123)

        assert "already exists" in str(exc_info.value)

    def test_update_not_found(self, db, user123):
        """Test updating a non-existent skill."""
        update_data = SkillListUpdate(description="Updated")

        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.update(db, "non-existent-id", update_data, user123)

        assert "not found" in str(exc_info.value)

    def test_update_requires_creator_or_admin(self, db, user123, user456):
        """A non-creator, non-admin user cannot update a skill."""
        created = SkillListService.create(db, SkillListCreate(
            name="owned-skill", content=skill_content("owned-skill")
        ), user123)

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.update(
                db, created.id, SkillListUpdate(description="hijacked"), user456
            )

        assert "permission" in str(exc_info.value).lower()

    def test_update_same_name(self, db, user123):
        """Test updating skill to its own name (should succeed)."""
        # Create skill
        skill_data = SkillListCreate(
            name="same-name-skill",
            description="Original",
            content=skill_content("same-name-skill")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Update with same name (should not cause conflict)
        update_data = SkillListUpdate(
            content=skill_content("same-name-skill"),
            description="Updated"
        )
        updated = SkillListService.update(db, created.id, update_data, user123)

        assert updated.name == "same-name-skill"
        assert updated.description == "Updated"


class TestSkillListServiceDelete:
    """Tests for skill deletion operations."""

    def test_delete_skill(self, db, user123):
        """Test successful skill deletion."""
        # Create skill first
        skill_data = SkillListCreate(
            name="delete-skill",
            content=skill_content("delete-skill")
        )
        created = SkillListService.create(db, skill_data, user123)

        # Delete
        result = SkillListService.delete(db, created.id, user123)

        assert result is True

        # Verify deleted
        skill = SkillListService.get_by_id(db, created.id)
        assert skill is None

    def test_delete_not_found(self, db, user123):
        """Test deleting a non-existent skill."""
        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.delete(db, "non-existent-id", user123)

        assert "not found" in str(exc_info.value)

    def test_delete_requires_creator_or_admin(self, db, user123, user456):
        """A non-creator, non-admin user cannot delete a skill."""
        created = SkillListService.create(db, SkillListCreate(
            name="delete-owned-skill", content=skill_content("delete-owned-skill")
        ), user123)

        with pytest.raises(ValidationException) as exc_info:
            SkillListService.delete(db, created.id, user456)

        assert "permission" in str(exc_info.value).lower()

    def test_delete_multiple(self, db, user123):
        """Test deleting multiple skills."""
        # Create multiple skills
        skill1 = SkillListService.create(db, SkillListCreate(
            name="delete-multi-1", content=skill_content("delete-multi-1")
        ), user123)
        skill2 = SkillListService.create(db, SkillListCreate(
            name="delete-multi-2", content=skill_content("delete-multi-2")
        ), user123)

        # Delete first
        result1 = SkillListService.delete(db, skill1.id, user123)
        assert result1 is True

        # Verify first deleted but second exists
        assert SkillListService.get_by_id(db, skill1.id) is None
        assert SkillListService.get_by_id(db, skill2.id) is not None

        # Delete second
        result2 = SkillListService.delete(db, skill2.id, user123)
        assert result2 is True

        # Verify both deleted
        assert SkillListService.get_by_id(db, skill2.id) is None
