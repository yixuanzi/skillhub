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
        db.commit()
        db.close()


def test_create_resource(db):
    """Test resource creation."""
    resource_data = ResourceCreate(
        name="test-resource",
        desc="Test resource description",
        type=ResourceType.BUILD,
        url="http://example.com"
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.id is not None
    assert resource.name == "test-resource"
    assert resource.desc == "Test resource description"
    assert resource.type == ResourceType.BUILD
    assert resource.url == "http://example.com"


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


def test_duplicate_name(db):
    """Test that duplicate resource names are rejected."""
    resource_data = ResourceCreate(
        name="duplicate-test",
        type=ResourceType.BUILD
    )

    # Create first resource
    ResourceService.create(db, resource_data)

    # Try to create duplicate
    with pytest.raises(ValidationException) as exc_info:
        ResourceService.create(db, resource_data)

    assert "already exists" in str(exc_info.value)


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


def test_list_all_resources(db):
    """Test listing all resources."""
    # Create multiple resources
    for i in range(3):
        resource_data = ResourceCreate(
            name=f"list-test-{i}",
            type=ResourceType.BUILD
        )
        ResourceService.create(db, resource_data)

    # List all
    resources = ResourceService.list_all(db)

    assert len(resources) >= 3


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


def test_list_by_type(db):
    """Test listing resources by type."""
    # Create resources of different types
    ResourceService.create(db, ResourceCreate(name="build-1", type=ResourceType.BUILD))
    ResourceService.create(db, ResourceCreate(name="build-2", type=ResourceType.BUILD))
    ResourceService.create(db, ResourceCreate(name="gateway-1", type=ResourceType.GATEWAY))
    ResourceService.create(db, ResourceCreate(name="third-1", type=ResourceType.THIRD))

    # List by BUILD type
    build_resources = ResourceService.list_by_type(db, ResourceType.BUILD)
    assert len(build_resources) == 2

    # List by GATEWAY type
    gateway_resources = ResourceService.list_by_type(db, ResourceType.GATEWAY)
    assert len(gateway_resources) == 1

    # List by THIRD type
    third_resources = ResourceService.list_by_type(db, ResourceType.THIRD)
    assert len(third_resources) == 1


def test_count_all(db):
    """Test counting all resources."""
    # Initial count
    initial_count = ResourceService.count_all(db)

    # Create 3 resources
    for i in range(3):
        resource_data = ResourceCreate(
            name=f"count-test-{i}",
            type=ResourceType.BUILD
        )
        ResourceService.create(db, resource_data)

    # Check count increased
    new_count = ResourceService.count_all(db)
    assert new_count == initial_count + 3


def test_count_by_type(db):
    """Test counting resources by type."""
    # Create resources of different types
    ResourceService.create(db, ResourceCreate(name="count-build-1", type=ResourceType.BUILD))
    ResourceService.create(db, ResourceCreate(name="count-build-2", type=ResourceType.BUILD))
    ResourceService.create(db, ResourceCreate(name="count-gateway-1", type=ResourceType.GATEWAY))

    # Count by BUILD type
    build_count = ResourceService.count_by_type(db, ResourceType.BUILD)
    assert build_count == 2

    # Count by GATEWAY type
    gateway_count = ResourceService.count_by_type(db, ResourceType.GATEWAY)
    assert gateway_count == 1


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


def test_update_resource_name(db):
    """Test updating resource name."""
    # Create first
    resource_data = ResourceCreate(
        name="old-name",
        type=ResourceType.BUILD
    )
    created = ResourceService.create(db, resource_data)

    # Update name
    update_data = ResourceUpdate(name="new-name")
    updated = ResourceService.update(db, created.id, update_data)

    assert updated.name == "new-name"


def test_update_duplicate_name(db):
    """Test that updating to a duplicate name is rejected."""
    # Create two resources
    ResourceService.create(db, ResourceCreate(name="resource-1", type=ResourceType.BUILD))
    resource2 = ResourceService.create(db, ResourceCreate(name="resource-2", type=ResourceType.BUILD))

    # Try to update resource2 to have the same name as resource1
    update_data = ResourceUpdate(name="resource-1")
    with pytest.raises(ValidationException) as exc_info:
        ResourceService.update(db, resource2.id, update_data)

    assert "already exists" in str(exc_info.value)


def test_update_not_found(db):
    """Test updating a non-existent resource."""
    update_data = ResourceUpdate(desc="Updated")

    with pytest.raises(NotFoundException) as exc_info:
        ResourceService.update(db, "non-existent-id", update_data)

    assert "not found" in str(exc_info.value)


def test_delete_resource(db):
    """Test deleting a resource."""
    # Create first
    resource_data = ResourceCreate(
        name="delete-test",
        type=ResourceType.BUILD
    )
    created = ResourceService.create(db, resource_data)

    # Delete
    result = ResourceService.delete(db, created.id)

    assert result is True

    # Verify deleted
    resource = ResourceService.get_by_id(db, created.id)
    assert resource is None


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


def test_resource_all_types(db):
    """Test creating resources of all types."""
    types = [ResourceType.BUILD, ResourceType.GATEWAY, ResourceType.THIRD]

    for resource_type in types:
        resource_data = ResourceCreate(
            name=f"type-test-{resource_type}",
            type=resource_type
        )
        resource = ResourceService.create(db, resource_data)
        assert resource.type == resource_type


def test_update_multiple_fields(db):
    """Test updating multiple fields at once."""
    # Create resource
    resource_data = ResourceCreate(
        name="multi-update-test",
        type=ResourceType.BUILD,
        desc="Original",
        url="http://original.com"
    )
    created = ResourceService.create(db, resource_data)

    # Update multiple fields
    update_data = ResourceUpdate(
        desc="Updated description",
        url="http://updated.com",
        ext={"new": "data"}
    )
    updated = ResourceService.update(db, created.id, update_data)

    assert updated.desc == "Updated description"
    assert updated.url == "http://updated.com"
