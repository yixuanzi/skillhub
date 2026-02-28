"""Unit tests for resource ACL management module.

This module contains tests for resource ACL operations including:
- Creating ACL rules
- Retrieving ACL rules by ID and resource ID
- Listing ACL rules with pagination and mode filtering
- Updating ACL rules
- Deleting ACL rules
- Managing role bindings
- Checking user permissions
"""
import pytest
from models.acl import ACLRule, ACLRuleRole, AccessMode
from models.resource import Resource
from models.user import User, Role
from schemas.acl_resource import (
    ACLRuleCreate,
    ACLRuleUpdate,
    RoleBindingCreate,
    ConditionSchema,
    PermissionCheckRequest
)
from services.acl_resource_service import ACLResourceService
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
        # Clean up after each test
        db.query(ACLRuleRole).delete()
        db.query(ACLRule).delete()
        db.query(Resource).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def test_resource(db):
    """Create a test resource."""
    from services.resource_service import ResourceService
    from schemas.resource import ResourceCreate, ResourceType

    resource_data = ResourceCreate(
        name="test-acl-resource",
        type=ResourceType.BUILD,
        desc="Test resource for ACL"
    )
    return ResourceService.create(db, resource_data)


@pytest.fixture(scope="function")
def test_role(db):
    """Create a test role."""
    role = Role(name="test-role", description="Test role for ACL")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture(scope="function")
def test_user(db, test_role):
    """Create a test user with a role."""
    from services.auth_service import AuthService
    from schemas.auth import UserCreate

    user_data = UserCreate(
        username="testuser_acl",
        email="test_acl@example.com",
        password="testpassword123"
    )
    user_response = AuthService.register(db, user_data)

    # Get the actual User model from database
    user = db.query(User).filter(User.id == user_response.id).first()
    user.roles.append(test_role)
    db.commit()
    db.refresh(user)
    return user


def test_create_acl_rule_any_mode(db, test_resource):
    """Test creating ACL rule with ANY access mode."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )

    acl_rule = ACLResourceService.create(db, acl_data)

    assert acl_rule.id is not None
    assert acl_rule.resource_id == test_resource.id
    assert acl_rule.access_mode == AccessMode.ANY


def test_create_acl_rule_rbac_mode(db, test_resource, test_role):
    """Test creating ACL rule with RBAC access mode."""
    role_binding = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read", "write"]
    )

    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        role_bindings=[role_binding]
    )

    acl_rule = ACLResourceService.create(db, acl_data)

    assert acl_rule.id is not None
    assert acl_rule.access_mode == AccessMode.RBAC
    assert len(acl_rule.role_bindings) == 1
    assert acl_rule.role_bindings[0].role_id == test_role.id


def test_create_acl_rule_with_conditions(db, test_resource):
    """Test creating ACL rule with conditions."""
    conditions = ConditionSchema(
        users=["user-1", "user-2"],
        roles=["role-1", "role-2"],
        ip_whitelist=["192.168.1.0/24"],
        rate_limit={"requests": 100, "window": 60}
    )

    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        conditions=conditions
    )

    acl_rule = ACLResourceService.create(db, acl_data)

    assert acl_rule.conditions is not None
    assert "users" in acl_rule.conditions
    assert "roles" in acl_rule.conditions
    assert "ip_whitelist" in acl_rule.conditions
    assert "rate_limit" in acl_rule.conditions


def test_create_duplicate_acl_rule(db, test_resource):
    """Test that duplicate ACL rules for the same resource are rejected."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )

    # Create first ACL rule
    ACLResourceService.create(db, acl_data)

    # Try to create duplicate
    with pytest.raises(ValidationException) as exc_info:
        ACLResourceService.create(db, acl_data)

    assert "already exists" in str(exc_info.value).lower()


def test_get_acl_rule_by_id(db, test_resource):
    """Test getting ACL rule by ID."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data)

    # Get by ID
    acl_rule = ACLResourceService.get_by_id(db, created.id)

    assert acl_rule is not None
    assert acl_rule.id == created.id
    assert acl_rule.resource_id == test_resource.id


def test_get_acl_rule_by_resource_id(db, test_resource):
    """Test getting ACL rule by resource ID."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data)

    # Get by resource ID
    acl_rule = ACLResourceService.get_by_resource_id(db, test_resource.id)

    assert acl_rule is not None
    assert acl_rule.resource_id == test_resource.id


