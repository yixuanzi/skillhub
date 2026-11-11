"""Tests for the role model: three built-in roles, no permission matrix.

- every account gets `user`
- `admin` manages users and roles, but cannot grant `super_admin` or touch a
  `super_admin` account
- the built-in roles cannot be renamed, deleted or re-created
- scripts/migrate_roles.py converts a database seeded with the old five roles
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from core.roles import ADMIN, SUPER_ADMIN, USER, get_or_create_role, is_admin_user, is_super_admin
from core.security import create_access_token, get_password_hash
from models.acl import ACLRule, ACLRuleRole, AccessMode
from models.user import Role, User
from schemas.auth import UserCreate
from scripts import migrate_roles
from services.auth_service import AuthService


def make_user(db: Session, username: str, *role_names: str) -> User:
    """An active account holding exactly `role_names`."""
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    user.roles = [get_or_create_role(db, name) for name in role_names]
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def headers(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': user.id})}"}


def role_names(db: Session, username: str) -> list:
    db.expire_all()
    user = db.query(User).filter(User.username == username).first()
    return sorted(role.name for role in user.roles)


@pytest.fixture
def admin(db):
    return make_user(db, "the_admin", ADMIN)


@pytest.fixture
def root(db):
    return make_user(db, "the_root", SUPER_ADMIN)


@pytest.fixture
def plain(db):
    return make_user(db, "plain", USER)


@pytest.fixture(autouse=True)
def clean_acl(db):
    """conftest's cleanup does not cover ACL tables."""
    yield
    db.rollback()
    db.query(ACLRuleRole).delete()
    db.query(ACLRule).delete()
    db.commit()


class TestRoleHelpers:
    def test_admin_and_super_admin_are_admins(self, db, admin, root, plain):
        assert is_admin_user(admin) and is_admin_user(root)
        assert not is_admin_user(plain)
        assert not is_admin_user(None)

    def test_only_super_admin_is_super_admin(self, db, admin, root):
        assert is_super_admin(root)
        assert not is_super_admin(admin)

    def test_custom_role_grants_nothing(self, db):
        member = make_user(db, "member", "data-team")
        assert not is_admin_user(member)


class TestDefaultRole:
    def test_registration_assigns_user_role(self, db):
        AuthService.register(db, UserCreate(username="fresh", email="fresh@example.com", password="password123"))
        assert role_names(db, "fresh") == [USER]

    def test_user_role_is_created_once(self, db):
        for name in ("first", "second"):
            AuthService.register(db, UserCreate(username=name, email=f"{name}@example.com", password="password123"))
        assert db.query(Role).filter(Role.name == USER).count() == 1

    def test_admin_created_account_defaults_to_user_role(self, client: TestClient, db, admin):
        response = client.post("/api/v1/admin/users/", headers=headers(admin), json={
            "username": "created", "email": "created@example.com", "password": "password123",
        })
        assert response.status_code == 201
        assert [role["name"] for role in response.json()["roles"]] == [USER]

    def test_roles_are_returned_without_permissions(self, client: TestClient, db, plain):
        response = client.get("/api/v1/auth/me/", headers=headers(plain))
        assert response.status_code == 200
        role = response.json()["roles"][0]
        assert role["name"] == USER
        assert "permissions" not in role


class TestAdminEndpointsRequireAdmin:
    @pytest.mark.parametrize("path", ["/api/v1/admin/users/list/", "/api/v1/admin/roles/list/"])
    def test_plain_user_is_refused(self, client: TestClient, db, plain, path):
        assert client.get(path, headers=headers(plain)).status_code == 403

    @pytest.mark.parametrize("path", ["/api/v1/admin/users/list/", "/api/v1/admin/roles/list/"])
    def test_admin_is_allowed(self, client: TestClient, db, admin, path):
        assert client.get(path, headers=headers(admin)).status_code == 200

    def test_permission_endpoints_are_gone(self, client: TestClient, db, root):
        assert client.get("/api/v1/admin/permissions/list/", headers=headers(root)).status_code == 404
        role = get_or_create_role(db, USER)
        db.commit()
        response = client.get(f"/api/v1/admin/roles/{role.id}/permissions/", headers=headers(root))
        assert response.status_code == 404


