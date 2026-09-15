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
def test_resource(db, acl_admin):
    """Create a test resource.

    The Resource row is created directly (rather than through
    ``ResourceService.create``) because that service now also auto-creates a
    default RBAC ACL rule for every new resource. These tests exercise ACL rule
    creation themselves, so they need a resource that starts with no ACL rule.
    """
    from models.resource import ResourceType

    resource = Resource(
        name="test-acl-resource",
        type=ResourceType.GATEWAY,
        desc="Test resource for ACL",
        view_scope="private",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def _make_resource(db, name: str):
    """Create a bare Resource row without any auto-generated ACL rule.

    ``ResourceService.create`` now also creates a default RBAC ACL rule for the
    new resource, which would collide with the rules these tests create.
    """
    from models.resource import ResourceType

    resource = Resource(
        name=name,
        type=ResourceType.GATEWAY,
        desc=f"Test resource {name}",
        view_scope="private",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@pytest.fixture(scope="function")
def acl_admin(db):
    """Create an admin user allowed to manage ACL rules for any resource."""
    admin_role = Role(name="admin", description="Administrator")
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

    user = User(
        username="acl_admin",
        email="acl_admin@example.com",
        hashed_password="not-used",
    )
    user.roles.append(admin_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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


def test_create_acl_rule_any_mode(db, test_resource, acl_admin):
    """Test creating ACL rule with ANY access mode."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )

    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    assert acl_rule.id is not None
    assert acl_rule.resource_id == test_resource.id
    assert acl_rule.access_mode == AccessMode.ANY


def test_create_acl_rule_rbac_mode(db, test_resource, test_role, acl_admin):
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

    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    assert acl_rule.id is not None
    assert acl_rule.access_mode == AccessMode.RBAC
    assert len(acl_rule.role_bindings) == 1
    assert acl_rule.role_bindings[0].role_id == test_role.id


def test_create_acl_rule_with_conditions(db, test_resource, acl_admin):
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

    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    assert acl_rule.conditions is not None
    assert "users" in acl_rule.conditions
    assert "roles" in acl_rule.conditions
    assert "ip_whitelist" in acl_rule.conditions
    assert "rate_limit" in acl_rule.conditions


def test_create_duplicate_acl_rule(db, test_resource, acl_admin):
    """Test that duplicate ACL rules for the same resource are rejected."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )

    # Create first ACL rule
    ACLResourceService.create(db, acl_data, acl_admin)

    # Try to create duplicate
    with pytest.raises(ValidationException) as exc_info:
        ACLResourceService.create(db, acl_data, acl_admin)

    assert "already exists" in str(exc_info.value).lower()


def test_get_acl_rule_by_id(db, test_resource, acl_admin):
    """Test getting ACL rule by ID."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data, acl_admin)

    # Get by ID
    acl_rule = ACLResourceService.get_by_id(db, created.id)

    assert acl_rule is not None
    assert acl_rule.id == created.id
    assert acl_rule.resource_id == test_resource.id


def test_get_acl_rule_by_resource_id(db, test_resource, acl_admin):
    """Test getting ACL rule by resource ID."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data, acl_admin)

    # Get by resource ID
    acl_rule = ACLResourceService.get_by_resource_id(db, test_resource.id)

    assert acl_rule is not None
    assert acl_rule.resource_id == test_resource.id


def test_list_all_acl_rules(db, test_resource, acl_admin):
    """Test listing all ACL rules."""
    # Create multiple ACL rules
    for i in range(3):
        resource = _make_resource(db, f"test-resource-{i}")

        acl_data = ACLRuleCreate(
            resource_id=resource.id,
            resource_name=f"test-resource-{i}",
            access_mode=AccessMode.ANY
        )
        ACLResourceService.create(db, acl_data, acl_admin)

    # List all
    acl_rules = ACLResourceService.list_all(db)

    assert len(acl_rules) >= 3


def test_list_acl_rules_with_pagination(db, test_resource, acl_admin):
    """Test listing ACL rules with pagination."""
    # Create multiple ACL rules
    for i in range(5):
        resource = _make_resource(db, f"page-resource-{i}")

        acl_data = ACLRuleCreate(
            resource_id=resource.id,
            resource_name=f"page-resource-{i}",
            access_mode=AccessMode.ANY
        )
        ACLResourceService.create(db, acl_data, acl_admin)

    # Get first page
    page1 = ACLResourceService.list_all(db, skip=0, limit=3)
    assert len(page1) == 3

    # Get second page
    page2 = ACLResourceService.list_all(db, skip=3, limit=3)
    assert len(page2) == 2


def test_list_acl_rules_by_mode(db, test_resource, acl_admin):
    """Test listing ACL rules by access mode."""
    # Create ACL rules with different modes
    acl_data_any = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data_any, acl_admin)

    resource2 = _make_resource(db, "test-resource-2")
    acl_data_rbac = ACLRuleCreate(
        resource_id=resource2.id,
        resource_name="test-resource-2",
        access_mode=AccessMode.RBAC
    )
    ACLResourceService.create(db, acl_data_rbac, acl_admin)

    # List by ANY mode
    any_rules = ACLResourceService.list_by_mode(db, AccessMode.ANY)
    assert len(any_rules) >= 1
    assert all(rule.access_mode == AccessMode.ANY for rule in any_rules)

    # List by RBAC mode
    rbac_rules = ACLResourceService.list_by_mode(db, AccessMode.RBAC)
    assert len(rbac_rules) >= 1
    assert all(rule.access_mode == AccessMode.RBAC for rule in rbac_rules)


def test_count_acl_rules(db, test_resource, acl_admin):
    """Test counting ACL rules."""
    initial_count = ACLResourceService.count_all(db)

    # Create 2 ACL rules
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data, acl_admin)

    resource2 = _make_resource(db, "test-resource-2")
    acl_data2 = ACLRuleCreate(
        resource_id=resource2.id,
        resource_name="test-resource-2",
        access_mode=AccessMode.RBAC
    )
    ACLResourceService.create(db, acl_data2, acl_admin)

    new_count = ACLResourceService.count_all(db)
    assert new_count == initial_count + 2


def test_update_acl_rule(db, test_resource, acl_admin):
    """Test updating ACL rule."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data, acl_admin)

    # Update access mode
    update_data = ACLRuleUpdate(access_mode=AccessMode.RBAC)
    updated = ACLResourceService.update(db, created.id, update_data, acl_admin)

    assert updated.access_mode == AccessMode.RBAC


def test_update_acl_rule_conditions(db, test_resource, acl_admin):
    """Test updating ACL rule conditions."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    created = ACLResourceService.create(db, acl_data, acl_admin)

    # Update conditions
    new_conditions = ConditionSchema(
        users=["user-1"],
        ip_whitelist=["10.0.0.1"]
    )
    update_data = ACLRuleUpdate(conditions=new_conditions)
    updated = ACLResourceService.update(db, created.id, update_data, acl_admin)

    assert updated.conditions is not None
    assert "users" in updated.conditions
    assert "ip_whitelist" in updated.conditions


def test_delete_acl_rule(db, test_resource, acl_admin):
    """Test deleting ACL rule."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    created = ACLResourceService.create(db, acl_data, acl_admin)

    # Delete
    result = ACLResourceService.delete(db, created.id, acl_admin)
    assert result is True

    # Verify deleted
    acl_rule = ACLResourceService.get_by_id(db, created.id)
    assert acl_rule is None


def test_add_role_binding(db, test_resource, test_role, acl_admin):
    """Test adding role binding to ACL rule."""
    # Create ACL rule
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    # Add role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read", "write"]
    )
    binding = ACLResourceService.add_role_binding(db, acl_rule.id, binding_data, acl_admin)

    assert binding.id is not None
    assert binding.role_id == test_role.id
    assert binding.permissions == ["read", "write"]


def test_add_duplicate_role_binding(db, test_resource, test_role, acl_admin):
    """Test that duplicate role bindings are rejected."""
    # Create ACL rule
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    # Add first role binding
    binding_data = RoleBindingCreate(
        role_id=test_role.id,
        permissions=["read"]
    )
    ACLResourceService.add_role_binding(db, acl_rule.id, binding_data, acl_admin)

    # Try to add duplicate
    with pytest.raises(ValidationException) as exc_info:
        ACLResourceService.add_role_binding(db, acl_rule.id, binding_data, acl_admin)

    assert "already exists" in str(exc_info.value).lower()


def test_remove_role_binding(db, test_resource, test_role, acl_admin):
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
    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    # Remove role binding
    result = ACLResourceService.remove_role_binding(db, acl_rule.id, test_role.id, acl_admin)
    assert result is True

    # Verify removed
    updated_acl = ACLResourceService.get_by_id(db, acl_rule.id)
    assert len(updated_acl.role_bindings) == 0


def test_update_role_binding(db, test_resource, test_role, acl_admin):
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
    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    # Update permissions
    updated_binding = ACLResourceService.update_role_binding(
        db,
        acl_rule.id,
        test_role.id,
        ["read", "write", "delete"],
        acl_admin
    )

    assert updated_binding.permissions == ["read", "write", "delete"]


def test_check_permission_any_mode(db, test_resource, acl_admin):
    """Test permission check with ANY access mode."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.ANY
    )
    ACLResourceService.create(db, acl_data, acl_admin)

    # Check permission
    check_data = PermissionCheckRequest(
        user_id="any-user-id",
        required_permission="read"
    )
    result = ACLResourceService.check_permission(db, test_resource.id, check_data)

    assert result.allowed is True
    assert "public" in result.reason.lower()


