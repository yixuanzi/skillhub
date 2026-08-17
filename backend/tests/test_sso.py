from urllib.parse import parse_qs, urlparse

import pytest

import api.sso as sso_module
from config import settings
from models.oidc import OidcLoginTransaction, SsoLoginTicket
from models.user import Role, User
from core.security import get_password_hash


@pytest.fixture
def oidc_settings(monkeypatch):
    monkeypatch.setattr(settings, "OIDC_ISSUER", "http://portal.example")
    monkeypatch.setattr(settings, "OIDC_BACKCHANNEL_URL", "http://portal-api.example")
    monkeypatch.setattr(settings, "OIDC_CLIENT_ID", "skillhub-client")
    monkeypatch.setattr(settings, "OIDC_CLIENT_SECRET", "server-only-secret")
    monkeypatch.setattr(settings, "OIDC_REDIRECT_URI", "http://skillhub.example/api/v1/sso/callback")
    monkeypatch.setattr(settings, "OIDC_POST_LOGIN_REDIRECT", "/sso/callback")
    monkeypatch.setattr(settings, "OIDC_TICKET_TTL_SECONDS", 60)
    return settings


def test_sso_start_uses_s256_and_hides_subscription_id(client, db, oidc_settings):
    response = client.get("/api/v1/sso/start?sso=1", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    assert params["client_id"] == ["skillhub-client"]
    assert params["sso"] == ["1"]
    assert params["code_challenge_method"] == ["S256"]
    assert "organization_id" not in params
    assert "subscription_id" not in params
    assert db.query(OidcLoginTransaction).count() == 1


def test_direct_start_requires_matching_client_and_organization(client, oidc_settings):
    missing_client = client.get("/api/v1/sso/start?organization_id=org-1")
    assert missing_client.status_code == 400

    wrong_client = client.get(
        "/api/v1/sso/start?organization_id=org-1&client_id=wrong-client"
    )
    assert wrong_client.status_code == 400

    valid = client.get(
        "/api/v1/sso/start?organization_id=org-1&client_id=skillhub-client",
        follow_redirects=False,
    )
    assert valid.status_code == 302
    params = parse_qs(urlparse(valid.headers["location"]).query)
    assert params["organization_id"] == ["org-1"]
    assert "sso" not in params


def test_callback_creates_local_viewer_and_ticket_is_one_time(
    client, db, oidc_settings, monkeypatch
):
    start = client.get("/api/v1/sso/start?sso=1", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    async def fake_exchange(transaction, code):
        assert transaction.state == state
        assert code == "portal-code"
        claims = {
            "sub": "portal-user-1",
            "organization_id": "org-1",
            "email": "new-user@example.com",
            "name": "New User",
        }
        return claims, {**claims}

    monkeypatch.setattr(sso_module, "_exchange_code", fake_exchange)
    callback = client.get(
        f"/api/v1/sso/callback?state={state}&code=portal-code",
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert callback.headers["location"] == "/sso/callback"
    assert "skillhub_sso_ticket=" in callback.headers["set-cookie"]

    exchange = client.post("/api/v1/sso/exchange")
    assert exchange.status_code == 200
    assert exchange.json()["access_token"]
    assert exchange.json()["refresh_token"]

    replay = client.post("/api/v1/sso/exchange")
    assert replay.status_code == 401

    user = db.query(User).filter(User.oidc_subject == "portal-user-1").one()
    assert user.is_active is True
    assert [role.name for role in user.roles] == ["viewer"]


def test_existing_same_email_user_is_bound_without_role_escalation(client, db, oidc_settings):
    existing = User(
        username="existing-user",
        email="existing@example.com",
        hashed_password=get_password_hash("local-password-123"),
        is_active=True,
    )
    admin = Role(name="admin", description="local admin")
    existing.roles = [admin]
    db.add(existing)
    db.commit()

    user = sso_module._upsert_local_user(
        db,
        {"sub": "portal-existing"},
        {
            "sub": "portal-existing",
            "email": "existing@example.com",
            "name": "Existing User",
            "organization_id": "org-1",
        },
    )
    db.commit()

    assert user.id == existing.id
    assert user.oidc_subject == "portal-existing"
    assert [role.name for role in user.roles] == ["admin"]


def test_callback_rejects_organization_mismatch(client, db, oidc_settings, monkeypatch):
    start = client.get(
        "/api/v1/sso/start?organization_id=org-expected&client_id=skillhub-client",
        follow_redirects=False,
    )
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    async def fake_exchange(transaction, code):
        claims = {"sub": "portal-user-2", "organization_id": "org-other", "email": "other@example.com"}
        return claims, {**claims}

    monkeypatch.setattr(sso_module, "_exchange_code", fake_exchange)
    callback = client.get(
        f"/api/v1/sso/callback?state={state}&code=portal-code",
        follow_redirects=False,
    )
    assert callback.status_code == 302
    assert "access_denied" in callback.headers["location"]
    assert db.query(SsoLoginTicket).count() == 0
