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
from schemas.skill_list import SkillListCreate, SkillListUpdate
from services.skill_list_service import SkillListService
from core.exceptions import ValidationException, NotFoundException
from database import SessionLocal


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    finally:
        # Clean up resources after each test
        db.query(SkillList).delete()
        db.commit()
        db.close()


class TestSkillListServiceCreate:
    """Tests for skill creation operations."""

    def test_create_skill(self, db):
        """Test successful skill creation."""
        skill_data = SkillListCreate(
            name="test-skill",
            description="Test skill description",
            content="Test skill content",
            created_by="user123",
            category="data-processing",
            tags="python,etl",
            version="1.0.0"
        )

        skill = SkillListService.create(db, skill_data)

        assert skill.id is not None
        assert skill.name == "test-skill"
        assert skill.description == "Test skill description"
        assert skill.content == "Test skill content"
        assert skill.created_by == "user123"
        assert skill.category == "data-processing"
        assert skill.tags == "python,etl"
        assert skill.version == "1.0.0"

    def test_create_skill_minimal(self, db):
        """Test skill creation with minimal required fields."""
        skill_data = SkillListCreate(
            name="minimal-skill",
            created_by="user123"
        )

        skill = SkillListService.create(db, skill_data)

        assert skill.id is not None
        assert skill.name == "minimal-skill"
        assert skill.created_by == "user123"
        assert skill.version == "1.0.0"  # Default version

    def test_create_skill_duplicate_name(self, db):
        """Test that duplicate skill names are rejected."""
        skill_data = SkillListCreate(
            name="duplicate-skill",
            created_by="user123"
        )

        # Create first skill
        SkillListService.create(db, skill_data)

        # Try to create duplicate
        with pytest.raises(ValidationException) as exc_info:
            SkillListService.create(db, skill_data)

        assert "already exists" in str(exc_info.value)
        assert "duplicate-skill" in str(exc_info.value)

    def test_create_skill_with_tags(self, db):
        """Test skill creation with various tags."""
        skill_data = SkillListCreate(
            name="tagged-skill",
            created_by="user123",
            tags="machine-learning,ai,python,data-science"
        )

        skill = SkillListService.create(db, skill_data)

        assert skill.tags == "machine-learning,ai,python,data-science"


