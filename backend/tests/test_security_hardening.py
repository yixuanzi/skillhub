"""Tests for the security hardening around audit logs, outbound calls, the
signing key and password login.

- audit logs never store passwords, token values or upstream credentials
- resources cannot target local/private addresses (SSRF)
- the server refuses to start with the placeholder SECRET_KEY
- repeated failed logins are throttled
"""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from config import settings
from core import url_guard
from core.exceptions import ValidationException
from core.login_throttle import LoginThrottle
from core.redaction import REDACTED, redact, redact_request
from core.security import ensure_secret_key_is_safe
from models.resource import ResourceType
from models.system_audit_log import SystemAuditLog
from models.user import User
from schemas.resource import ResourceCreate, ResourceUpdate
from scripts import redact_audit_logs
from services.gateway_service import GatewayService
from services.resource_service import ResourceService


def stored_details(db: Session, action: str) -> dict:
    db.expire_all()
    log = (
        db.query(SystemAuditLog)
        .filter(SystemAuditLog.action == action)
        .order_by(SystemAuditLog.created_at.desc())
        .first()
    )
    assert log is not None, f"no audit row for {action!r}"
    return log.details


# --------------------------------------------------------------------------
# Audit log redaction
# --------------------------------------------------------------------------

class TestRedaction:
    def test_sensitive_keys_are_hidden_at_any_depth(self):
        cleaned = redact({
            "username": "alice",
            "password": "hunter2",
            "nested": [{"refresh_token": "abc", "X-API-Key": "k", "note": "kept"}],
            "client_secret": "s",
        })

        assert cleaned == {
            "username": "alice",
            "password": REDACTED,
            "nested": [{"refresh_token": REDACTED, "X-API-Key": REDACTED, "note": "kept"}],
            "client_secret": REDACTED,
        }

    def test_original_is_not_modified(self):
        original = {"password": "hunter2", "inner": {"token": "t"}}
        redact(original)
        assert original == {"password": "hunter2", "inner": {"token": "t"}}

    def test_empty_values_stay_distinguishable(self):
        assert redact({"password": "", "token": None}) == {"password": "", "token": None}

    def test_headers_and_ext_hide_every_string_but_keep_placeholders(self):
        cleaned = redact({
            "headers": {"X-Custom-Auth": "abc123", "Authorization": "Bearer {github_token}"},
            "ext": {"timeout": 30, "headers": {"X-Key": "{my_key}", "X-Other": "literal"}},
        })

        assert cleaned["headers"] == {"X-Custom-Auth": REDACTED, "Authorization": REDACTED}
        # A value that is only a {placeholder} names a managed token, it is not one.
        assert cleaned["ext"] == {"timeout": 30, "headers": {"X-Key": "{my_key}", "X-Other": REDACTED}}

    def test_json_passed_as_a_string_is_inspected(self):
        cleaned = redact({"inputs": json.dumps({"query": "weather", "password": "hunter2"})})
        assert json.loads(cleaned["inputs"]) == {"query": "weather", "password": REDACTED}

    def test_token_value_is_hidden_only_on_the_token_endpoints(self):
        body = {"body": {"json": {"app_name": "GitHub", "value": "ghp_secret"}}}

        assert redact_request("/api/v1/mtokens/", body)["body"]["json"]["value"] == REDACTED
        assert redact_request("/api/v1/gateway/calc/post", body)["body"]["json"]["value"] == "ghp_secret"

    def test_free_text_copies_of_a_body_are_dropped(self):
        cleaned = redact_request("/api/v1/x", {"body": {"body_type": "text/plain", "text": "password=hunter2"}})
        assert "text" not in cleaned["body"]
        assert "hunter2" not in json.dumps(cleaned)