def test_check_permission_rbac_with_role(db, test_resource, test_role, test_user, acl_admin):
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
    ACLResourceService.create(db, acl_data, acl_admin)

    # check_permission now takes the User object itself, not a
    # PermissionCheckRequest.
    result = ACLResourceService.check_permission(db, test_resource.id, test_user)

    assert result.allowed is True

    # A user without the bound role must not be granted access.
    other_user = User(
        username="testuser_acl_other",
        email="test_acl_other@example.com",
        hashed_password="not-used",
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    result2 = ACLResourceService.check_permission(db, test_resource.id, other_user)

    assert result2.allowed is False


def test_check_permission_with_user_whitelist(db, test_resource, test_user, acl_admin):
    """Test permission check with user whitelist in conditions."""
    # The user whitelist in ACL conditions holds usernames, not user ids.
    conditions = ConditionSchema(
        users=[test_user.username]
    )
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC,
        conditions=conditions
    )
    ACLResourceService.create(db, acl_data, acl_admin)

    # Check permission for whitelisted user
    result = ACLResourceService.check_permission(db, test_resource.id, test_user)

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


def test_create_acl_rule_nonexistent_resource(db, acl_admin):
    """Test creating ACL rule for non-existent resource."""
    acl_data = ACLRuleCreate(
        resource_id="non-existent-resource-id",
        resource_name="non-existent",
        access_mode=AccessMode.ANY
    )

    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.create(db, acl_data, acl_admin)

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


