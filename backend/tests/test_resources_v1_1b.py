"""Unit tests for resource management module (v1.1b update).

This module contains tests for resource CRUD operations including:
- Creating resources with view_scope
- MCP resource creation
- Basic CRUD operations

Note: User ownership and access control features are not yet implemented.
Tests for those features are marked as skipped.
"""
import pytest
from models.resource import Resource, ResourceType
from models.user import User
from schemas.resource import ResourceCreate, ResourceUpdate, ViewScope, MCPConfig, MCPServerType
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

    resource = ResourceService.create(db, resource_data)

    assert resource.id is not None
    assert resource.name == "test-resource"
    assert resource.desc == "Test resource description"
    assert resource.type == ResourceType.GATEWAY
    assert resource.url == "http://example.com"
    assert resource.view_scope == ViewScope.PRIVATE  # default is private


def test_create_private_resource(db, test_user):
    """Test private resource creation."""
    resource_data = ResourceCreate(
        name="private-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.view_scope == ViewScope.PRIVATE


def test_create_public_resource(db, test_user):
    """Test public resource creation."""
    resource_data = ResourceCreate(
        name="public-resource",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PUBLIC
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.view_scope == ViewScope.PUBLIC


def test_create_mcp_resource_stdio(db, test_user):
    """Test MCP resource creation with STDIO transport."""
    resource_data = ResourceCreate(
        name="mcp-stdio-resource",
        type=ResourceType.MCP,
        view_scope=ViewScope.PUBLIC,
        ext={
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-example"],
            "timeout": 30000
        }
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.type == ResourceType.MCP
    assert resource.ext is not None
    assert resource.ext.get("transport") == "stdio"
    assert resource.ext.get("command") == "npx"


def test_create_mcp_resource_sse(db, test_user):
    """Test MCP resource creation with SSE transport."""
    resource_data = ResourceCreate(
        name="mcp-sse-resource",
        type=ResourceType.MCP,
        view_scope=ViewScope.PUBLIC,
        ext={
            "transport": "sse",
            "endpoint": "http://localhost:3000/sse",
            "timeout": 30000
        }
    )

    resource = ResourceService.create(db, resource_data)

    assert resource.type == ResourceType.MCP
    assert resource.ext is not None
    assert resource.ext.get("transport") == "sse"
    assert resource.ext.get("endpoint") == "http://localhost:3000/sse"


def test_duplicate_name(db, test_user):
    """Test that duplicate resource names are rejected."""
    resource_data = ResourceCreate(
        name="duplicate-test",
        type=ResourceType.GATEWAY
    )

    # Create first resource
    ResourceService.create(db, resource_data)

    # Try to create duplicate
    with pytest.raises(ValidationException) as exc_info:
        ResourceService.create(db, resource_data)

    assert "already exists" in str(exc_info.value)


def test_get_resource_by_id(db, test_user):
    """Test getting a resource by ID."""
    resource_data = ResourceCreate(
        name="get-test",
        type=ResourceType.GATEWAY,
        desc="Get test resource"
    )
    created = ResourceService.create(db, resource_data)

    # Get resource by ID
    resource = ResourceService.get_by_id(db, created.id)

    assert resource is not None
    assert resource.name == "get-test"
    assert resource.desc == "Get test resource"


def test_get_resource_by_name(db, test_user):
    """Test getting resource by name."""
    resource_data = ResourceCreate(
        name="unique-name-test",
        type=ResourceType.GATEWAY
    )
    ResourceService.create(db, resource_data)

    resource = ResourceService.get_by_name(db, "unique-name-test")
    assert resource is not None
    assert resource.name == "unique-name-test"


def test_update_resource(db, test_user):
    """Test updating a resource."""
    resource_data = ResourceCreate(
        name="update-test",
        type=ResourceType.GATEWAY,
        desc="Original description"
    )
    created = ResourceService.create(db, resource_data)

    # Update
    update_data = ResourceUpdate(desc="Updated description")
    updated = ResourceService.update(db, created.id, update_data)

    assert updated.desc == "Updated description"


def test_update_duplicate_name(db, test_user):
    """Test updating to duplicate name raises error."""
    ResourceService.create(db, ResourceCreate(
        name="resource-1",
        type=ResourceType.GATEWAY
    ))

    resource2 = ResourceService.create(db, ResourceCreate(
        name="resource-2",
        type=ResourceType.GATEWAY
    ))

    # Try to rename to existing name
    with pytest.raises(ValidationException):
        ResourceService.update(db, resource2.id, ResourceUpdate(name="resource-1"))


def test_update_view_scope(db, test_user):
    """Test updating resource view_scope."""
    resource_data = ResourceCreate(
        name="scope-test",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    )
    created = ResourceService.create(db, resource_data)

    # Update to public
    update_data = ResourceUpdate(view_scope=ViewScope.PUBLIC)
    updated = ResourceService.update(db, created.id, update_data)

    assert updated.view_scope == ViewScope.PUBLIC


def test_delete_resource(db, test_user):
    """Test deleting a resource."""
    resource_data = ResourceCreate(
        name="delete-test",
        type=ResourceType.GATEWAY
    )
    created = ResourceService.create(db, resource_data)

    # Delete
    result = ResourceService.delete(db, created.id)
    assert result is True

    # Verify deleted
    resource = ResourceService.get_by_id(db, created.id)
    assert resource is None


def test_delete_nonexistent_resource(db, test_user):
    """Test deleting non-existent resource raises error."""
    with pytest.raises(NotFoundException):
        ResourceService.delete(db, "non-existent-id")


def test_count_resources(db, test_user):
    """Test counting resources."""
    ResourceService.create(db, ResourceCreate(
        name="resource-1",
        type=ResourceType.GATEWAY
    ))

    ResourceService.create(db, ResourceCreate(
        name="resource-2",
        type=ResourceType.THIRD
    ))

    count = ResourceService.count_all(db)
    assert count >= 2


def test_count_by_view_scope(db, test_user):
    """Test counting resources by view_scope."""
    ResourceService.create(db, ResourceCreate(
        name="public-1",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PUBLIC
    ))

    ResourceService.create(db, ResourceCreate(
        name="private-1",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    ))

    public_count = ResourceService.count_by_view_scope(db, "public")
    private_count = ResourceService.count_by_view_scope(db, "private")

    assert public_count >= 1
    assert private_count >= 1


def test_list_by_type(db, test_user):
    """Test listing resources by type."""
    ResourceService.create(db, ResourceCreate(
        name="gateway-1",
        type=ResourceType.GATEWAY
    ))

    ResourceService.create(db, ResourceCreate(
        name="third-1",
        type=ResourceType.THIRD
    ))

    gateway_resources = ResourceService.list_by_type(db, ResourceType.GATEWAY.value)
    gateway_names = [r.name for r in gateway_resources]

    assert "gateway-1" in gateway_names
    assert "third-1" not in gateway_names


def test_list_by_view_scope(db, test_user):
    """Test listing resources by view_scope."""
    ResourceService.create(db, ResourceCreate(
        name="public-1",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PUBLIC
    ))

    ResourceService.create(db, ResourceCreate(
        name="private-1",
        type=ResourceType.GATEWAY,
        view_scope=ViewScope.PRIVATE
    ))

    public_resources = ResourceService.list_by_view_scope(db, "public")
    public_names = [r.name for r in public_resources]

    assert "public-1" in public_names
    assert "private-1" not in public_names


def test_get_mcp_resources(db, test_user):
    """Test getting MCP type resources."""
    ResourceService.create(db, ResourceCreate(
        name="mcp-1",
        type=ResourceType.MCP,
        ext={"transport": "stdio", "command": "node"}
    ))

    ResourceService.create(db, ResourceCreate(
        name="gateway-1",
        type=ResourceType.GATEWAY
    ))

    mcp_resources = ResourceService.get_mcp_resources(db)
    mcp_names = [r.name for r in mcp_resources]

    assert "mcp-1" in mcp_names
    assert "gateway-1" not in mcp_names


def test_list_all_with_pagination(db, test_user):
    """Test listing all resources with pagination."""
    # Create 5 resources
    for i in range(5):
        ResourceService.create(db, ResourceCreate(
            name=f"resource-{i}",
            type=ResourceType.GATEWAY
        ))

    # Get first page
    page1 = ResourceService.list_all(db, skip=0, limit=2)
    assert len(page1) == 2

    # Get second page
    page2 = ResourceService.list_all(db, skip=2, limit=2)
    assert len(page2) == 2


# --- Skipped tests for features not yet implemented ---

@pytest.mark.skip(reason="User ownership not yet implemented - Resource model lacks owner_id field")
def test_private_resource_ownership(db, test_user):
    """Test that private resources have owner set."""
    pass


@pytest.mark.skip(reason="get_accessible method not yet implemented in ResourceService")
def test_get_accessible_resource(db, test_user):
    """Test getting resource with access control."""
    pass


@pytest.mark.skip(reason="list_accessible method not yet implemented in ResourceService")
def test_list_accessible_resources(db, test_user):
    """Test listing resources accessible to user."""
    pass


@pytest.mark.skip(reason="User-based access control not yet implemented")
def test_private_resource_access_control(db, test_user):
    """Test that users cannot access others' private resources."""
    pass
