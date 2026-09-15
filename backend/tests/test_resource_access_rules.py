"""Visibility, secret exposure, and write permission must be uniform.

These pin four fixes that all shared one root cause: the same question was
answered by several independent implementations that had drifted apart.
"""
import pytest

from models.acl import ACLRule, ACLRuleRole, AccessMode
from models.resource import Resource, ResourceType
from models.user import Role, User
from schemas.resource import ResourceCreate, ResourceUpdate
from services.resource_service import REDACTED, ResourceService
from core.exceptions import ValidationException

MCP_EXT = {
    "transport": "sse",
    "endpoint": "https://mcp.example.com/sse",
    "headers": {"Authorization": "Bearer SECRET_LITERAL_KEY"},
    "timeout": 30000,
}
COMPOSIO_EXT = {"COMPOSIO_API_KEY": "ak_SECRET", "COMPOSIO_USER_ID": "acct-1"}

ALL_TYPES = [
    pytest.param(ResourceType.GATEWAY, {"token": "SECRET_LITERAL_KEY"}, id="gateway"),
    pytest.param(ResourceType.THIRD, {"token": "SECRET_LITERAL_KEY"}, id="third"),
    pytest.param(ResourceType.MCP, MCP_EXT, id="mcp"),
    pytest.param(ResourceType.COMPOSIO, COMPOSIO_EXT, id="composio"),
]


