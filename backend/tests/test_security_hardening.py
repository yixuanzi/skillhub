"""Tests for the security hardening around audit logs, the signing key and
password login.

- audit logs never store passwords, token values or upstream credentials
- the server refuses to start with the placeholder SECRET_KEY
- repeated failed logins are throttled
"""
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from config import settings
from core.login_throttle import LoginThrottle
from core.redaction import REDACTED, redact, redact_request
from core.security import ensure_secret_key_is_safe
from models.system_audit_log import SystemAuditLog
from models.user import User
from scripts import redact_audit_logs


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
