"""Invocation permission must be ACL-only, and identical for all 4 resource types.

Regression coverage for a split-brain authorization model: the gateway/third
proxy called ACLResourceService.check_permission (ACL only), while the mcp and
composio paths called ResourceService.get_accessible - which answers a
different question ("may this user see and manage it?") and returns early on
public/owner/admin before ever reading the ACL. A deny-all ACL rule was
therefore enforced for gateway resources and silently ignored for mcp and
composio ones, so a public mcp resource was callable by every authenticated
user no matter what its ACL said.
"""
import pytest

from models.acl import ACLRule, AccessMode
from models.resource import ResourceType
from models.user import Role, User
from schemas.resource import ResourceCreate
from services.acl_resource_service import ACLResourceService
from services.resource_service import ResourceService
from core.exceptions import ValidationException

MCP_EXT = {"transport": "sse", "endpoint": "https://mcp.example.com/sse"}
COMPOSIO_EXT = {"COMPOSIO_API_KEY": "ak_x", "COMPOSIO_USER_ID": "u1"}

# (type, ext) for every resource type that can be invoked.
ALL_TYPES = [
    pytest.param(ResourceType.GATEWAY, None, id="gateway"),
    pytest.param(ResourceType.THIRD, None, id="third"),
    pytest.param(ResourceType.MCP, MCP_EXT, id="mcp"),
    pytest.param(ResourceType.COMPOSIO, COMPOSIO_EXT, id="composio"),
]


def _make_user(db, username):
    user = User(username=username, email=f"{username}@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _rule_for(db, resource_id):
    return db.query(ACLRule).filter(ACLRule.resource_id == resource_id).first()


def _create(db, owner, rtype, ext, name="probe", view_scope="private"):
    return ResourceService.create(db, ResourceCreate(
        name=name, type=rtype, ext=ext, view_scope=view_scope,
    ), user=owner)


class TestDefaultAclSeedsTheOwner:
    """A creator must be able to call what they just created."""

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_owner_is_written_into_the_users_whitelist(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)

        rule = _rule_for(db, resource.id)
        assert rule.access_mode == AccessMode.RBAC
        assert rule.conditions == {"users": [test_user.username]}

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_owner_may_invoke_immediately(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)

        ACLResourceService.enforce_permission(db, resource.id, test_user)

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_a_stranger_may_not(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)
        stranger = _make_user(db, "stranger")

        with pytest.raises(ValidationException, match="Permission denied"):
            ACLResourceService.enforce_permission(db, resource.id, stranger)

    def test_an_ownerless_resource_gets_a_deny_all_rule(self, db):
        """Anonymous creation has no owner to seed, so nothing is whitelisted."""
        resource = ResourceService.create(db, ResourceCreate(
            name="ownerless", type=ResourceType.GATEWAY,
        ))

        assert _rule_for(db, resource.id).conditions is None


class TestViewScopeDoesNotGrantInvocation:
    """view_scope governs visibility; the ACL governs invocation.

    This is the exact hole that made a deny-all ACL meaningless for mcp and
    composio: they authorized via get_accessible, which returns early for any
    public resource.
    """

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_public_scope_does_not_let_a_stranger_invoke(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext, view_scope="public")
        stranger = _make_user(db, "stranger")

        # Visible...
        ResourceService.get_accessible(db, resource.id, stranger)
        # ...but not callable.
        with pytest.raises(ValidationException, match="Permission denied"):
            ACLResourceService.enforce_permission(db, resource.id, stranger)

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_any_mode_is_how_a_resource_is_opened_up(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext, view_scope="private")
        stranger = _make_user(db, "stranger")

        rule = _rule_for(db, resource.id)
        rule.access_mode = AccessMode.ANY
        db.commit()

        ACLResourceService.enforce_permission(db, resource.id, stranger)


class TestOwnershipAndAdminDoNotGrantInvocation:
    """Ownership and admin are management privileges, not execute privileges."""

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_owner_removed_from_the_whitelist_can_no_longer_invoke(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)

        rule = _rule_for(db, resource.id)
        rule.conditions = {"users": []}
        db.commit()

        # Still theirs to manage...
        ResourceService.get_accessible(db, resource.id, test_user)
        # ...but no longer theirs to call.
        with pytest.raises(ValidationException, match="Permission denied"):
            ACLResourceService.enforce_permission(db, resource.id, test_user)

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_admin_needs_an_acl_grant_like_anyone_else(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)
        admin_role = Role(name="admin", description="Administrator")
        db.add(admin_role)
        db.commit()
        admin = _make_user(db, "an-admin")
        admin.roles.append(admin_role)
        db.commit()

        ResourceService.get_accessible(db, resource.id, admin)  # can manage
        with pytest.raises(ValidationException, match="Permission denied"):
            ACLResourceService.enforce_permission(db, resource.id, admin)


class TestEveryInvocationPathUsesTheSharedCheck:
    """Static guard: no invocation path may authorize via get_accessible again."""

    PATHS = ["services/gateway_service.py", "services/mcp_service.py", "services/composio_service.py"]

    @pytest.mark.parametrize("path", PATHS)
    def test_no_invocation_path_calls_get_accessible(self, path):
        from pathlib import Path

        source = (Path(__file__).resolve().parent.parent / path).read_text()
        assert "get_accessible" not in source, (
            f"{path} authorizes with ResourceService.get_accessible again - "
            "invocation permission must go through "
            "ACLResourceService.enforce_permission"
        )

    @pytest.mark.parametrize("path", PATHS)
    def test_each_invocation_path_calls_enforce_permission(self, path):
        from pathlib import Path

        source = (Path(__file__).resolve().parent.parent / path).read_text()
        assert "ACLResourceService.enforce_permission(" in source