def _make_user(db, username, roles=()):
    user = User(username=username, email=f"{username}@example.com", hashed_password="x")
    for role in roles:
        user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_role(db, name):
    role = Role(name=name, description=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _rule_for(db, resource_id):
    return db.query(ACLRule).filter(ACLRule.resource_id == resource_id).first()


def _create(db, owner, rtype, ext, name="probe", view_scope="private"):
    return ResourceService.create(db, ResourceCreate(
        name=name, type=rtype, ext=ext, view_scope=view_scope,
    ), user=owner)


class TestExtIsRedactedForNonOwners:
    """`ext` carries credentials and must not ship to everyone who can see it.

    Regression coverage: ResourceResponse includes `ext` verbatim, and a
    resource is visible to far more people than may write it (anyone at all,
    for a public one), so `GET /resources/` handed every authenticated user the
    literal MCP Authorization header and Composio API key of every public
    resource. Not being allowed to *invoke* a resource is no protection if you
    can read its key and use it directly.
    """

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_owner_still_sees_the_real_values(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext, view_scope="public")
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        assert ResourceService.to_response_for(row, test_user).ext == ext

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_admin_still_sees_the_real_values(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext, view_scope="public")
        admin = _make_user(db, "an-admin", [_make_role(db, "admin")])
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        assert ResourceService.to_response_for(row, admin).ext == ext

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_a_stranger_gets_no_secret_back(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext, view_scope="public")
        stranger = _make_user(db, "stranger")
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        redacted = ResourceService.to_response_for(row, stranger).ext

        assert "SECRET_LITERAL_KEY" not in str(redacted)
        assert "ak_SECRET" not in str(redacted)

    def test_structure_and_keys_survive_redaction(self, db, test_user):
        resource = _create(db, test_user, ResourceType.MCP, MCP_EXT, view_scope="public")
        stranger = _make_user(db, "stranger")
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        redacted = ResourceService.to_response_for(row, stranger).ext

        assert set(redacted) == set(MCP_EXT)
        assert redacted["headers"]["Authorization"] == REDACTED
        assert redacted["timeout"] == 30000, "non-string scalars carry no secret"

    def test_token_placeholders_stay_readable(self, db, test_user):
        """A {token_name} placeholder names a token; it is not itself a secret."""
        ext = {
            "COMPOSIO_API_KEY": "{my_key}",
            "COMPOSIO_USER_ID": "literal-account-id",
        }
        resource = _create(db, test_user, ResourceType.COMPOSIO, ext, view_scope="public")
        stranger = _make_user(db, "stranger")
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        redacted = ResourceService.to_response_for(row, stranger).ext

        assert redacted["COMPOSIO_API_KEY"] == "{my_key}"
        assert redacted["COMPOSIO_USER_ID"] == REDACTED

    def test_an_embedded_placeholder_is_still_redacted(self, db, test_user):
        """Only a bare placeholder is safe - "Bearer {k}" could hide more."""
        ext = {"headers": {"Authorization": "Bearer {my_key}"}}
        resource = _create(db, test_user, ResourceType.GATEWAY, ext, view_scope="public")
        stranger = _make_user(db, "stranger")
        row = db.query(Resource).filter(Resource.id == resource.id).first()

        assert ResourceService.to_response_for(row, stranger).ext["headers"]["Authorization"] == REDACTED


class TestListingAgreesWithAccess:
    """A resource you may open and invoke must also appear in your listing.

    Regression coverage: _get_acl_granted_resource_ids matched roles by id only
    and ignored role_bindings, while the other three ACL call sites accepted
    role names too and honoured bindings. A user granted access via a role
    binding could invoke a resource that was invisible to them in the UI.
    """

    def _granted_via(self, db, owner, kind):
        resource = _create(db, owner, ResourceType.GATEWAY, None)
        team = _make_role(db, "team")
        member = _make_user(db, "member", [team])
        rule = _rule_for(db, resource.id)

        if kind == "role_binding":
            db.add(ACLRuleRole(acl_rule_id=rule.id, role_id=team.id, permissions=["read"]))
        elif kind == "role_name":
            rule.conditions = {"roles": [team.name]}
        elif kind == "role_id":
            rule.conditions = {"roles": [team.id]}
        elif kind == "username":
            rule.conditions = {"users": [member.username]}
        db.commit()
        return resource, member

    @pytest.mark.parametrize("kind", ["role_binding", "role_name", "role_id", "username"])
    def test_granted_user_sees_the_resource_in_the_listing(self, db, test_user, kind):
        resource, member = self._granted_via(db, test_user, kind)

        # Can open it...
        ResourceService.get_accessible(db, resource.id, member)
        # ...so it must be listed too.
        rows, total = ResourceService.list_accessible_with_count(db, member, limit=100)

        assert total == 1
        assert [r.id for r in rows] == [resource.id]

    def test_an_ungranted_user_still_sees_nothing(self, db, test_user):
        resource = _create(db, test_user, ResourceType.GATEWAY, None)
        stranger = _make_user(db, "stranger")

        _rows, total = ResourceService.list_accessible_with_count(db, stranger, limit=100)

        assert total == 0


class TestWritePermission:
    """update and delete share one rule: owner or admin, and never nobody."""

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_owner_may_update_and_delete(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)

        ResourceService.update_owner_only(db, resource.id, ResourceUpdate(desc="mine"), user=test_user)
        ResourceService.delete_owner_only(db, resource.id, user=test_user)

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_admin_may_update_as_well_as_delete(self, db, test_user, rtype, ext):
        """Admins could always delete; being unable to edit made no sense."""
        resource = _create(db, test_user, rtype, ext)
        admin = _make_user(db, "an-admin", [_make_role(db, "admin")])

        updated = ResourceService.update_owner_only(
            db, resource.id, ResourceUpdate(desc="fixed by admin"), user=admin
        )
        assert updated.desc == "fixed by admin"
        ResourceService.delete_owner_only(db, resource.id, user=admin)

    @pytest.mark.parametrize("rtype,ext", ALL_TYPES)
    def test_a_stranger_may_do_neither(self, db, test_user, rtype, ext):
        resource = _create(db, test_user, rtype, ext)
        stranger = _make_user(db, "stranger")

        with pytest.raises(ValidationException, match="permission"):
            ResourceService.update_owner_only(db, resource.id, ResourceUpdate(desc="x"), user=stranger)
        with pytest.raises(ValidationException, match="permission"):
            ResourceService.delete_owner_only(db, resource.id, user=stranger)

    def test_an_ownerless_resource_is_admin_only(self, db):
        """Regression: `if resource.owner_id:` skipped the check when NULL,
        leaving anonymously-created and legacy rows writable by anyone."""
        resource = Resource(name="orphan", type=ResourceType.GATEWAY, view_scope="private", owner_id=None)
        db.add(resource)
        db.commit()
        db.refresh(resource)
        stranger = _make_user(db, "stranger")

        with pytest.raises(ValidationException, match="permission"):
            ResourceService.update_owner_only(db, resource.id, ResourceUpdate(desc="x"), user=stranger)
        with pytest.raises(ValidationException, match="permission"):
            ResourceService.delete_owner_only(db, resource.id, user=stranger)

        admin = _make_user(db, "an-admin", [_make_role(db, "admin")])
        ResourceService.update_owner_only(db, resource.id, ResourceUpdate(desc="ok"), user=admin)
        ResourceService.delete_owner_only(db, resource.id, user=admin)

    def test_anonymous_callers_may_not_write(self, db, test_user):
        resource = _create(db, test_user, ResourceType.GATEWAY, None)

        with pytest.raises(ValidationException, match="permission"):
            ResourceService.update_owner_only(db, resource.id, ResourceUpdate(desc="x"), user=None)
        with pytest.raises(ValidationException, match="permission"):
            ResourceService.delete_owner_only(db, resource.id, user=None)