class TestAuditLogStoresNoSecrets:
    def test_login_password_is_not_stored(self, client: TestClient, db: Session, test_user: User):
        client.post("/api/v1/auth/login/", json={"username": "testuser", "password": "testpassword123"})

        details = stored_details(db, "post /api/v1/auth/login/")
        assert details["body"]["json"] == {"username": "testuser", "password": REDACTED}
        assert "testpassword123" not in json.dumps(details)

    def test_wrong_password_is_not_stored_either(self, client: TestClient, db: Session, test_user: User):
        client.post("/api/v1/auth/login/", json={"username": "testuser", "password": "my-other-password"})

        assert "my-other-password" not in json.dumps(stored_details(db, "post /api/v1/auth/login/"))

    def test_refresh_token_is_not_stored(self, client: TestClient, db: Session, test_user: User):
        tokens = client.post(
            "/api/v1/auth/login/", json={"username": "testuser", "password": "testpassword123"}
        ).json()
        client.post("/api/v1/auth/refresh/", json={"refresh_token": tokens["refresh_token"]})

        details = stored_details(db, "post /api/v1/auth/refresh/")
        assert details["body"]["json"] == {"refresh_token": REDACTED}

    def test_managed_token_value_is_not_stored(self, client: TestClient, db: Session, auth_headers: dict):
        response = client.post(
            "/api/v1/mtokens/",
            json={"app_name": "GitHub", "key_name": "pat", "value": "ghp_super_secret_value"},
            headers=auth_headers,
        )
        assert response.status_code == 201

        details = stored_details(db, "post /api/v1/mtokens/")
        assert details["body"]["json"]["value"] == REDACTED
        assert details["body"]["json"]["app_name"] == "GitHub"
        assert "ghp_super_secret_value" not in json.dumps(details)

    def test_resource_credentials_are_not_stored(self, client: TestClient, db: Session, auth_headers: dict):
        response = client.post(
            "/api/v1/resources/",
            json={
                "name": "audited-api", "type": "third", "url": "https://api.example.com/v1",
                "ext": {"headers": {"X-Upstream-Key": "upstream-secret", "X-Ref": "{my_token}"}},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

        details = stored_details(db, "post /api/v1/resources/")
        assert details["body"]["json"]["ext"]["headers"] == {"X-Upstream-Key": REDACTED, "X-Ref": "{my_token}"}
        assert details["body"]["json"]["name"] == "audited-api"
        assert "upstream-secret" not in json.dumps(details)

    def test_secrets_in_query_strings_are_not_stored(self, client: TestClient, db: Session, auth_headers: dict):
        client.get("/api/v1/skills/?search=weather&access_token=leaked", headers=auth_headers)

        details = stored_details(db, "get /api/v1/skills/")
        assert details["query_params"] == {"search": "weather", "access_token": REDACTED}


class TestRedactExistingRows:
    """scripts/redact_audit_logs.py: rows written before redaction existed."""

    def _row(self, db: Session, action: str, details) -> str:
        log = SystemAuditLog(action=action, resource_type="auth", details=details, status="success")
        db.add(log)
        db.commit()
        return log.id

    def test_old_rows_are_redacted_and_otherwise_kept(self, db: Session):
        leaked = self._row(db, "post /api/v1/auth/login/", {
            "method": "POST", "path": "/api/v1/auth/login/", "status_code": 200,
            "body": {"body_type": "application/json", "json": {"username": "admin", "password": "admin123"}},
        })
        token = self._row(db, "post /api/v1/mtokens/", {
            "path": "/api/v1/mtokens/",
            "body": {"json": {"app_name": "GitHub", "value": "ghp_secret"}},
        })
        clean = self._row(db, "get /api/v1/skills/", {"path": "/api/v1/skills/", "query_params": {"page": "1"}})

        changed = redact_audit_logs.redact_logs(db)
        db.commit()
        db.expire_all()

        assert dict(changed) == {"post /api/v1/auth/login/": 1, "post /api/v1/mtokens/": 1}
        login = db.query(SystemAuditLog).filter(SystemAuditLog.id == leaked).one()
        assert login.details["body"]["json"] == {"username": "admin", "password": REDACTED}
        assert login.details["status_code"] == 200
        assert db.query(SystemAuditLog).filter(SystemAuditLog.id == token).one().details["body"]["json"] == {
            "app_name": "GitHub", "value": REDACTED,
        }
        assert db.query(SystemAuditLog).filter(SystemAuditLog.id == clean).one().details == {
            "path": "/api/v1/skills/", "query_params": {"page": "1"},
        }

    def test_running_twice_changes_nothing(self, db: Session):
        self._row(db, "post /api/v1/auth/login/", {
            "path": "/api/v1/auth/login/", "body": {"json": {"username": "a", "password": "b"}},
        })

        assert sum(redact_audit_logs.redact_logs(db).values()) == 1
        db.commit()
        assert sum(redact_audit_logs.redact_logs(db).values()) == 0


# --------------------------------------------------------------------------
# Outbound URL guard (SSRF)
# --------------------------------------------------------------------------

LOCAL_TARGETS = [
    "http://127.0.0.1:8000/admin",
    "http://localhost:5432/",
    "http://db.localhost/",
    "http://169.254.169.254/latest/meta-data/",   # cloud metadata
    "http://10.0.0.5/internal",
    "http://172.16.3.4/",
    "http://192.168.1.1/",
    "http://0.0.0.0:8000/",
    "http://[::1]:8000/",
    "http://[fd00::1]/",                           # unique-local IPv6
    "http://[::ffff:10.0.0.5]/",                   # IPv4-mapped private address
    "http://100.64.0.1/",                          # carrier-grade NAT range
]


@pytest.fixture
def resolve_to(monkeypatch):
    """Make every hostname resolve to the given addresses."""
    def install(*addresses):
        async def resolve(host, port):
            return list(addresses)
        monkeypatch.setattr(url_guard, "_resolve", resolve)
    return install


@pytest.fixture
def allow_hosts(monkeypatch):
    def install(*entries):
        monkeypatch.setattr(settings, "GATEWAY_ALLOWED_HOSTS", list(entries))
    return install


class TestUrlGuard:
    @pytest.mark.parametrize("url", LOCAL_TARGETS)
    def test_local_and_private_targets_are_refused(self, url):
        with pytest.raises(ValidationException, match="local or private"):
            url_guard.check_url(url)

    @pytest.mark.parametrize("url", ["https://api.example.com/v1", "http://93.184.216.34/", "https://[2606:4700::1111]/"])
    def test_public_targets_are_accepted(self, url):
        url_guard.check_url(url)

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "gopher://10.0.0.1/", "ftp://example.com/", "example.com/x", ""])
    def test_only_http_and_https_are_accepted(self, url):
        with pytest.raises(ValidationException):
            url_guard.check_url(url)

    def test_public_name_that_resolves_to_a_private_address_is_refused(self, resolve_to):
        resolve_to("10.0.0.5")
        # Nothing wrong with the name itself, so the DNS-free check lets it through...
        url_guard.check_url("https://innocent.example.com/")
        # ...and the call-time check catches it.
        with pytest.raises(ValidationException, match="local or private"):
            asyncio.run(url_guard.ensure_url_allowed("https://innocent.example.com/"))

    def test_one_private_address_among_several_is_enough_to_refuse(self, resolve_to):
        resolve_to("93.184.216.34", "127.0.0.1")
        with pytest.raises(ValidationException, match="local or private"):
            asyncio.run(url_guard.ensure_url_allowed("https://mixed.example.com/"))

    def test_public_name_is_allowed_at_call_time(self, resolve_to):
        resolve_to("93.184.216.34")
        asyncio.run(url_guard.ensure_url_allowed("https://api.example.com/v1"))

    def test_unresolvable_name_is_refused(self, monkeypatch):
        async def resolve(host, port):
            raise OSError("no such host")
        monkeypatch.setattr(url_guard, "_resolve", resolve)

        with pytest.raises(ValidationException, match="could not be resolved"):
            asyncio.run(url_guard.ensure_url_allowed("https://nope.example.com/"))

    def test_refusal_does_not_reveal_the_resolved_address(self, resolve_to):
        resolve_to("10.9.8.7")
        with pytest.raises(ValidationException) as exc:
            asyncio.run(url_guard.ensure_url_allowed("https://intranet.example.com/"))
        assert "10.9.8.7" not in str(exc.value)