class TestAdminIsLimited:
    """An admin cannot reach above itself; a super_admin can."""

    def test_admin_cannot_grant_itself_super_admin(self, client: TestClient, db, admin):
        super_role = get_or_create_role(db, SUPER_ADMIN)
        db.commit()
        response = client.put(
            f"/api/v1/admin/users/{admin.id}/roles/", headers=headers(admin), json={"role_ids": [super_role.id]},
        )
        assert response.status_code == 403
        assert role_names(db, "the_admin") == [ADMIN]

    def test_admin_cannot_grant_super_admin_to_others(self, client: TestClient, db, admin, plain):
        super_role = get_or_create_role(db, SUPER_ADMIN)
        db.commit()
        response = client.put(
            f"/api/v1/admin/users/{plain.id}/roles/", headers=headers(admin), json={"role_ids": [super_role.id]},
        )
        assert response.status_code == 403
        assert role_names(db, "plain") == [USER]

    def test_admin_cannot_create_a_super_admin(self, client: TestClient, db, admin):
        super_role = get_or_create_role(db, SUPER_ADMIN)
        db.commit()
        response = client.post("/api/v1/admin/users/", headers=headers(admin), json={
            "username": "sneaky", "email": "sneaky@example.com", "password": "password123",
            "role_ids": [super_role.id],
        })
        assert response.status_code == 403
        assert db.query(User).filter(User.username == "sneaky").first() is None

    def test_admin_cannot_edit_a_super_admin(self, client: TestClient, db, admin, root):
        response = client.put(
            f"/api/v1/admin/users/{root.id}/", headers=headers(admin), json={"password": "takeover123"},
        )
        assert response.status_code == 403

    def test_admin_cannot_demote_a_super_admin(self, client: TestClient, db, admin, root):
        response = client.put(
            f"/api/v1/admin/users/{root.id}/roles/", headers=headers(admin), json={"role_ids": []},
        )
        assert response.status_code == 403
        assert role_names(db, "the_root") == [SUPER_ADMIN]

    def test_admin_cannot_delete_a_super_admin(self, client: TestClient, db, admin, root):
        response = client.delete(f"/api/v1/admin/users/{root.id}/", headers=headers(admin))
        assert response.status_code == 403
        assert db.query(User).filter(User.id == root.id).first() is not None

    def test_admin_manages_ordinary_accounts(self, client: TestClient, db, admin, plain):
        admin_role = get_or_create_role(db, ADMIN)
        db.commit()
        assert client.put(
            f"/api/v1/admin/users/{plain.id}/", headers=headers(admin), json={"is_active": False},
        ).status_code == 200
        assert client.put(
            f"/api/v1/admin/users/{plain.id}/roles/", headers=headers(admin), json={"role_ids": [admin_role.id]},
        ).status_code == 200
        assert client.delete(f"/api/v1/admin/users/{plain.id}/", headers=headers(admin)).status_code == 204

    def test_super_admin_manages_super_admins(self, client: TestClient, db, root, plain):
        super_role = get_or_create_role(db, SUPER_ADMIN)
        db.commit()
        other_root = make_user(db, "other_root", SUPER_ADMIN)

        assert client.put(
            f"/api/v1/admin/users/{plain.id}/roles/", headers=headers(root), json={"role_ids": [super_role.id]},
        ).status_code == 200
        assert role_names(db, "plain") == [SUPER_ADMIN]
        assert client.put(
            f"/api/v1/admin/users/{other_root.id}/", headers=headers(root), json={"is_active": False},
        ).status_code == 200
        assert client.delete(f"/api/v1/admin/users/{other_root.id}/", headers=headers(root)).status_code == 204


