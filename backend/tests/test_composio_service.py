"""Tests for the Composio integration service.

Covers config parsing, the global singleton constraint on the `composio`
resource type, and that each meta tool call builds the arguments Composio's
API expects - all against a fake `composio` SDK module so no real network
call is ever made.

Note: pytest-asyncio isn't installed in this project (see other test files'
skipped/erroring `async def test_*`), so async ComposioService methods are
driven with a plain `asyncio.run(...)` inside ordinary sync test functions
instead of `@pytest.mark.asyncio`.
"""
import asyncio
import sys
import types

import pytest
from pydantic import ValidationError

from models.acl import ACLRule, AccessMode
from models.resource import ResourceType
from schemas.resource import ComposioConfig, ResourceCreate, ResourceUpdate
from services.resource_service import ResourceService
from services.composio_service import ComposioService
from core.exceptions import ValidationException
from config import settings


class TestComposioConfigParsing:
    """Test ComposioConfig schema parsing."""

    def test_valid_config(self):
        config = ComposioConfig(COMPOSIO_API_KEY="ak_x", COMPOSIO_USER_ID="user-1")
        assert config.COMPOSIO_API_KEY == "ak_x"
        assert config.COMPOSIO_USER_ID == "user-1"

    def test_missing_api_key_raises(self):
        with pytest.raises(ValidationError):
            ComposioConfig(COMPOSIO_USER_ID="user-1")

    def test_missing_user_id_raises(self):
        with pytest.raises(ValidationError):
            ComposioConfig(COMPOSIO_API_KEY="ak_x")


class TestComposioSingleton:
    """Test that only one composio-type resource can exist globally."""

    def test_get_singleton_resource_missing_raises(self, db):
        with pytest.raises(ValidationException, match="No composio resource"):
            ComposioService.get_singleton_resource(db)

    def test_second_composio_resource_rejected(self, db, test_user):
        ResourceService.create(db, ResourceCreate(
            name="composio-1",
            type=ResourceType.COMPOSIO,
            ext={"COMPOSIO_API_KEY": "ak_1", "COMPOSIO_USER_ID": "u1"},
        ), user=test_user)

        with pytest.raises(ValidationException, match="only one is allowed"):
            ResourceService.create(db, ResourceCreate(
                name="composio-2",
                type=ResourceType.COMPOSIO,
                ext={"COMPOSIO_API_KEY": "ak_2", "COMPOSIO_USER_ID": "u2"},
            ), user=test_user)

    def test_updating_other_resource_to_composio_rejected(self, db, test_user):
        ResourceService.create(db, ResourceCreate(
            name="composio-existing",
            type=ResourceType.COMPOSIO,
            ext={"COMPOSIO_API_KEY": "ak_1", "COMPOSIO_USER_ID": "u1"},
        ), user=test_user)

        other = ResourceService.create(db, ResourceCreate(
            name="other-third",
            type=ResourceType.THIRD,
            url="https://example.com",
        ), user=test_user)

        with pytest.raises(ValidationException, match="only one is allowed"):
            ResourceService.update_owner_only(
                db, other.id, ResourceUpdate(type=ResourceType.COMPOSIO), user=test_user
            )

    def test_resaving_existing_composio_resource_allowed(self, db, test_user):
        created = ResourceService.create(db, ResourceCreate(
            name="composio-existing",
            type=ResourceType.COMPOSIO,
            ext={"COMPOSIO_API_KEY": "ak_1", "COMPOSIO_USER_ID": "u1"},
        ), user=test_user)

        updated = ResourceService.update_owner_only(
            db, created.id,
            ResourceUpdate(type=ResourceType.COMPOSIO, desc="still fine"),
            user=test_user,
        )
        assert updated.desc == "still fine"


@pytest.fixture
def composio_resource(db, test_user):
    """Create the singleton composio resource, owned by test_user."""
    return ResourceService.create(db, ResourceCreate(
        name="composio",
        type=ResourceType.COMPOSIO,
        view_scope="private",
        ext={"COMPOSIO_API_KEY": "ak_test", "COMPOSIO_USER_ID": "test-user-id"},
    ), user=test_user)


def _open_acl(db, resource_id):
    """Switch a resource's ACL rule to ANY mode, so any user may invoke it.

    Invocation permission is decided purely by the ACL, so view_scope="public"
    no longer lets a second user call a resource - view_scope governs
    visibility only. An ANY-mode rule is how a resource is opened up now.
    """
    rule = db.query(ACLRule).filter(ACLRule.resource_id == resource_id).first()
    assert rule is not None, "every resource is created with a default ACL rule"
    rule.access_mode = AccessMode.ANY
    db.commit()