class TestUrlGuardAllowlist:
    def test_cidr_allows_addresses_inside_it_only(self, allow_hosts):
        allow_hosts("10.20.0.0/16")

        url_guard.check_url("http://10.20.3.4/")
        with pytest.raises(ValidationException):
            url_guard.check_url("http://10.21.0.1/")

    def test_cidr_applies_to_resolved_addresses(self, allow_hosts, resolve_to):
        allow_hosts("10.20.0.0/16")
        resolve_to("10.20.3.4")

        asyncio.run(url_guard.ensure_url_allowed("https://billing.internal/"))

    def test_hostname_entry_allows_that_name_whatever_it_resolves_to(self, allow_hosts, resolve_to):
        allow_hosts("billing.internal")
        resolve_to("10.0.0.5")

        asyncio.run(url_guard.ensure_url_allowed("https://billing.internal/api"))
        with pytest.raises(ValidationException):
            asyncio.run(url_guard.ensure_url_allowed("https://other.internal/api"))

    def test_wildcard_suffix(self, allow_hosts, resolve_to):
        allow_hosts("*.corp.example.com")
        resolve_to("10.0.0.5")

        asyncio.run(url_guard.ensure_url_allowed("https://wiki.corp.example.com/"))
        with pytest.raises(ValidationException):
            asyncio.run(url_guard.ensure_url_allowed("https://corp.example.com.evil.test/"))

    def test_star_turns_the_guard_off(self, allow_hosts):
        allow_hosts("*")
        for url in LOCAL_TARGETS:
            url_guard.check_url(url)


