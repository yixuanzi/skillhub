"""Unit tests for gateway module.

This module contains tests for gateway operations including:
- Permission checking before resource invocation
- Resource lookup and invocation
- Error handling for permission denied and resource not found
- Different HTTP methods (GET, POST, PUT, DELETE)
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from models.resource import Resource, ResourceType
from models.user import User, Role
from schemas.acl_resource import ACLRuleCreate, RoleBindingCreate
from schemas.gateway import GatewayCallRequest
from services.gateway_service import GatewayService
from core.exceptions import NotFoundException, ValidationException
from database import SessionLocal


@pytest.fixture(scope="function")
def db():
    """Create a new database session for each test."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    finally:
        # Clean up after each test
        from models.acl import ACLRule, ACLRuleRole
        db.query(ACLRuleRole).delete()
        db.query(ACLRule).delete()
        db.query(Resource).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user."""
    from services.auth_service import AuthService
    from schemas.auth import UserCreate

    user_data = UserCreate(
        username="gateway_user",
        email="gateway@example.com",
        password="testpassword123"
    )
    user_response = AuthService.register(db, user_data)
    user = db.query(User).filter(User.id == user_response.id).first()
    return user


@pytest.fixture(scope="function")
def test_role(db):
    """Create a test role."""
    role = Role(name="gateway-role", description="Test role for gateway")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture(scope="function")
def build_resource(db):
    """Create a test build resource."""
    from services.resource_service import ResourceService
    from schemas.resource import ResourceCreate

    resource_data = ResourceCreate(
        name="test-build-api",
        type=ResourceType.BUILD,
        url="https://api.example.com/test",
        ext={"timeout": 10, "headers": {"X-Custom": "value"}}
    )
    return ResourceService.create(db, resource_data)


@pytest.fixture(scope="function")
def acl_rule_with_permission(db, build_resource, test_role):
    """Create ACL rule allowing access to the resource."""
    from services.acl_resource_service import ACLResourceService
    from models.acl import AccessMode

    role_binding = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["execute"]
    )

    acl_data = ACLRuleCreate(
        resource_id=build_resource.id,
        resource_name=build_resource.name,
        access_mode=AccessMode.RBAC,
        role_bindings=[role_binding]
    )
    return ACLResourceService.create(db, acl_data)


@pytest.mark.asyncio
async def test_gateway_call_success(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test successful gateway call with permission."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success", "data": "test data"}
    mock_response.text = '{"result": "success"}'

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET"
        )

        assert result["success"] is True
        assert result["resource_name"] == build_resource.name
        assert result["resource_type"] == "build"
        assert result["status_code"] == 200
        assert result["data"]["result"] == "success"


@pytest.mark.asyncio
async def test_gateway_call_with_post(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test gateway call with POST method."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"created": True}
    mock_response.text = '{"created": true}'

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="POST",
            body={"name": "test", "value": "data"}
        )

        assert result["success"] is True
        assert result["status_code"] == 201
        assert result["data"]["created"] is True


@pytest.mark.asyncio
async def test_gateway_call_permission_denied(db, test_user, build_resource):
    """Test gateway call with permission denied."""
    # No ACL rule created, user has no permission
    result = await GatewayService.call_resource(
        db=db,
        resource_name=build_resource.name,
        user=test_user,
        method="GET"
    )

    assert result["success"] is False
    assert result["error_type"] == "permission_denied"
    assert "denied" in result["error"].lower()


@pytest.mark.asyncio
async def test_gateway_call_resource_not_found(db, test_user):
    """Test gateway call with non-existent resource."""
    result = await GatewayService.call_resource(
        db=db,
        resource_name="non-existent-resource",
        user=test_user,
        method="GET"
    )

    assert result["success"] is False
    assert result["error_type"] == "resource_not_found"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_gateway_call_insufficient_permissions(db, test_user, test_role, build_resource):
    """Test gateway call with insufficient permissions (read instead of execute)."""
    from services.acl_resource_service import ACLResourceService
    from models.acl import AccessMode

    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()

    # Create ACL rule with only 'read' permission, not 'execute'
    role_binding = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read"]  # No 'execute' permission
    )

    acl_data = ACLRuleCreate(
        resource_id=build_resource.id,
        resource_name=build_resource.name,
        access_mode=AccessMode.RBAC,
        role_bindings=[role_binding]
    )
    ACLResourceService.create(db, acl_data)

    result = await GatewayService.call_resource(
        db=db,
        resource_name=build_resource.name,
        user=test_user,
        method="GET"
    )

    assert result["success"] is False
    assert result["error_type"] == "permission_denied"


@pytest.mark.asyncio
async def test_gateway_call_any_mode(db, test_user, build_resource):
    """Test gateway call with ANY access mode (public access)."""
    from services.acl_resource_service import ACLResourceService
    from models.acl import AccessMode

    # Create ACL rule with ANY mode (no authentication required)
    acl_data = ACLRuleCreate(
        resource_id=build_resource.id,
        resource_name=build_resource.name,
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"public": "data"}

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET"
        )

        assert result["success"] is True
        assert result["data"]["public"] == "data"


@pytest.mark.asyncio
async def test_gateway_call_with_user_whitelist(db, test_user, build_resource):
    """Test gateway call with user whitelist in conditions."""
    from services.acl_resource_service import ACLResourceService
    from models.acl import AccessMode
    from schemas.acl_resource import ConditionSchema

    # Create ACL rule with user whitelist
    conditions = ConditionSchema(
        users=[str(test_user.id)]
    )
    acl_data = ACLRuleCreate(
        resource_id=build_resource.id,
        resource_name=build_resource.name,
        access_mode=AccessMode.RBAC,
        conditions=conditions
    )
    ACLResourceService.create(db, acl_data)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"whitelisted": "user"}

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET"
        )

        assert result["success"] is True
        assert result["data"]["whitelisted"] == "user"


@pytest.mark.asyncio
async def test_gateway_call_http_timeout(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test gateway call with HTTP timeout."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException(
            "Request timed out"
        )

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET"
        )

        assert result["success"] is False
        assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_gateway_call_http_error(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test gateway call with HTTP error."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.HTTPError(
            "Connection error"
        )

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET"
        )

        assert result["success"] is False
        assert "http error" in result["error"].lower()


@pytest.mark.asyncio
async def test_gateway_call_with_headers(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test gateway call with custom headers."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"headers": "received"}

    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET",
            headers={"X-Custom-Header": "custom-value"}
        )

        assert result["success"] is True
        # Verify the call was made with custom headers
        call_args = mock_get.call_args
        headers = call_args[1].get("headers") if call_args else None
        assert headers is not None
        assert "X-Custom-Header" in headers or "X-Custom" in headers  # May have resource headers merged


@pytest.mark.asyncio
async def test_gateway_call_with_params(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test gateway call with query parameters."""
    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"params": "received"}

    with patch('httpx.AsyncClient') as mock_client:
        mock_get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await GatewayService.call_resource(
            db=db,
            resource_name=build_resource.name,
            user=test_user,
            method="GET",
            params={"key1": "value1", "key2": "value2"}
        )

        assert result["success"] is True
        # Verify the call was made with query parameters
        call_args = mock_get.call_args
        params = call_args[1].get("params") if call_args else None
        assert params is not None


def test_gateway_execution_time_tracking(db, test_user, test_role, build_resource, acl_rule_with_permission):
    """Test that gateway calls track execution time."""
    import asyncio

    # Assign role to user
    test_user.roles.append(test_role)
    db.commit()
    db.refresh(test_user)

    async def run_test():
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await GatewayService.call_resource(
                db=db,
                resource_name=build_resource.name,
                user=test_user,
                method="GET"
            )

            assert result["success"] is True
            assert result["execution_time_ms"] is not None
            assert result["execution_time_ms"] >= 0

    asyncio.run(run_test())