def test_list_all_acl_rules(db, test_resource):
    """Test listing all ACL rules."""
    # Create multiple ACL rules
    for i in range(3):
        from services.resource_service import ResourceService
        from schemas.resource import ResourceCreate, ResourceType

        resource = ResourceService.create(
            db,
            ResourceCreate(name=f"test-resource-{i}", type=ResourceType.BUILD)
        )

        acl_data = ACLRuleCreate(
            resource_id=resource.id,
            resource_name=f"test-resource-{i}",
            access_mode=AccessMode.ANY
        )
        ACLResourceService.create(db, acl_data)

    # List all
    acl_rules = ACLResourceService.list_all(db)

    assert len(acl_rules) >= 3


def test_list_acl_rules_with_pagination(db, test_resource):
    """Test listing ACL rules with pagination."""
    # Create multiple ACL rules
    for i in range(5):
        from services.resource_service import ResourceService
        from schemas.resource import ResourceCreate, ResourceType

        resource = ResourceService.create(
            db,
            ResourceCreate(name=f"page-resource-{i}", type=ResourceType.BUILD)
        )

        acl_data = ACLRuleCreate(
            resource_id=resource.id,
            resource_name=f"page-resource-{i}",
            access_mode=AccessMode.ANY
        )
        ACLResourceService.create(db, acl_data)

    # Get first page
    page1 = ACLResourceService.list_all(db, skip=0, limit=3)
    assert len(page1) == 3

    # Get second page
    page2 = ACLResourceService.list_all(db, skip=3, limit=3)
    assert len(page2) == 2


def test_list_acl_rules_by_mode(db, test_resource):
    """Test listing ACL rules by access mode."""
    # Create ACL rules with different modes
    acl_data_any = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data_any)

    from services.resource_service import ResourceService
    from schemas.resource import ResourceCreate, ResourceType

    resource2 = ResourceService.create(
        db,
        ResourceCreate(name="test-resource-2", type=ResourceType.BUILD)
    )
    acl_data_rbac = ACLRuleCreate(
        resource_id=resource2.id,
        resource_name="test-resource-2",
        access_mode=AccessMode.RBAC
    )
    ACLResourceService.create(db, acl_data_rbac)

    # List by ANY mode
    any_rules = ACLResourceService.list_by_mode(db, AccessMode.ANY)
    assert len(any_rules) >= 1
    assert all(rule.access_mode == AccessMode.ANY for rule in any_rules)

    # List by RBAC mode
    rbac_rules = ACLResourceService.list_by_mode(db, AccessMode.RBAC)
    assert len(rbac_rules) >= 1
    assert all(rule.access_mode == AccessMode.RBAC for rule in rbac_rules)


def test_count_acl_rules(db, test_resource):
    """Test counting ACL rules."""
    initial_count = ACLResourceService.count_all(db)

    # Create 2 ACL rules
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data)

    from services.resource_service import ResourceService
    from schemas.resource import ResourceCreate, ResourceType

    resource2 = ResourceService.create(
        db,
        ResourceCreate(name="test-resource-2", type=ResourceType.BUILD)
    )
    acl_data2 = ACLRuleCreate(
        resource_id=resource2.id,
        resource_name="test-resource-2",
        access_mode=AccessMode.RBAC
    )
    ACLResourceService.create(db, acl_data2)

    new_count = ACLResourceService.count_all(db)
    assert new_count == initial_count + 2


def test_update_acl_rule(db, test_resource):
    """Test updating ACL rule."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data)

    # Update access mode
    update_data = ACLRuleUpdate(access_mode=AccessMode.RBAC)
    updated = ACLResourceService.update(db, created.id, update_data)

    assert updated.access_mode == AccessMode.RBAC


def test_update_acl_rule_conditions(db, test_resource):
    """Test updating ACL rule conditions."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    created = ACLResourceService.create(db, acl_data)

    # Update conditions
    new_conditions = ConditionSchema(
        users=["user-1"],
        ip_whitelist=["10.0.0.1"]
    )
    update_data = ACLRuleUpdate(conditions=new_conditions)
    updated = ACLResourceService.update(db, created.id, update_data)

    assert updated.conditions is not None
    assert "users" in updated.conditions
    assert "ip_whitelist" in updated.conditions