class TestResourcesCannotTargetTheInternalNetwork:
    def test_create_is_refused(self, client: TestClient, db: Session, auth_headers: dict):
        response = client.post(
            "/api/v1/resources/",
            json={"name": "metadata", "type": "third", "url": "http://169.254.169.254/latest/meta-data/"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "local or private" in response.json()["detail"]

    def test_update_to_a_local_url_is_refused(self, db: Session, test_user: User):
        resource = ResourceService.create(
            db, ResourceCreate(name="moved", type=ResourceType.GATEWAY, url="https://api.example.com"), user=test_user,
        )

        with pytest.raises(ValidationException, match="local or private"):
            ResourceService.update_owner_only(
                db, resource.id, ResourceUpdate(url="http://127.0.0.1:8000"), user=test_user,
            )

    @pytest.mark.parametrize("ext", [
        {"transport": "sse", "endpoint": "http://localhost:3000/sse"},
        {"mcp_config": {"transport": "httpstream", "endpoint": "http://10.0.0.5/mcp"}},
    ], ids=["flat", "nested"])
    def test_mcp_endpoint_is_checked_too(self, db: Session, test_user: User, ext):
        with pytest.raises(ValidationException, match="local or private"):
            ResourceService.create(
                db, ResourceCreate(name="local-mcp", type=ResourceType.MCP, ext=ext), user=test_user,
            )

    def test_mcp_connection_is_refused_when_the_name_resolves_to_a_private_address(self, resolve_to):
        """Checked before a client is built, for a name that looked fine when it was saved."""
        from schemas.resource import MCPConfig
        from services.mcp_service import MCPService

        resolve_to("10.0.0.5")
        config = MCPConfig(transport="sse", endpoint="https://innocent.example.com/sse")

        with pytest.raises(ValidationException, match="local or private"):
            asyncio.run(MCPService._get_or_create_client("guarded-mcp", config, None, "user-1"))

    def test_allowlisted_internal_target_can_be_created(self, db: Session, test_user: User, allow_hosts):
        allow_hosts("10.20.0.0/16")

        created = ResourceService.create(
            db, ResourceCreate(name="internal", type=ResourceType.THIRD, url="http://10.20.3.4/api"), user=test_user,
        )
        assert created.url == "http://10.20.3.4/api"

    @pytest.mark.parametrize("rtype", [ResourceType.THIRD, ResourceType.GATEWAY])
    def test_call_is_refused_when_the_name_resolves_to_a_private_address(
        self, db: Session, test_user: User, resolve_to, monkeypatch, rtype
    ):
        """The request must never be sent: the check runs before the HTTP client is built."""
        import httpx

        resource = ResourceService.create(
            db, ResourceCreate(name=f"rebound-{rtype.value}", type=rtype, url="https://innocent.example.com"),
            user=test_user,
        )
        resolve_to("10.0.0.5")

        def no_http_client(*args, **kwargs):
            raise AssertionError("an outbound request was attempted")
        monkeypatch.setattr(httpx, "AsyncClient", no_http_client)

        result = asyncio.run(GatewayService.call_resource(
            db, resource.name, method="GET", path="status", user=test_user,
        ))

        # call_resource reports failures in its result rather than raising.
        assert result["success"] is False
        assert "local or private" in result["error"]


# --------------------------------------------------------------------------
# SECRET_KEY startup check
# --------------------------------------------------------------------------

class TestSecretKeyCheck:
    @pytest.mark.parametrize("key", ["your-secret-key-change-in-production", "Your-Secret-Key-Change-In-Production", "changeme", "short", ""])
    def test_placeholder_or_short_key_is_refused(self, monkeypatch, key):
        monkeypatch.setattr(settings, "SECRET_KEY", key)
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            ensure_secret_key_is_safe()

    def test_random_key_is_accepted(self, monkeypatch):
        monkeypatch.setattr(settings, "SECRET_KEY", "Zk3vN8qT1xW6yB4mC9dF2hJ7lP0sR5uA8eG1iK4oM7")
        ensure_secret_key_is_safe()

    def test_server_does_not_start_with_the_placeholder(self, monkeypatch):
        from main import app

        monkeypatch.setattr(settings, "SECRET_KEY", "your-secret-key-change-in-production")
        with pytest.raises(RuntimeError, match="Refusing to start"):
            with TestClient(app):
                pass


# --------------------------------------------------------------------------
# Login throttling
# --------------------------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def throttle(clock):
    return LoginThrottle(clock=clock)


class TestLoginThrottle:
    def test_blocks_at_the_limit_and_not_before(self, throttle):
        for _ in range(settings.LOGIN_MAX_FAILURES - 1):
            throttle.record_failure("alice", "1.1.1.1")
        assert throttle.retry_after("alice", "1.1.1.1") == 0

        throttle.record_failure("alice", "1.1.1.1")
        assert throttle.retry_after("alice", "1.1.1.1") > 0

    def test_username_is_blocked_from_any_address(self, throttle):
        for i in range(settings.LOGIN_MAX_FAILURES):
            throttle.record_failure("alice", f"1.1.1.{i}")

        assert throttle.retry_after("Alice", "9.9.9.9") > 0      # case-insensitive
        assert throttle.retry_after("bob", "9.9.9.9") == 0

    def test_block_lifts_when_the_window_moves_on(self, throttle, clock):
        for _ in range(settings.LOGIN_MAX_FAILURES):
            throttle.record_failure("alice", "1.1.1.1")
        wait = throttle.retry_after("alice", "1.1.1.1")
        assert 0 < wait <= settings.LOGIN_FAILURE_WINDOW_SECONDS + 1

        clock.advance(wait)
        assert throttle.retry_after("alice", "1.1.1.1") == 0

    def test_success_clears_the_username(self, throttle):
        for _ in range(settings.LOGIN_MAX_FAILURES - 1):
            throttle.record_failure("alice", "1.1.1.1")
        throttle.record_success("alice")
        throttle.record_failure("alice", "1.1.1.1")

        assert throttle.retry_after("alice", "1.1.1.1") == 0

    def test_one_address_trying_many_usernames_is_blocked(self, throttle):
        for i in range(settings.LOGIN_MAX_FAILURES_PER_IP):
            throttle.record_failure(f"user{i}", "6.6.6.6")

        assert throttle.retry_after("someone-new", "6.6.6.6") > 0
        assert throttle.retry_after("someone-new", "7.7.7.7") == 0

    def test_limit_of_zero_disables_it(self, throttle, monkeypatch):
        monkeypatch.setattr(settings, "LOGIN_MAX_FAILURES", 0)
        for _ in range(50):
            throttle.record_failure("alice", None)

        assert throttle.retry_after("alice", None) == 0


class TestLoginEndpointThrottling:
    def _login(self, client, password, username="testuser"):
        return client.post("/api/v1/auth/login/", json={"username": username, "password": password})

    def test_account_is_locked_after_repeated_failures(self, client: TestClient, test_user: User):
        for _ in range(settings.LOGIN_MAX_FAILURES):
            assert self._login(client, "wrong-password").status_code == 401

        blocked = self._login(client, "wrong-password")
        assert blocked.status_code == 429
        assert int(blocked.headers["Retry-After"]) > 0
        assert "Too many failed login attempts" in blocked.json()["detail"]

    def test_correct_password_does_not_get_through_while_locked(self, client: TestClient, test_user: User):
        for _ in range(settings.LOGIN_MAX_FAILURES):
            self._login(client, "wrong-password")

        assert self._login(client, "testpassword123").status_code == 429

    def test_unknown_usernames_are_counted_too(self, client: TestClient):
        for _ in range(settings.LOGIN_MAX_FAILURES):
            assert self._login(client, "x", username="nobody").status_code == 401

        assert self._login(client, "x", username="nobody").status_code == 429

    def test_other_accounts_are_not_affected(self, client: TestClient, test_user: User, admin_user: User):
        for _ in range(settings.LOGIN_MAX_FAILURES):
            self._login(client, "wrong-password")

        assert self._login(client, "adminpassword123", username="admin").status_code == 200

    def test_successful_login_resets_the_count(self, client: TestClient, test_user: User):
        for _ in range(settings.LOGIN_MAX_FAILURES - 1):
            self._login(client, "wrong-password")
        assert self._login(client, "testpassword123").status_code == 200

        for _ in range(settings.LOGIN_MAX_FAILURES - 1):
            assert self._login(client, "wrong-password").status_code == 401
        assert self._login(client, "testpassword123").status_code == 200