@pytest.fixture
def shared_composio_resource(db, test_user):
    """Singleton composio resource any user may invoke (ACL in ANY mode)."""
    resource = ResourceService.create(db, ResourceCreate(
        name="composio",
        type=ResourceType.COMPOSIO,
        view_scope="public",
        ext={"COMPOSIO_API_KEY": "ak_test", "COMPOSIO_USER_ID": "test-user-id"},
    ), user=test_user)
    _open_acl(db, resource.id)
    return resource


class _FakeToolsClient:
    """Fake `composio.tools` namespace; records every .execute() call."""

    def __init__(self, calls):
        self._calls = calls

    def execute(self, tool_slug, **kwargs):
        self._calls.append((tool_slug, kwargs))
        return {"data": {"echo": tool_slug}, "successful": True, "error": None}


class _FakeSession:
    def __init__(self, calls):
        self._calls = calls

    def execute(self, tool_slug, arguments):
        self._calls.append((tool_slug, {"arguments": arguments, "via_session": True}))
        return {"data": {"echo": tool_slug, "via": "session"}, "error": None}


class _FakeSessions:
    def __init__(self, owner):
        self._owner = owner

    def create(self, user_id):
        self._owner.session_user_ids.append(user_id)
        return _FakeSession(self._owner.calls)


class _FakeComposio:
    """Fake `composio.Composio` client, capturing everything called on it."""

    instances: list["_FakeComposio"] = []

    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        self.calls = []
        self.session_user_ids = []
        self.tools = _FakeToolsClient(self.calls)
        self.sessions = _FakeSessions(self)
        _FakeComposio.instances.append(self)


@pytest.fixture
def fake_composio_module(monkeypatch):
    """Install a fake `composio` module so ComposioService never hits the network."""
    _FakeComposio.instances = []
    fake_module = types.ModuleType("composio")
    fake_module.Composio = _FakeComposio
    monkeypatch.setitem(sys.modules, "composio", fake_module)
    return _FakeComposio


@pytest.fixture(autouse=True)
def clear_composio_cache():
    """The client/session cache is class-level state - never leak it across tests."""
    ComposioService._session_cache.clear()
    ComposioService._key_locks.clear()
    yield
    ComposioService._session_cache.clear()
    ComposioService._key_locks.clear()


def _make_user(db, username: str):
    from models.user import User

    user = User(username=username, email=f"{username}@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_mtoken(db, user_id: str, key_name: str, value: str):
    from models.mtoken import MToken

    token = MToken(app_name="composio", key_name=key_name, value=value, created_by=user_id)
    db.add(token)
    db.commit()
    return token


class TestComposioServiceCalls:
    """Test that each meta tool call builds the arguments Composio expects."""

    def test_search_tools_builds_expected_arguments(self, db, test_user, composio_resource, fake_composio_module):
        result = asyncio.run(ComposioService.search_tools(
            db, test_user, use_case="send an email", known_fields="to:me"
        ))

        client = fake_composio_module.instances[-1]
        assert client.api_key == "ak_test"
        tool_slug, kwargs = client.calls[0]
        assert tool_slug == "COMPOSIO_SEARCH_TOOLS"
        assert kwargs["user_id"] == "test-user-id"
        assert kwargs["dangerously_skip_version_check"] is True
        assert kwargs["arguments"] == {
            "queries": [{"use_case": "send an email", "known_fields": "to:me"}]
        }
        assert result["data"]["echo"] == "COMPOSIO_SEARCH_TOOLS"

    def test_search_tools_without_known_fields(self, db, test_user, composio_resource, fake_composio_module):
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="send an email"))

        client = fake_composio_module.instances[-1]
        _, kwargs = client.calls[0]
        assert kwargs["arguments"] == {"queries": [{"use_case": "send an email"}]}

    def test_get_tool_schemas_builds_expected_arguments(self, db, test_user, composio_resource, fake_composio_module):
        asyncio.run(ComposioService.get_tool_schemas(db, test_user, tool_slugs=["JIRA_SEARCH_ISSUES"]))

        client = fake_composio_module.instances[-1]
        tool_slug, kwargs = client.calls[0]
        assert tool_slug == "COMPOSIO_GET_TOOL_SCHEMAS"
        assert kwargs["arguments"] == {"tool_slugs": ["JIRA_SEARCH_ISSUES"]}
        assert kwargs["dangerously_skip_version_check"] is True

    def test_multi_execute_tool_runs_inside_a_session(self, db, test_user, composio_resource, fake_composio_module):
        tools = [{"tool_slug": "JIRA_SEARCH_ISSUES", "arguments": {"project_key": "VMS"}}]

        result = asyncio.run(ComposioService.multi_execute_tool(db, test_user, tools=tools))

        client = fake_composio_module.instances[-1]
        # COMPOSIO_MULTI_EXECUTE_TOOL is rejected outside a Tool Router session,
        # so this must go through composio.sessions.create(...).execute(...).
        assert client.session_user_ids == ["test-user-id"]
        tool_slug, kwargs = client.calls[0]
        assert tool_slug == "COMPOSIO_MULTI_EXECUTE_TOOL"
        assert kwargs["via_session"] is True
        assert kwargs["arguments"]["tools"] == tools
        assert kwargs["arguments"]["memory"] == {}
        assert kwargs["arguments"]["sync_response_to_workbench"] is False
        assert result["data"]["via"] == "session"

    def test_missing_resource_raises_validation_error(self, db, test_user, fake_composio_module):
        with pytest.raises(ValidationException, match="No composio resource"):
            asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

    def test_missing_ext_raises_validation_error(self, db, test_user, fake_composio_module):
        ResourceService.create(db, ResourceCreate(
            name="composio", type=ResourceType.COMPOSIO,
        ), user=test_user)

        with pytest.raises(ValidationException, match="missing ext"):
            asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))


