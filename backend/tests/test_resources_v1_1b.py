"""Unit tests for resource management module (v1.1b update).

This module contains tests for resource CRUD operations including:
- Creating resources with view_scope
- Retrieving resources by ID with access control
- Listing accessible resources
- Updating resources
- Deleting resources
"""
import pytest
from models.resource import Resource, ResourceType
from models.user import User
from schemas.resource import ResourceCreate, ResourceUpdate, ViewScope
from services.resource_service import ResourceService
from core.exceptions import ValidationException, NotFoundException
from core.security import get_password_hash
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
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_resource(db, test_user):
    """Test resource creation with view_scope."""
    resource_data = ResourceCreate(
        name="test-resource",
        desc="Test resource description",
        type=ResourceType.GATEWAY,
        url="http://example.com"
    )

    resource = ResourceService.create(db, resource_data, test_user)

    assert resource.id is not None
    assert resource.name == "test-resource"
    assert resource.desc == "Test resource description"
    assert resource.type == ResourceType.GATEWAY
    assert resource.url == "http://example.com"
    assert resource.view_scope == ViewScope.PUBLIC  # default


def test_create_private_resource(db, test_user):
    """Test private resource creation sets owner."""
    resource_data = ResourceCreate(
        name="private-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )

    resource = ResourceService.create(db, resource_data, test_user)

    assert resource.view_scope == ViewScope.PRIVATE
    assert resource.owner_id == test_user.id


def test_create_mcp_resource(db, test_user):
    """Test MCP resource creation with config."""
    from schemas.resource import MCPConfig, MCPServerType

    resource_data = ResourceCreate(
        name="mcp-resource",
        type=ResourceType.MCP,
        view_scope=ViewScope.PUBLIC,
        mcp_config=MCPConfig(
            transport=MCPServerType.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-example"]
        )
    )

    resource = ResourceService.create(db, resource_data, test_user)

    assert resource.type == ResourceType.MCP
    # MCP config is stored in ext field
    assert resource.ext is not None
    assert resource.ext.get("transport") == "stdio"


def test_create_mcp_resource_without_config_raises_error(db, test_user):
    """Test that MCP resource without config raises error."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ResourceCreate(
            name="invalid-mcp",
            type=ResourceType.MCP,
            # Missing mcp_config
        )


def test_duplicate_name(db, test_user):
    """Test that duplicate resource names are rejected."""
    resource_data = ResourceCreate(
        name="duplicate-test",
        type=ResourceType.GATEWAY
    )

    # Create first resource
    ResourceService.create(db, resource_data, test_user)

    # Try to create duplicate
    with pytest.raises(ValidationException) as exc_info:
        ResourceService.create(db, resource_data, test_user)

    assert "already exists" in str(exc_info.value)


def test_get_resource(db, test_user):
    """Test getting a resource by ID."""
    resource_data = ResourceCreate(
        name="get-test",
        type=ResourceType.GATEWAY,
        desc="Get test resource"
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Get accessible resource
    resource = ResourceService.get_accessible(db, created.id, test_user)

    assert resource is not None
    assert resource.name == "get-test"
    assert resource.desc == "Get test resource"


def test_get_private_resource_as_owner(db, test_user):
    """Test owner can access private resource."""
    resource_data = ResourceCreate(
        name="private-test",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Owner can access
    resource = ResourceService.get_accessible(db, created.id, test_user)
    assert resource.name == "private-test"


def test_get_private_resource_as_other_user_raises_error(db, test_user):
    """Test other user cannot access private resource."""
    # Create private resource as test_user
    resource_data = ResourceCreate(
        name="private-test",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Create another user
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(other_user)
    db.commit()

    # Other user cannot access
    with pytest.raises(ValidationException) as exc_info:
        ResourceService.get_accessible(db, created.id, other_user)

    assert "no access" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()


def test_get_public_resource_as_any_user(db, test_user):
    """Test any user can access public resource."""
    resource_data = ResourceCreate(
        name="public-test",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PUBLIC
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Create another user
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(other_user)
    db.commit()

    # Other user can access public resource
    resource = ResourceService.get_accessible(db, created.id, other_user)
    assert resource.name == "public-test"


def test_list_accessible_resources(db, test_user):
    """Test listing accessible resources."""
    # Create public resource
    ResourceService.create(db, ResourceCreate(
        name="public-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PUBLIC
    ), test_user)

    # Create private resource
    ResourceService.create(db, ResourceCreate(
        name="private-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    ), test_user)

    # List accessible - should return both (owner of private)
    resources = ResourceService.list_accessible(db, test_user)
    resource_names = [r.name for r in resources]

    assert "public-resource" in resource_names
    assert "private-resource" in resource_names


def test_update_resource(db, test_user):
    """Test updating a resource."""
    resource_data = ResourceCreate(
        name="update-test",
        type=ResourceType.GATEWAY,
        desc="Original description"
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Update
    update_data = ResourceUpdate(desc="Updated description")
    updated = ResourceService.update(db, created.id, update_data, test_user)

    assert updated.desc == "Updated description"


def test_update_duplicate_name(db, test_user):
    """Test updating to duplicate name raises error."""
    ResourceService.create(db, ResourceCreate(
        name="resource-1",
        type=ResourceType.GATEWAY
    ), test_user)

    resource2 = ResourceService.create(db, ResourceCreate(
        name="resource-2",
        type=ResourceType.GATEWAY
    ), test_user)

    # Try to rename to existing name
    with pytest.raises(ValidationException):
        ResourceService.update(db, resource2.id, ResourceUpdate(name="resource-1"), test_user)


def test_delete_resource(db, test_user):
    """Test deleting a resource as owner."""
    resource_data = ResourceCreate(
        name="delete-test",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE  # Private so owner_id is set
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Delete as owner
    result = ResourceService.delete(db, created.id, test_user)
    assert result is True

    # Verify deleted
    resource = ResourceService.get_by_id(db, created.id)
    assert resource is None


def test_delete_resource_by_non_owner_raises_error(db, test_user):
    """Test non-owner cannot delete private resource."""
    resource_data = ResourceCreate(
        name="protected-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )
    created = ResourceService.create(db, resource_data, test_user)

    # Create another user (not admin)
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    db.add(other_user)
    db.commit()

    # Try to delete - should fail
    with pytest.raises(ValidationException):
        ResourceService.delete(db, created.id, other_user)


def test_count_resources(db, test_user):
    """Test counting resources."""
    ResourceService.create(db, ResourceCreate(
        name="resource-1",
        type=ResourceType.GATEWAY
    ), test_user)

    ResourceService.create(db, ResourceCreate(
        name="resource-2",
        type=ResourceType.THIRD
    ), test_user)

    count = ResourceService.count_all(db)
    assert count >= 2


def test_get_by_name(db, test_user):
    """Test getting resource by name."""
    resource_data = ResourceCreate(
        name="unique-name-test",
        type=ResourceType.GATEWAY
    )
    ResourceService.create(db, resource_data, test_user)

    resource = ResourceService.get_by_name(db, "unique-name-test")
    assert resource is not None
    assert resource.name == "unique-name-test"


def test_list_by_type(db, test_user):
    """Test listing resources by type."""
    ResourceService.create(db, ResourceCreate(
        name="gateway-1",
        type=ResourceType.GATEWAY
    ), test_user)

    ResourceService.create(db, ResourceCreate(
        name="third-1",
        type=ResourceType.THIRD
    ), test_user)

    gateway_resources = ResourceService.list_by_type(db, ResourceType.GATEWAY.value)
    gateway_names = [r.name for r in gateway_resources]

    assert "gateway-1" in gateway_names
    assert "third-1" not in gateway_names