class TestSkillListServiceGet:
    """Tests for skill retrieval operations."""

    def test_get_by_id_found(self, db):
        """Test getting a skill by ID when it exists."""
        # Create skill first
        skill_data = SkillListCreate(
            name="get-test-skill",
            description="Get test skill",
            created_by="user123",
            category="test"
        )
        created = SkillListService.create(db, skill_data)

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

    def test_get_by_name_found(self, db):
        """Test getting a skill by name when it exists."""
        # Create skill first
        skill_data = SkillListCreate(
            name="name-test-skill",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

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

    def test_list_all_multiple(self, db):
        """Test listing all skills with multiple entries."""
        # Create 3 skills
        for i in range(3):
            skill_data = SkillListCreate(
                name=f"list-skill-{i}",
                created_by="user123"
            )
            SkillListService.create(db, skill_data)

        # List all
        skills = SkillListService.list_all(db)
        assert len(skills) >= 3

    def test_list_all_pagination(self, db):
        """Test listing skills with pagination."""
        # Create 5 skills
        for i in range(5):
            skill_data = SkillListCreate(
                name=f"page-skill-{i}",
                created_by="user123"
            )
            SkillListService.create(db, skill_data)

        # Get first page
        page1 = SkillListService.list_all(db, skip=0, limit=3)
        assert len(page1) == 3

        # Get second page
        page2 = SkillListService.list_all(db, skip=3, limit=3)
        assert len(page2) == 2

    def test_list_by_category(self, db):
        """Test listing skills by category."""
        # Create skills in different categories
        SkillListService.create(db, SkillListCreate(
            name="cat-skill-1", created_by="user123", category="data-processing"
        ))
        SkillListService.create(db, SkillListCreate(
            name="cat-skill-2", created_by="user123", category="data-processing"
        ))
        SkillListService.create(db, SkillListCreate(
            name="cat-skill-3", created_by="user123", category="ai-llm"
        ))

        # List by data-processing category
        data_skills = SkillListService.list_by_category(db, "data-processing")
        assert len(data_skills) == 2

        # List by ai-llm category
        ai_skills = SkillListService.list_by_category(db, "ai-llm")
        assert len(ai_skills) == 1

    def test_list_by_author(self, db):
        """Test listing skills by creator/author."""
        # Create skills by different authors
        SkillListService.create(db, SkillListCreate(
            name="author-skill-1", created_by="user123"
        ))
        SkillListService.create(db, SkillListCreate(
            name="author-skill-2", created_by="user123"
        ))
        SkillListService.create(db, SkillListCreate(
            name="author-skill-3", created_by="user456"
        ))

        # List by user123
        user123_skills = SkillListService.list_by_author(db, "user123")
        assert len(user123_skills) == 2

        # List by user456
        user456_skills = SkillListService.list_by_author(db, "user456")
        assert len(user456_skills) == 1

    def test_list_by_tags_single(self, db):
        """Test listing skills by a single tag."""
        # Create skills with different tags
        SkillListService.create(db, SkillListCreate(
            name="tag-skill-1", created_by="user123", tags="python"
        ))
        SkillListService.create(db, SkillListCreate(
            name="tag-skill-2", created_by="user123", tags="python,etl"
        ))
        SkillListService.create(db, SkillListCreate(
            name="tag-skill-3", created_by="user123", tags="javascript"
        ))

        # List by python tag (should match skill-1 and skill-2)
        python_skills = SkillListService.list_by_tags(db, "python")
        assert len(python_skills) == 2

        # List by javascript tag
        js_skills = SkillListService.list_by_tags(db, "javascript")
        assert len(js_skills) == 1

    def test_list_by_tags_multiple(self, db):
        """Test listing skills by multiple tags (OR logic)."""
        # Create skills
        SkillListService.create(db, SkillListCreate(
            name="multi-tag-1", created_by="user123", tags="python,etl"
        ))
        SkillListService.create(db, SkillListCreate(
            name="multi-tag-2", created_by="user123", tags="javascript,api"
        ))
        SkillListService.create(db, SkillListCreate(
            name="multi-tag-3", created_by="user123", tags="python,ml"
        ))

        # List by multiple tags (should match any skill with python OR etl)
        skills = SkillListService.list_by_tags(db, "python,etl")
        assert len(skills) == 2  # multi-tag-1 and multi-tag-3

    def test_list_by_tags_empty(self, db):
        """Test listing skills with empty tag string."""
        skills = SkillListService.list_by_tags(db, "")
        assert len(skills) == 0

    def test_count_all(self, db):
        """Test counting all skills."""
        # Initial count
        initial_count = SkillListService.count_all(db)

        # Create 3 skills
        for i in range(3):
            skill_data = SkillListCreate(
                name=f"count-skill-{i}",
                created_by="user123"
            )
            SkillListService.create(db, skill_data)

        # Check count increased
        new_count = SkillListService.count_all(db)
        assert new_count == initial_count + 3

    def test_count_by_category(self, db):
        """Test counting skills by category."""
        # Create skills in different categories
        SkillListService.create(db, SkillListCreate(
            name="count-cat-1", created_by="user123", category="data-processing"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-cat-2", created_by="user123", category="data-processing"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-cat-3", created_by="user123", category="ai-llm"
        ))

        # Count by data-processing category
        data_count = SkillListService.count_by_category(db, "data-processing")
        assert data_count == 2

        # Count by ai-llm category
        ai_count = SkillListService.count_by_category(db, "ai-llm")
        assert ai_count == 1

    def test_count_by_author(self, db):
        """Test counting skills by creator/author."""
        # Create skills by different authors
        SkillListService.create(db, SkillListCreate(
            name="count-auth-1", created_by="user123"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-auth-2", created_by="user123"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-auth-3", created_by="user456"
        ))

        # Count by user123
        user123_count = SkillListService.count_by_author(db, "user123")
        assert user123_count == 2

        # Count by user456
        user456_count = SkillListService.count_by_author(db, "user456")
        assert user456_count == 1

    def test_count_by_tags(self, db):
        """Test counting skills by tags."""
        # Create skills with different tags
        SkillListService.create(db, SkillListCreate(
            name="count-tag-1", created_by="user123", tags="python"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-tag-2", created_by="user123", tags="python,etl"
        ))
        SkillListService.create(db, SkillListCreate(
            name="count-tag-3", created_by="user123", tags="javascript"
        ))

        # Count by python tag
        python_count = SkillListService.count_by_tags(db, "python")
        assert python_count == 2

        # Count by javascript tag
        js_count = SkillListService.count_by_tags(db, "javascript")
        assert js_count == 1


class TestSkillListServiceUpdate:
    """Tests for skill update operations."""

    def test_update_description(self, db):
        """Test updating skill description."""
        # Create skill first
        skill_data = SkillListCreate(
            name="update-desc-skill",
            description="Original description",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

        # Update description
        update_data = SkillListUpdate(description="Updated description")
        updated = SkillListService.update(db, created.id, update_data)

        assert updated.description == "Updated description"
        assert updated.name == "update-desc-skill"  # Name unchanged

    def test_update_name(self, db):
        """Test updating skill name."""
        # Create skill first
        skill_data = SkillListCreate(
            name="old-name-skill",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

        # Update name
        update_data = SkillListUpdate(name="new-name-skill")
        updated = SkillListService.update(db, created.id, update_data)

        assert updated.name == "new-name-skill"

    def test_update_multiple_fields(self, db):
        """Test updating multiple fields at once."""
        # Create skill
        skill_data = SkillListCreate(
            name="multi-update-skill",
            description="Original",
            created_by="user123",
            category="original-category",
            tags="original-tags",
            version="1.0.0"
        )
        created = SkillListService.create(db, skill_data)

        # Update multiple fields
        update_data = SkillListUpdate(
            description="Updated description",
            category="updated-category",
            tags="updated-tags",
            version="2.0.0"
        )
        updated = SkillListService.update(db, created.id, update_data)

        assert updated.description == "Updated description"
        assert updated.category == "updated-category"
        assert updated.tags == "updated-tags"
        assert updated.version == "2.0.0"
        assert updated.name == "multi-update-skill"  # Name unchanged

    def test_update_content(self, db):
        """Test updating skill content."""
        # Create skill
        skill_data = SkillListCreate(
            name="content-skill",
            content="Original content",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

        # Update content
        update_data = SkillListUpdate(content="Updated content")
        updated = SkillListService.update(db, created.id, update_data)

        assert updated.content == "Updated content"

    def test_update_duplicate_name(self, db):
        """Test that updating to a duplicate name is rejected."""
        # Create two skills
        skill1 = SkillListService.create(db, SkillListCreate(
            name="skill-1", created_by="user123"
        ))
        skill2 = SkillListService.create(db, SkillListCreate(
            name="skill-2", created_by="user123"
        ))

        # Try to update skill2 to have the same name as skill1
        update_data = SkillListUpdate(name="skill-1")
        with pytest.raises(ValidationException) as exc_info:
            SkillListService.update(db, skill2.id, update_data)

        assert "already exists" in str(exc_info.value)

    def test_update_not_found(self, db):
        """Test updating a non-existent skill."""
        update_data = SkillListUpdate(description="Updated")

        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.update(db, "non-existent-id", update_data)

        assert "not found" in str(exc_info.value)

    def test_update_same_name(self, db):
        """Test updating skill to its own name (should succeed)."""
        # Create skill
        skill_data = SkillListCreate(
            name="same-name-skill",
            description="Original",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

        # Update with same name (should not cause conflict)
        update_data = SkillListUpdate(
            name="same-name-skill",
            description="Updated"
        )
        updated = SkillListService.update(db, created.id, update_data)

        assert updated.name == "same-name-skill"
        assert updated.description == "Updated"


class TestSkillListServiceDelete:
    """Tests for skill deletion operations."""

    def test_delete_skill(self, db):
        """Test successful skill deletion."""
        # Create skill first
        skill_data = SkillListCreate(
            name="delete-skill",
            created_by="user123"
        )
        created = SkillListService.create(db, skill_data)

        # Delete
        result = SkillListService.delete(db, created.id)

        assert result is True

        # Verify deleted
        skill = SkillListService.get_by_id(db, created.id)
        assert skill is None

    def test_delete_not_found(self, db):
        """Test deleting a non-existent skill."""
        with pytest.raises(NotFoundException) as exc_info:
            SkillListService.delete(db, "non-existent-id")

        assert "not found" in str(exc_info.value)

    def test_delete_multiple(self, db):
        """Test deleting multiple skills."""
        # Create multiple skills
        skill1 = SkillListService.create(db, SkillListCreate(
            name="delete-multi-1", created_by="user123"
        ))
        skill2 = SkillListService.create(db, SkillListCreate(
            name="delete-multi-2", created_by="user123"
        ))

        # Delete first
        result1 = SkillListService.delete(db, skill1.id)
        assert result1 is True

        # Verify first deleted but second exists
        assert SkillListService.get_by_id(db, skill1.id) is None
        assert SkillListService.get_by_id(db, skill2.id) is not None

        # Delete second
        result2 = SkillListService.delete(db, skill2.id)
        assert result2 is True

        # Verify both deleted
        assert SkillListService.get_by_id(db, skill2.id) is None