class TestManagedTokenPlaceholders:
    """ext supports the same {token_name} placeholders as gateway/third resources."""

    def _create_placeholder_resource(self, db, owner):
        resource = ResourceService.create(db, ResourceCreate(
            name="composio",
            type=ResourceType.COMPOSIO,
            view_scope="public",
            ext={"COMPOSIO_API_KEY": "{my_composio_key}", "COMPOSIO_USER_ID": "{my_composio_uid}"},
        ), user=owner)
        # These tests are about per-user token resolution, not about the ACL.
        _open_acl(db, resource.id)
        return resource

    def test_placeholders_resolve_from_callers_own_tokens(self, db, test_user, fake_composio_module):
        self._create_placeholder_resource(db, test_user)
        _make_mtoken(db, str(test_user.id), "my_composio_key", "ak_resolved_123")
        _make_mtoken(db, str(test_user.id), "my_composio_uid", "pg-resolved-456")

        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

        client = fake_composio_module.instances[-1]
        assert client.api_key == "ak_resolved_123"
        _slug, kwargs = client.calls[0]
        assert kwargs["user_id"] == "pg-resolved-456"

    def test_each_user_resolves_their_own_token(self, db, test_user, fake_composio_module):
        """Two users, same resource row, different effective Composio accounts."""
        self._create_placeholder_resource(db, test_user)
        other_user = _make_user(db, "composio-other-user")

        _make_mtoken(db, str(test_user.id), "my_composio_key", "ak_user_one")
        _make_mtoken(db, str(test_user.id), "my_composio_uid", "pg-user-one")
        _make_mtoken(db, str(other_user.id), "my_composio_key", "ak_user_two")
        _make_mtoken(db, str(other_user.id), "my_composio_uid", "pg-user-two")

        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        asyncio.run(ComposioService.search_tools(db, other_user, use_case="x"))

        keys = [c.api_key for c in fake_composio_module.instances]
        assert keys == ["ak_user_one", "ak_user_two"]

    def test_cannot_resolve_another_users_token(self, db, test_user, fake_composio_module):
        """Adversarial: a placeholder must never fall back to someone else's token.

        The resource `ext` is authored once (global singleton) but resolved per
        caller, so a caller who lacks the named token must fail closed rather
        than pick up another user's value.
        """
        self._create_placeholder_resource(db, test_user)
        victim = _make_user(db, "composio-victim")

        # Only the victim owns tokens with these names.
        _make_mtoken(db, str(victim.id), "my_composio_key", "ak_VICTIM_SECRET")
        _make_mtoken(db, str(victim.id), "my_composio_uid", "pg-victim")

        with pytest.raises(ValidationException, match=r"Token not found"):
            asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

        # And nothing was ever constructed with the victim's secret.
        assert all(c.api_key != "ak_VICTIM_SECRET" for c in fake_composio_module.instances)

    def test_admin_caller_also_only_sees_own_tokens(self, db, test_user, fake_composio_module):
        """Admin role grants resource visibility, never access to others' tokens."""
        from models.user import Role

        self._create_placeholder_resource(db, test_user)
        victim = _make_user(db, "composio-victim-2")
        _make_mtoken(db, str(victim.id), "my_composio_key", "ak_VICTIM_SECRET")
        _make_mtoken(db, str(victim.id), "my_composio_uid", "pg-victim")

        admin_role = Role(name="admin", description="Administrator")
        db.add(admin_role)
        test_user.roles.append(admin_role)
        db.commit()

        with pytest.raises(ValidationException, match=r"Token not found"):
            asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

    def test_unresolved_placeholder_raises_clear_error(self, db, test_user, fake_composio_module):
        self._create_placeholder_resource(db, test_user)
        # Only one of the two tokens exists.
        _make_mtoken(db, str(test_user.id), "my_composio_key", "ak_resolved_123")

        with pytest.raises(ValidationException, match=r"Token not found"):
            asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

    def test_literal_values_still_work(self, db, test_user, composio_resource, fake_composio_module):
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

        client = fake_composio_module.instances[-1]
        assert client.api_key == "ak_test"