class TestBuiltinRolesAreFixed:
    @pytest.mark.parametrize("name", [SUPER_ADMIN, ADMIN, USER])
    def test_cannot_be_renamed(self, client: TestClient, db, root, name):
        role = get_or_create_role(db, name)
        db.commit()
        response = client.put(f"/api/v1/admin/roles/{role.id}/", headers=headers(root), json={"name": "renamed"})
        assert response.status_code == 400
        assert db.query(Role).filter(Role.name == name).count() == 1

    @pytest.mark.parametrize("name", [SUPER_ADMIN, ADMIN, USER])
    def test_cannot_be_deleted(self, client: TestClient, db, root, name):
        role = get_or_create_role(db, name)
        db.commit()
        response = client.delete(f"/api/v1/admin/roles/{role.id}/", headers=headers(root))
        assert response.status_code == 400
        assert db.query(Role).filter(Role.name == name).count() == 1

    def test_description_can_still_be_edited(self, client: TestClient, db, root):
        role = get_or_create_role(db, USER)
        db.commit()
        response = client.put(
            f"/api/v1/admin/roles/{role.id}/", headers=headers(root), json={"description": "Everyone"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Everyone"

    def test_reserved_name_cannot_be_created(self, client: TestClient, db, plain):
        # `plain` exists, so `user` exists but `super_admin` does not: the name
        # is reserved even while the row is missing.
        admin = make_user(db, "an_admin", ADMIN)
        response = client.post("/api/v1/admin/roles/", headers=headers(admin), json={"name": SUPER_ADMIN})
        assert response.status_code == 400
        assert db.query(Role).filter(Role.name == SUPER_ADMIN).first() is None

    def test_custom_role_lifecycle(self, client: TestClient, db, admin):
        created = client.post(
            "/api/v1/admin/roles/", headers=headers(admin), json={"name": "data-team", "description": "Data"},
        )
        assert created.status_code == 201
        role_id = created.json()["id"]

        assert client.put(
            f"/api/v1/admin/roles/{role_id}/", headers=headers(admin), json={"name": "analytics"},
        ).status_code == 200
        # ...but not into a built-in name
        assert client.put(
            f"/api/v1/admin/roles/{role_id}/", headers=headers(admin), json={"name": SUPER_ADMIN},
        ).status_code == 400
        assert client.delete(f"/api/v1/admin/roles/{role_id}/", headers=headers(admin)).status_code == 204


class TestMigrateRoles:
    """scripts/migrate_roles.py against a database seeded the old way."""

    def _legacy(self, db):
        for name in (SUPER_ADMIN, ADMIN, "developer", "operator", "viewer"):
            db.add(Role(name=name, description=f"legacy {name}"))
        db.commit()
        return {role.name: role for role in db.query(Role).all()}

    def _rule(self, db, name, roles=None, bound=()):
        rule = ACLRule(
            resource_id=f"id-{name}", resource_name=name, access_mode=AccessMode.RBAC,
            conditions={"users": ["someone"], "roles": roles or []},
        )
        db.add(rule)
        db.flush()
        for role in bound:
            db.add(ACLRuleRole(acl_rule_id=rule.id, role_id=role.id, permissions=["read"]))
        db.commit()
        return rule

    def test_viewer_becomes_user_and_keeps_its_id(self, db):
        legacy = self._legacy(db)
        viewer_id = legacy["viewer"].id
        make_user(db, "vera", "viewer")

        migrate_roles.migrate(db)
        db.commit()

        assert sorted(role.name for role in db.query(Role).all()) == [ADMIN, SUPER_ADMIN, USER]
        assert db.query(Role).filter(Role.name == USER).one().id == viewer_id
        assert role_names(db, "vera") == [USER]

    def test_developers_and_operators_become_users(self, db):
        self._legacy(db)
        make_user(db, "dev", "developer")
        make_user(db, "ops", "operator", ADMIN)

        migrate_roles.migrate(db)
        db.commit()

        assert role_names(db, "dev") == [USER]
        assert role_names(db, "ops") == [ADMIN, USER]

    def test_accounts_without_a_role_get_user(self, db):
        self._legacy(db)
        make_user(db, "nobody")

        migrate_roles.migrate(db)
        db.commit()

        assert role_names(db, "nobody") == [USER]

    def test_acl_grants_follow_the_roles(self, db):
        legacy = self._legacy(db)
        custom = get_or_create_role(db, "data-team")
        db.commit()
        rule = self._rule(
            db, "report-api",
            roles=["viewer", "developer", str(legacy["operator"].id), "admin", "data-team"],
            bound=(legacy["viewer"], legacy["developer"], custom),
        )

        log = migrate_roles.migrate(db)
        db.commit()
        db.expire_all()

        user_role = db.query(Role).filter(Role.name == USER).one()
        rule = db.query(ACLRule).filter(ACLRule.id == rule.id).one()
        # viewer -> user; developer and operator dropped, by name and by id;
        # everything else, including the users whitelist, untouched.
        assert rule.conditions == {"users": ["someone"], "roles": ["user", "admin", "data-team"]}
        assert sorted(binding.role_id for binding in rule.role_bindings) == sorted([user_role.id, custom.id])
        # every dropped grant is reported
        assert len([line for line in log if line.startswith("ACCESS REMOVED")]) == 3

    def test_viewer_is_merged_when_user_already_exists(self, db):
        legacy = self._legacy(db)
        user_role = get_or_create_role(db, USER)
        db.commit()
        make_user(db, "vera", "viewer")
        make_user(db, "both", "viewer", USER)
        shared = self._rule(db, "shared", roles=[str(legacy["viewer"].id)], bound=(legacy["viewer"], user_role))
        viewer_only = self._rule(db, "viewer-only", bound=(legacy["viewer"],))

        migrate_roles.migrate(db)
        db.commit()
        db.expire_all()

        assert db.query(Role).filter(Role.name == "viewer").first() is None
        assert role_names(db, "vera") == [USER]
        assert role_names(db, "both") == [USER]
        shared = db.query(ACLRule).filter(ACLRule.id == shared.id).one()
        assert [binding.role_id for binding in shared.role_bindings] == [user_role.id]
        assert shared.conditions["roles"] == [str(user_role.id)]
        viewer_only = db.query(ACLRule).filter(ACLRule.id == viewer_only.id).one()
        assert [binding.role_id for binding in viewer_only.role_bindings] == [user_role.id]

    def test_is_idempotent(self, db):
        self._legacy(db)
        make_user(db, "dev", "developer")

        assert migrate_roles.migrate(db)
        db.commit()
        assert migrate_roles.migrate(db) == []

    def test_seeded_database_needs_nothing(self, db):
        make_user(db, "a", SUPER_ADMIN)
        make_user(db, "b", ADMIN)
        make_user(db, "c", USER)
        custom = get_or_create_role(db, "data-team")
        db.commit()
        self._rule(db, "kept", roles=["admin", "data-team"], bound=(custom,))

        assert migrate_roles.migrate(db) == []

    def test_obsolete_tables_are_dropped(self, db):
        bind = db.get_bind()
        db.commit()
        with bind.begin() as connection:
            connection.execute(text("CREATE TABLE IF NOT EXISTS permissions (id VARCHAR(36) PRIMARY KEY)"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS role_permissions (role_id VARCHAR(36), permission_id VARCHAR(36))"))

        assert migrate_roles.obsolete_tables(bind) == ["role_permissions", "permissions"]
        assert migrate_roles.drop_obsolete_tables(bind) == ["role_permissions", "permissions"]
        assert not {"permissions", "role_permissions"} & set(inspect(bind).get_table_names())
        assert migrate_roles.drop_obsolete_tables(bind) == []
