"""API-level tests for the resource ACL endpoints."""
import pytest

from models.acl import AccessMode
from models.resource import Resource, ResourceType
from models.user import Role
from schemas.acl_resource import ACLRuleCreate, RoleBindingCreate
from services.acl_resource_service import ACLResourceService


@pytest.fixture(scope="function")
def acl_resource(db, admin_user):
    """A bare resource row, created without the auto-generated default ACL rule."""
    resource = Resource(
        name="acl-api-resource",
        type=ResourceType.GATEWAY,
        desc="Resource for ACL API tests",
        view_scope="private",
        owner_id=admin_user.id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


class TestCheckPermissionEndpoint:
    """POST /api/v1/acl/resources/check-permission/{resource_id}.

    Regression coverage: the route passed the request *body* where the service
    expects the User object, so every call raised AttributeError and the
    endpoint always returned 500.
    """

    def _post(self, client, resource_id, headers):
        return client.post(
            f"/api/v1/acl/resources/check-permission/{resource_id}",
            json={"user_id": "ignored", "required_permission": "execute"},
            headers=headers,
        )

    def test_any_mode_allows(self, client, db, acl_resource, admin_user, admin_headers, auth_headers):
        ACLResourceService.create(db, ACLRuleCreate(
            resource_id=acl_resource.id,
            resource_name=acl_resource.name,
            access_mode=AccessMode.ANY,
        ), admin_user)

        response = self._post(client, acl_resource.id, auth_headers)

        assert response.status_code == 200
        assert response.json()["allowed"] is True

    def test_rbac_denies_user_without_the_bound_role(
        self, client, db, acl_resource, admin_user, auth_headers
    ):
        ACLResourceService.create(db, ACLRuleCreate(
            resource_id=acl_resource.id,
            resource_name=acl_resource.name,
            access_mode=AccessMode.RBAC,
        ), admin_user)

        response = self._post(client, acl_resource.id, auth_headers)

        assert response.status_code == 200
        assert response.json()["allowed"] is False

    def test_rbac_allows_user_holding_the_bound_role(
        self, client, db, acl_resource, admin_user, test_user, auth_headers
    ):
        role = Role(name="acl-api-role", description="Role bound to the resource")
        db.add(role)
        db.commit()
        db.refresh(role)
        test_user.roles.append(role)
        db.commit()

        ACLResourceService.create(db, ACLRuleCreate(
            resource_id=acl_resource.id,
            resource_name=acl_resource.name,
            access_mode=AccessMode.RBAC,
            role_bindings=[RoleBindingCreate(role_id=role.id, permissions=["execute"])],
        ), admin_user)

        response = self._post(client, acl_resource.id, auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["allowed"] is True
        assert body["matched_conditions"] == {"role_bindings": [role.id]}

    def test_no_acl_rule_denies(self, client, acl_resource, auth_headers):
        response = self._post(client, acl_resource.id, auth_headers)

        assert response.status_code == 200
        assert response.json()["allowed"] is False
