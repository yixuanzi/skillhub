"""Unit tests for resource management module.

This module contains tests for resource CRUD operations including:
- Creating resources
- Retrieving resources by ID and name
- Listing resources with pagination and filtering
- Updating resources
- Deleting resources
- Handling duplicate names
"""
import pytest
from models.resource import Resource, ResourceType
from models.user import User, Role
from schemas.resource import ResourceCreate, ResourceUpdate
from services.resource_service import ResourceService
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
        db.query(Resource).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def test_user(db):
    """A plain (non-admin) persisted user, local to this module's own `db`."""
    user = User(username="resources-test-user", email="resources-test-user@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_resource_with_ext(db):
    """Test resource creation with ext data."""
    resource_data = ResourceCreate(
        name="test-resource-ext",
        desc="Test resource with ext",
        type=ResourceType.GATEWAY,
        ext={"key1": "value1", "key2": "value2"}
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.id is not None
    assert resource.name == "test-resource-ext"
    assert resource.type == ResourceType.GATEWAY
    # ext is stored as JSON string in database


def test_get_resource(db):
    """Test getting a resource by ID."""
    # Create first
    resource_data = ResourceCreate(
        name="get-test",
        type=ResourceType.GATEWAY,
        desc="Get test resource"
    )
    created = ResourceService.create(db, resource_data)

    # Get by ID
    resource = ResourceService.get_by_id(db, created.id)

    assert resource is not None
    assert resource.name == "get-test"
    assert resource.desc == "Get test resource"


def test_get_resource_not_found(db):
    """Test getting a non-existent resource."""
    resource = ResourceService.get_by_id(db, "non-existent-id")
    assert resource is None


def test_get_by_name(db):
    """Test getting a resource by name."""
    # Create first
    resource_data = ResourceCreate(
        name="name-test",
        type=ResourceType.THIRD
    )
    created = ResourceService.create(db, resource_data)

    # Get by name
    resource = ResourceService.get_by_name(db, "name-test")

    assert resource is not None
    assert resource.id == created.id
    assert resource.name == "name-test"


def test_list_resources_with_pagination(db):
    """Test listing resources with pagination."""
    # Create 5 resources
    for i in range(5):
        resource_data = ResourceCreate(
            name=f"page-test-{i}",
            type=ResourceType.GATEWAY
        )
        ResourceService.create(db, resource_data)

    # Get first page
    page1 = ResourceService.list_all(db, skip=0, limit=3)
    assert len(page1) == 3

    # Get second page
    page2 = ResourceService.list_all(db, skip=3, limit=3)
    assert len(page2) == 2


def test_update_resource(db):
    """Test updating a resource."""
    # Create first
    resource_data = ResourceCreate(
        name="update-test",
        type=ResourceType.THIRD,
        desc="Original description"
    )
    created = ResourceService.create(db, resource_data)

    # Update description
    update_data = ResourceUpdate(desc="Updated description")
    updated = ResourceService.update(db, created.id, update_data)

    assert updated.desc == "Updated description"
    assert updated.name == "update-test"  # Name unchanged


def test_update_not_found(db):
    """Test updating a non-existent resource."""
    update_data = ResourceUpdate(desc="Updated")

    with pytest.raises(NotFoundException) as exc_info:
        ResourceService.update(db, "non-existent-id", update_data)

    assert "not found" in str(exc_info.value)


def test_delete_not_found(db):
    """Test deleting a non-existent resource."""
    with pytest.raises(NotFoundException) as exc_info:
        ResourceService.delete(db, "non-existent-id")

    assert "not found" in str(exc_info.value)


def test_resource_with_url(db):
    """Test resource creation with URL."""
    resource_data = ResourceCreate(
        name="url-test",
        type=ResourceType.THIRD,
        url="https://api.example.com/v1/endpoint"
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.url == "https://api.example.com/v1/endpoint"


class TestListAccessibleWithCountResourceTypeFilter:
    """`GET /api/v1/resources/?resource_type=...` must actually filter by type.

    Regression coverage: the route accepted `resource_type` but never passed it
    to ResourceService.list_accessible_with_count, so every filtered listing
    silently returned ALL accessible resources regardless of type. The
    frontend's composio-singleton "does one already exist?" check relies on
    this: {resource_type: 'composio'} must not count unrelated resources.
    """

    def test_filters_by_type_for_anonymous_user(self, db):
        ResourceService.create(db, ResourceCreate(
            name="pub-gateway", type=ResourceType.GATEWAY, view_scope="public"
        ))
        ResourceService.create(db, ResourceCreate(
            name="pub-composio", type=ResourceType.COMPOSIO, view_scope="public",
            ext={"COMPOSIO_API_KEY": "ak_x", "COMPOSIO_USER_ID": "u1"},
        ))

        resources, total = ResourceService.list_accessible_with_count(
            db, None, resource_type=ResourceType.COMPOSIO.value
        )

        assert total == 1
        assert [r.name for r in resources] == ["pub-composio"]

    def test_filters_by_type_for_admin_user(self, db, test_user):
        ResourceService.create(db, ResourceCreate(name="gw", type=ResourceType.GATEWAY), user=test_user)
        ResourceService.create(db, ResourceCreate(
            name="composio", type=ResourceType.COMPOSIO,
            ext={"COMPOSIO_API_KEY": "ak_x", "COMPOSIO_USER_ID": "u1"},
        ), user=test_user)

        admin_role = Role(name="admin", description="Administrator")
        test_user.roles.append(admin_role)
        db.add(admin_role)
        db.commit()

        resources, total = ResourceService.list_accessible_with_count(
            db, test_user, resource_type=ResourceType.COMPOSIO.value
        )

        assert total == 1
        assert [r.name for r in resources] == ["composio"]

    def test_filters_by_type_for_regular_user(self, db, test_user):
        """This is the exact path the Resources page's existence-check hits."""
        ResourceService.create(db, ResourceCreate(name="gw", type=ResourceType.GATEWAY), user=test_user)
        ResourceService.create(db, ResourceCreate(name="third", type=ResourceType.THIRD), user=test_user)

        # No composio resource created yet - the count must be zero, not the
        # total count of all of this user's resources.
        resources, total = ResourceService.list_accessible_with_count(
            db, test_user, resource_type=ResourceType.COMPOSIO.value
        )

        assert total == 0
        assert resources == []

        ResourceService.create(db, ResourceCreate(
            name="composio", type=ResourceType.COMPOSIO,
            ext={"COMPOSIO_API_KEY": "ak_x", "COMPOSIO_USER_ID": "u1"},
        ), user=test_user)

        resources, total = ResourceService.list_accessible_with_count(
            db, test_user, resource_type=ResourceType.COMPOSIO.value
        )

        assert total == 1
        assert [r.name for r in resources] == ["composio"]

    def test_no_filter_returns_everything(self, db, test_user):
        ResourceService.create(db, ResourceCreate(name="gw", type=ResourceType.GATEWAY), user=test_user)
        ResourceService.create(db, ResourceCreate(name="third", type=ResourceType.THIRD), user=test_user)

        _resources, total = ResourceService.list_accessible_with_count(db, test_user)

        assert total == 2