class TestSessionCache:
    """Clients/sessions are cached per (resource, SkillHub user) with TTL + size cap."""

    def test_cache_key_is_resource_plus_uid(self, db, test_user, composio_resource, fake_composio_module):
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))

        assert ComposioService.get_cached_keys() == [f"composio::{test_user.id}"]

    def test_same_user_reuses_client_and_session(self, db, test_user, composio_resource, fake_composio_module):
        tools = [{"tool_slug": "X", "arguments": {}}]
        asyncio.run(ComposioService.multi_execute_tool(db, test_user, tools=tools))
        asyncio.run(ComposioService.multi_execute_tool(db, test_user, tools=tools))

        # One client, one session, two executions.
        assert len(fake_composio_module.instances) == 1
        client = fake_composio_module.instances[0]
        assert len(client.session_user_ids) == 1
        assert len(client.calls) == 2

    def test_different_users_never_share_a_session(self, db, test_user, shared_composio_resource, fake_composio_module):
        other_user = _make_user(db, "composio-second-user")
        tools = [{"tool_slug": "X", "arguments": {}}]

        asyncio.run(ComposioService.multi_execute_tool(db, test_user, tools=tools))
        asyncio.run(ComposioService.multi_execute_tool(db, other_user, tools=tools))

        assert len(fake_composio_module.instances) == 2
        assert sorted(ComposioService.get_cached_keys()) == sorted([
            f"composio::{test_user.id}",
            f"composio::{other_user.id}",
        ])

    def test_expired_entry_is_rebuilt(self, db, test_user, composio_resource, fake_composio_module, monkeypatch):
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        assert len(fake_composio_module.instances) == 1

        # Age the entry past the TTL.
        monkeypatch.setattr(settings, "COMPOSIO_SESSION_TTL_SECONDS", 1)
        entry = ComposioService._session_cache[f"composio::{test_user.id}"]
        entry["created_at"] -= 10

        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        assert len(fake_composio_module.instances) == 2

    def test_ttl_zero_disables_expiry(self, db, test_user, composio_resource, fake_composio_module, monkeypatch):
        monkeypatch.setattr(settings, "COMPOSIO_SESSION_TTL_SECONDS", 0)
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        entry = ComposioService._session_cache[f"composio::{test_user.id}"]
        entry["created_at"] -= 10_000

        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        assert len(fake_composio_module.instances) == 1

    def test_max_entries_evicts_oldest(self, db, test_user, shared_composio_resource, fake_composio_module, monkeypatch):
        monkeypatch.setattr(settings, "COMPOSIO_SESSION_MAX_ENTRIES", 2)

        users = [test_user] + [_make_user(db, f"composio-cap-user-{i}") for i in range(2)]
        for u in users:
            asyncio.run(ComposioService.search_tools(db, u, use_case="x"))

        cached = ComposioService.get_cached_keys()
        assert len(cached) == 2
        # The first user's entry is the oldest and must have been evicted.
        assert f"composio::{test_user.id}" not in cached

    def test_invalidate_resource_drops_all_users_entries(self, db, test_user, shared_composio_resource, fake_composio_module):
        other_user = _make_user(db, "composio-third-user")
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        asyncio.run(ComposioService.search_tools(db, other_user, use_case="x"))
        assert len(ComposioService.get_cached_keys()) == 2

        ComposioService.invalidate_resource("composio")

        assert ComposioService.get_cached_keys() == []

    def test_updating_resource_invalidates_cache(self, db, test_user, composio_resource, fake_composio_module):
        """Changing the API key in the UI must take effect immediately, not after TTL."""
        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        assert ComposioService.get_cached_keys() != []

        ResourceService.update_owner_only(
            db, composio_resource.id,
            ResourceUpdate(ext={"COMPOSIO_API_KEY": "ak_rotated", "COMPOSIO_USER_ID": "u2"}),
            user=test_user,
        )

        assert ComposioService.get_cached_keys() == []

        asyncio.run(ComposioService.search_tools(db, test_user, use_case="x"))
        assert fake_composio_module.instances[-1].api_key == "ak_rotated"