def test_add_role_binding_nonexistent_role(db, test_resource, acl_admin):
    """Test adding role binding with non-existent role."""
    acl_data = ACLRuleCreate(
        resource_id=test_resource.id,
        resource_name="test-acl-resource",
        access_mode=AccessMode.RBAC
    )
    acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

    binding_data = RoleBindingCreate(
        role_id="non-existent-role-id",
        permissions=["read"]
    )

    with pytest.raises(NotFoundException) as exc_info:
        ACLResourceService.add_role_binding(db, acl_rule.id, binding_data, acl_admin)

    assert "not found" in str(exc_info.value).lower()


class TestRoleBindingsGrantAccess:
    """Role bindings must actually affect the authorization decision.

    Regression coverage: check_permission eager-loaded acl_rule.role_bindings
    and then never looked at them, so binding a role to a resource through the
    ACL API (POST /acl/resources/{id}/roles) granted nothing - every RBAC
    decision fell through to the conditions whitelists. GatewayService.invoke()
    calls check_permission, so this silently denied every role-based grant.
    """

    def test_role_binding_added_after_rule_creation_grants_access(
        self, db, test_resource, test_role, test_user, acl_admin
    ):
        acl_data = ACLRuleCreate(
            resource_id=test_resource.id,
            resource_name="test-acl-resource",
            access_mode=AccessMode.RBAC,
        )
        acl_rule = ACLResourceService.create(db, acl_data, acl_admin)

        assert ACLResourceService.check_permission(db, test_resource.id, test_user).allowed is False

        ACLResourceService.add_role_binding(
            db, acl_rule.id, RoleBindingCreate(role_id=test_role.id, permissions=["execute"]), acl_admin
        )

        result = ACLResourceService.check_permission(db, test_resource.id, test_user)
        assert result.allowed is True
        assert result.matched_conditions == {"role_bindings": [test_role.id]}

    def test_binding_an_unrelated_role_does_not_grant_access(
        self, db, test_resource, test_role, test_user, acl_admin
    ):
        other_role = Role(name="other-role", description="A role test_user does not hold")
        db.add(other_role)
        db.commit()
        db.refresh(other_role)

        ACLResourceService.create(db, ACLRuleCreate(
            resource_id=test_resource.id,
            resource_name="test-acl-resource",
            access_mode=AccessMode.RBAC,
            role_bindings=[RoleBindingCreate(role_id=other_role.id, permissions=["read"])],
        ), acl_admin)

        assert ACLResourceService.check_permission(db, test_resource.id, test_user).allowed is False

    def test_role_binding_makes_the_rule_visible_to_the_bound_user(
        self, db, test_resource, test_role, test_user, acl_admin
    ):
        """The listing path must agree with the authorization path."""
        ACLResourceService.create(db, ACLRuleCreate(
            resource_id=test_resource.id,
            resource_name="test-acl-resource",
            access_mode=AccessMode.RBAC,
            role_bindings=[RoleBindingCreate(role_id=test_role.id, permissions=["read"])],
        ), acl_admin)

        rules, total = ACLResourceService.list_accessible(db, test_user)

        assert total == 1
        assert rules[0].resource_id == test_resource.id