def test_delete_acl_rule(db, test_resource):
    """Test deleting ACL rule."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data)

    # Delete
    result = ACLResourceService.delete(db, created.id)
    assert result is True

    # Verify deleted
    acl_rule = ACLResourceService.get_by_id(db, created.id)
    assert acl_rule is None


def test_add_role_binding(db, test_resource, test_role):
    """Test adding role binding to ACL rule."""
    # Create ACL rule
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data)

    # Add role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read", "write"]
    )
    binding = ACLResourceService.add_role_binding(db, acl_rule.id, binding_data)

    assert binding.id is not None
    assert binding.role_id == test_role.id
    assert binding.permissions == ["read", "write"]


def test_add_duplicate_role_binding(db, test_resource, test_role):
    """Test that duplicate role bindings are rejected."""
    # Create ACL rule
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data)

    # Add first role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read"]
    )
    ACLResourceService.add_role_binding(db, acl_rule.id, binding_data)

    # Try to add duplicate
    with pytest.raises(ValidationException) as exc_info:
        ACLResourceService.add_role_binding(db, acl_rule.id, binding_data)

    assert "already exists" in str(exc_info.value).lower()


def test_remove_role_binding(db, test_resource, test_role):
    """Test removing role binding from ACL rule."""
    # Create ACL rule with role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read"]
    )
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        role_bindings=[binding_data]
    )
    acl_rule = ACLResourceService.create(db, acl_data)

    # Remove role binding
    result = ACLResourceService.remove_role_binding(db, acl_rule.id, test_role.id)
    assert result is True

    # Verify removed
    updated_acl = ACLResourceService.get_by_id(db, acl_rule.id)
    assert len(updated_acl.role_bindings) == 0


def test_update_role_binding(db, test_resource, test_role):
    """Test updating role binding permissions."""
    # Create ACL rule with role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read"]
    )
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        role_bindings=[binding_data]
    )
    acl_rule = ACLResourceService.create(db, acl_data)

    # Update permissions
    updated_binding = ACLResourceService.update_role_binding(
        db,
        acl_rule.id,
        test_role.id,
        ["read", "write", "delete"]
    )

    assert updated_binding.permissions == ["read", "write", "delete"]


def test_check_permission_any_mode(db, test_resource):
    """Test permission check with ANY access mode."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data)

    # Check permission
    check_data = PermissionCheckRequest(
        user_id="any-user-id",
        required_permission="read"
    )
    result = ACLResourceService.check_permission(db, test_resource.id, check_data)

    assert result.allowed is True
    assert "public" in result.reason.lower()


def test_check_permission_rbac_with_role(db, test_resource, test_role, test_user):
    """Test permission check with RBAC and role binding."""
    # Create ACL rule with role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read", "write"]
    )
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        role_bindings=[binding_data]
    )
    ACLResourceService.create(db, acl_data)

    # Check permission with valid permission
    check_data = PermissionCheckRequest(
        user_id=test_user.id,
        required_permission="read"
    )
    result = ACLResourceService.check_permission(db, test_resource.id, check_data)

    assert result.allowed is True

    # Check permission with invalid permission
    check_data2 = PermissionCheckRequest(
        user_id=test_user.id,
        required_permission="delete"
    )
    result2 = ACLResourceService.check_permission(db, test_resource.id, check_data2)

    assert result2.allowed is False


def test_check_permission_with_user_whitelist(db, test_resource, test_user):
    """Test permission check with user whitelist in conditions."""
    conditions = ConditionSchema(
        users=[test_user.id]
    )
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        conditions=conditions
    )
    ACLResourceService.create(db, acl_data)

    # Check permission for whitelisted user
    check_data = PermissionCheckRequest(
        user_id=test_user.id,
        required_permission="read"
    )
    result = ACLResourceService.check_permission(db, test_resource.id, check_data)

    assert result.allowed is True
    assert "whitelist" in result.reason.lower()


def test_check_permission_no_acl_rule(db, test_resource):
    """Test permission check when no ACL rule exists."""
    check_data = PermissionCheckRequest(
        user_id="any-user-id",
        required_permission="read"
    )
    result = ACLResourceService.check_permission(db, test_resource.id, check_data)

    assert result.allowed is False
    assert "no acl rule" in result.reason.lower()


def test_create_acl_rule_nonexistent_resource(db):
    """Test creating ACL rule for non-existent resource."""
    acl_data = ACLRuleCreate(
        resource_id="non-existent-resource-id",
        resource_name="non-existent",
        access_mode=AccessMode.ANY
    )

    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.create(db, acl_data)

    assert "not found" in str(exc_info.value).lower()


def test_update_nonexistent_acl_rule(db):
    """Test updating non-existent ACL rule."""
    update_data = ACLRuleUpdate(access_mode=AccessMode.RBAC)

    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.update(db, "non-existent-id", update_data)

    assert "not found" in str(exc_info.value).lower()


def test_delete_nonexistent_acl_rule(db):
    """Test deleting non-existent ACL rule."""
    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.delete(db, "non-existent-id")

    assert "not found" in str(exc_info.value).lower()


def test_add_role_binding_nonexistent_role(db, test_resource):
    """Test adding role binding with non-existent role."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data)

    binding_data = RoleBindingCreate(
        role_id="non-existent-role-id",
        permissions=["read"]
    )

    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.add_role_binding(db, acl_rule.id, binding_data)

    assert "not found" in str(exc_info.value).lower()