class TestRoleWhitelistMatching:
    """conditions["roles"] accepts role ids or role names, consistently.

    Regression coverage: check_permission matched the whitelist against
    role.name while _user_has_acl_access and ResourceService._check_acl_permission
    matched against role.id, so an id-based rule granted gateway access but hid
    the rule from its own grantee (and a name-based rule did the reverse).
    """

    def _make_rule(self, db, resource, acl_admin, roles):
        return ACLResourceService.create(db, ACLRuleCreate(
            resource_id=resource.id,
            resource_name=resource.name,
            access_mode=AccessMode.RBAC,
            conditions=ConditionSchema(roles=roles),
        ), acl_admin)

    def test_whitelist_by_role_id(self, db, test_resource, test_role, test_user, acl_admin):
        self._make_rule(db, test_resource, acl_admin, [test_role.id])

        result = ACLResourceService.check_permission(db, test_resource.id, test_user)

        assert result.allowed is True
        assert result.matched_conditions == {"roles": [test_role.id]}

    def test_whitelist_by_role_name(self, db, test_resource, test_role, test_user, acl_admin):
        self._make_rule(db, test_resource, acl_admin, [test_role.name])

        result = ACLResourceService.check_permission(db, test_resource.id, test_user)

        assert result.allowed is True
        assert result.matched_conditions == {"roles": [test_role.name]}

    @pytest.mark.parametrize("by", ["id", "name"])
    def test_authorization_and_listing_agree(
        self, db, test_resource, test_role, test_user, acl_admin, by
    ):
        self._make_rule(db, test_resource, acl_admin,
                        [test_role.id if by == "id" else test_role.name])

        allowed = ACLResourceService.check_permission(db, test_resource.id, test_user).allowed
        _rules, total = ACLResourceService.list_accessible(db, test_user)

        assert allowed is True
        assert total == 1

    def test_unheld_role_is_not_matched(self, db, test_resource, test_user, acl_admin):
        self._make_rule(db, test_resource, acl_admin, ["some-other-role"])

        assert ACLResourceService.check_permission(db, test_resource.id, test_user).allowed is False
