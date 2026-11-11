"""Tests for the SkillHub MCP server (Streamable HTTP) at /api/v1/mcp.

The server exposes the scripts/skillhub CLI as MCP tools, so these tests pin
the two things that have to stay in step with the CLI: the tool/argument
surface, and how each tool's arguments are translated into service calls.
"""
import json

import pytest
from fastapi.testclient import TestClient

from main import app
from models.resource import ResourceType
from models.skill_list import SkillList
from schemas.resource import ResourceCreate
from services.composio_service import ComposioService
from services.gateway_service import GatewayService
from services.mcp_service import MCPService
from services.resource_service import ResourceService

MCP_URL = "/api/v1/mcp"
MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

EXPECTED_TOOLS = {
    "list", "install", "getme", "third", "gateway", "mcp",
    "composio_search", "composio_schema", "composio_exec",
}


@pytest.fixture
def mcp_client(db):
    """Client with the app lifespan running - the MCP session manager lives there."""
    with TestClient(app) as test_client:
        yield test_client


def rpc(client, method, params=None, headers=None):
    response = client.post(
        MCP_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
        headers={**MCP_HEADERS, **(headers or {})},
    )
    assert response.status_code == 200, response.text
    return response.json()


def call_tool(client, name, arguments=None, headers=None):
    """Call a tool; return (is_error, [text blocks])."""
    body = rpc(client, "tools/call", {"name": name, "arguments": arguments or {}}, headers)
    result = body["result"]
    return result.get("isError", False), [block["text"] for block in result["content"]]


def call_ok(client, name, arguments=None, headers=None):
    is_error, texts = call_tool(client, name, arguments, headers)
    assert not is_error, texts
    return texts


def call_err(client, name, arguments=None, headers=None):
    is_error, texts = call_tool(client, name, arguments, headers)
    assert is_error, texts
    return texts[0]


class TestTransport:
    def test_initialize(self, mcp_client):
        body = rpc(mcp_client, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0"},
        })
        assert body["result"]["serverInfo"]["name"] == "skillhub"
        assert "tools" in body["result"]["capabilities"]

    def test_tool_surface_matches_the_cli(self, mcp_client):
        tools = {t["name"]: t for t in rpc(mcp_client, "tools/list")["result"]["tools"]}
        assert set(tools) == EXPECTED_TOOLS

        def args(name):
            return set(tools[name]["inputSchema"].get("properties", {}))

        def required(name):
            return set(tools[name]["inputSchema"].get("required", []))

        assert args("list") == {"search_term", "page"}
        assert args("install") == {"skill_name", "outdir"}
        assert args("getme") == set()
        assert args("third") == {"res_name", "method", "inputs", "timeout"}
        assert required("third") == {"res_name", "method"}
        assert args("gateway") == {"res_name", "method", "path", "inputs", "timeout"}
        assert required("gateway") == {"res_name", "method", "path"}
        assert args("mcp") == {"res_name", "mcptool", "inputs", "timeout"}
        assert required("mcp") == {"res_name", "mcptool"}
        assert args("composio_search") == {"use_case", "known_fields", "timeout"}
        assert args("composio_schema") == {"tool_slugs", "timeout"}
        assert args("composio_exec") == {"tool_slug", "inputs", "tools", "timeout"}

    def test_trailing_slash_is_served_without_redirect(self, mcp_client):
        response = mcp_client.post(
            MCP_URL + "/",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers=MCP_HEADERS,
            follow_redirects=False,
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("method", ["get", "delete"])
    def test_non_post_is_405(self, mcp_client, method):
        response = getattr(mcp_client, method)(MCP_URL, headers=MCP_HEADERS)
        assert response.status_code == 405
        assert response.headers["allow"] == "POST"

    def test_invalid_token_is_rejected_at_connect_time(self, mcp_client):
        response = mcp_client.post(
            MCP_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={**MCP_HEADERS, "Authorization": "Bearer sk_not_a_real_key"},
        )
        assert response.status_code == 401

    def test_non_bearer_authorization_is_rejected(self, mcp_client):
        response = mcp_client.post(
            MCP_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={**MCP_HEADERS, "Authorization": "Basic abc"},
        )
        assert response.status_code == 401

    def test_endpoint_reports_503_when_lifespan_is_not_running(self, client):
        response = client.post(
            MCP_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers=MCP_HEADERS,
        )
        assert response.status_code == 503


class TestGetme:
    def test_requires_authentication(self, mcp_client):
        assert "No authentication token" in call_err(mcp_client, "getme")

    def test_returns_current_user(self, mcp_client, test_user, auth_headers):
        user = json.loads(call_ok(mcp_client, "getme", headers=auth_headers)[0])
        assert user["username"] == "testuser"
        assert user["id"] == test_user.id
        assert "hashed_password" not in user


class TestSkills:
    @pytest.fixture
    def skills(self, db, test_user):
        db.add_all([
            SkillList(name="weather-public", content="# public", created_by=test_user.id,
                      tags="public,published"),
            SkillList(name="weather-internal", content="# internal", created_by=test_user.id,
                      tags="published"),
            SkillList(name="billing", content="# billing", created_by=test_user.id,
                      tags="published"),
        ])
        db.commit()

    def test_anonymous_list_shows_public_skills_only(self, mcp_client, skills):
        data = json.loads(call_ok(mcp_client, "list")[0])
        assert [item["name"] for item in data["items"]] == ["weather-public"]
        assert "content" not in data["items"][0]

    def test_authenticated_list_and_search(self, mcp_client, skills, auth_headers):
        data = json.loads(call_ok(mcp_client, "list", headers=auth_headers)[0])
        assert data["total"] == 3
        assert (data["page"], data["size"]) == (1, 20)

        data = json.loads(
            call_ok(mcp_client, "list", {"search_term": "weather"}, auth_headers)[0]
        )
        assert {item["name"] for item in data["items"]} == {"weather-public", "weather-internal"}

    def test_list_page(self, mcp_client, skills, auth_headers):
        data = json.loads(call_ok(mcp_client, "list", {"page": 2}, auth_headers)[0])
        assert data["page"] == 2
        assert data["items"] == []

    def test_install_returns_target_path_and_exact_content(self, mcp_client, skills, auth_headers):
        instruction, content = call_ok(
            mcp_client, "install", {"skill_name": "weather-internal"}, auth_headers
        )
        assert "~/.agents/skills/weather-internal/SKILL.md" in instruction
        assert content == "# internal"

    def test_install_honours_outdir(self, mcp_client, skills, auth_headers):
        instruction, _ = call_ok(
            mcp_client, "install",
            {"skill_name": "weather-internal", "outdir": "./my-skills/"}, auth_headers,
        )
        assert "./my-skills/weather-internal/SKILL.md" in instruction

    def test_anonymous_install_is_limited_to_public_skills(self, mcp_client, skills):
        assert call_ok(mcp_client, "install", {"skill_name": "weather-public"})[1] == "# public"
        assert "access denied" in call_err(mcp_client, "install", {"skill_name": "weather-internal"})

    def test_install_unknown_skill(self, mcp_client, auth_headers):
        assert "not found" in call_err(mcp_client, "install", {"skill_name": "nope"}, auth_headers)


@pytest.fixture
def gateway_calls(monkeypatch):
    """Record GatewayService.call_resource invocations and return a canned success."""
    calls = []

    async def fake_call_resource(**kwargs):
        calls.append(kwargs)
        return {"success": True, "data": {"ok": True}}

    monkeypatch.setattr(GatewayService, "call_resource", staticmethod(fake_call_resource))
    return calls


class TestThirdAndGateway:
    def test_requires_authentication(self, mcp_client, gateway_calls):
        message = call_err(mcp_client, "third", {"res_name": "weather-api", "method": "GET"})
        assert "No authentication token" in message
        assert gateway_calls == []

    def test_third_get_sends_inputs_as_query_params(self, mcp_client, auth_headers, gateway_calls, test_user):
        text = call_ok(mcp_client, "third", {
            "res_name": "weather-api", "method": "get",
            "inputs": {"city": "Beijing", "limit": 100, "tag": ["a", "b"]},
        }, auth_headers)[0]

        assert json.loads(text) == {"ok": True}
        call = gateway_calls[0]
        assert call["resource_name"] == "weather-api"
        assert call["user"].id == test_user.id
        assert call["method"] == "GET"
        # Stringified and de-duplicated exactly as the CLI's query string would be.
        assert call["params"] == {"city": "Beijing", "limit": "100", "tag": "b"}
        assert call["body"] is None
        assert call["path"] == ""

    def test_third_post_sends_inputs_as_body(self, mcp_client, auth_headers, gateway_calls):
        call_ok(mcp_client, "third", {
            "res_name": "user-service", "method": "POST", "inputs": {"name": "John", "age": 3},
        }, auth_headers)
        call = gateway_calls[0]
        assert call["method"] == "POST"
        assert call["params"] is None
        assert call["body"] == {"name": "John", "age": 3}

    def test_inputs_may_be_a_json_string(self, mcp_client, auth_headers, gateway_calls):
        call_ok(mcp_client, "third", {
            "res_name": "user-service", "method": "POST", "inputs": '{"name": "John"}',
        }, auth_headers)
        assert gateway_calls[0]["body"] == {"name": "John"}

    def test_inputs_must_be_an_object(self, mcp_client, auth_headers, gateway_calls):
        # FastMCP decodes JSON strings before validating, so this is refused by
        # the argument schema rather than by our own check - either way no call.
        message = call_err(mcp_client, "third", {
            "res_name": "user-service", "method": "POST", "inputs": "[1, 2]",
        }, auth_headers)
        assert "inputs" in message
        assert gateway_calls == []

    def test_invalid_method(self, mcp_client, auth_headers, gateway_calls):
        message = call_err(mcp_client, "third", {"res_name": "x", "method": "PATCH"}, auth_headers)
        assert "Invalid method 'PATCH'" in message
        assert gateway_calls == []

    def test_gateway_strips_leading_slash_and_passes_path(self, mcp_client, auth_headers, gateway_calls):
        call_ok(mcp_client, "gateway", {
            "res_name": "backend-api", "method": "PUT", "path": "/users/123",
            "inputs": {"name": "Jane"},
        }, auth_headers)
        call = gateway_calls[0]
        assert (call["method"], call["path"]) == ("PUT", "users/123")
        assert call["body"] == {"name": "Jane"}

    def test_gateway_delete_sends_query_params(self, mcp_client, auth_headers, gateway_calls):
        call_ok(mcp_client, "gateway", {
            "res_name": "backend-api", "method": "DELETE", "path": "users/123",
            "inputs": {"force": True},
        }, auth_headers)
        call = gateway_calls[0]
        assert call["params"] == {"force": "True"}
        assert call["body"] is None

    def test_gateway_mcp_tools_path_lists_mcp_tools(self, mcp_client, auth_headers, gateway_calls, monkeypatch):
        async def fake_list_tools(db, resource_name, user):
            return [{"name": "echo", "description": "Echo", "args_schema": None}]

        monkeypatch.setattr(MCPService, "list_tools", staticmethod(fake_list_tools))
        text = call_ok(mcp_client, "gateway", {
            "res_name": "my-mcp", "method": "GET", "path": "mcp/tools",
        }, auth_headers)[0]
        assert json.loads(text)["tools"][0]["name"] == "echo"
        assert gateway_calls == []

    def test_text_response_is_returned_verbatim(self, mcp_client, auth_headers, monkeypatch):
        async def fake_call_resource(**kwargs):
            return {"success": True, "data": "plain text"}

        monkeypatch.setattr(GatewayService, "call_resource", staticmethod(fake_call_resource))
        assert call_ok(mcp_client, "third", {"res_name": "x", "method": "GET"}, auth_headers) == ["plain text"]

    def test_unknown_resource_is_a_tool_error(self, mcp_client, auth_headers):
        message = call_err(mcp_client, "third", {"res_name": "missing", "method": "GET"}, auth_headers)
        assert "Not found" in message

    def test_acl_denial_is_enforced_for_real(self, mcp_client, db, test_user, user2, auth_headers_user2):
        """No mocks: a resource the caller has no ACL grant on must be refused."""
        ResourceService.create(db, ResourceCreate(
            name="private-api", type=ResourceType.THIRD, url="https://api.example.com",
            view_scope="public",
        ), user=test_user)

        message = call_err(
            mcp_client, "third", {"res_name": "private-api", "method": "GET"}, auth_headers_user2
        )
        assert "Permission denied" in message

    def test_timeout_is_reported(self, mcp_client, auth_headers, monkeypatch):
        import asyncio

        async def slow_call_resource(**kwargs):
            await asyncio.sleep(5)

        monkeypatch.setattr(GatewayService, "call_resource", staticmethod(slow_call_resource))
        message = call_err(
            mcp_client, "third", {"res_name": "x", "method": "GET", "timeout": 1}, auth_headers
        )
        assert "timed out after 1s" in message


class TestMcpResource:
    def test_calls_the_mcp_resource(self, mcp_client, auth_headers, monkeypatch, test_user):
        calls = []

        async def fake_call(db, resource_name, method, params, user):
            calls.append((resource_name, method, params, user.id))
            return [{"type": "text", "text": "sunny"}]

        monkeypatch.setattr(MCPService, "call_mcp_resource", staticmethod(fake_call))
        text = call_ok(mcp_client, "mcp", {
            "res_name": "my-mcp", "mcptool": "weather", "inputs": {"location": "Tokyo"},
        }, auth_headers)[0]

        assert calls == [("my-mcp", "weather", {"location": "Tokyo"}, test_user.id)]
        assert json.loads(text) == [{"type": "text", "text": "sunny"}]

    def test_inputs_default_to_empty_object(self, mcp_client, auth_headers, monkeypatch):
        seen = {}

        async def fake_call(db, resource_name, method, params, user):
            seen["params"] = params
            return "done"

        monkeypatch.setattr(MCPService, "call_mcp_resource", staticmethod(fake_call))
        assert call_ok(mcp_client, "mcp", {"res_name": "m", "mcptool": "t"}, auth_headers) == ["done"]
        assert seen["params"] == {}

    def test_unknown_resource(self, mcp_client, auth_headers):
        message = call_err(mcp_client, "mcp", {"res_name": "missing", "mcptool": "t"}, auth_headers)
        assert "not found" in message


class TestComposio:
    @pytest.fixture
    def composio(self, monkeypatch):
        calls = {}

        async def fake_search(db, user, use_case, known_fields=None):
            calls["search"] = (use_case, known_fields)
            return {"data": {"results": []}}

        async def fake_schema(db, user, tool_slugs):
            calls["schema"] = tool_slugs
            return {"data": {}}

        async def fake_exec(db, user, tools):
            calls["exec"] = tools
            return {"data": {"results": []}}

        monkeypatch.setattr(ComposioService, "search_tools", staticmethod(fake_search))
        monkeypatch.setattr(ComposioService, "get_tool_schemas", staticmethod(fake_schema))
        monkeypatch.setattr(ComposioService, "multi_execute_tool", staticmethod(fake_exec))
        return calls

    def test_search(self, mcp_client, auth_headers, composio):
        call_ok(mcp_client, "composio_search", {
            "use_case": "search issues in jira", "known_fields": "project_key:VMS",
        }, auth_headers)
        assert composio["search"] == ("search issues in jira", "project_key:VMS")

    def test_schema(self, mcp_client, auth_headers, composio):
        call_ok(mcp_client, "composio_schema", {
            "tool_slugs": ["JIRA_SEARCH_ISSUES", "SLACK_SEND_MESSAGE"],
        }, auth_headers)
        assert composio["schema"] == ["JIRA_SEARCH_ISSUES", "SLACK_SEND_MESSAGE"]

    def test_exec_single_form(self, mcp_client, auth_headers, composio):
        call_ok(mcp_client, "composio_exec", {
            "tool_slug": "JIRA_SEARCH_ISSUES", "inputs": {"project_key": "VMS"},
        }, auth_headers)
        assert composio["exec"] == [
            {"tool_slug": "JIRA_SEARCH_ISSUES", "arguments": {"project_key": "VMS"}}
        ]

    def test_exec_single_form_without_inputs(self, mcp_client, auth_headers, composio):
        call_ok(mcp_client, "composio_exec", {"tool_slug": "X"}, auth_headers)
        assert composio["exec"] == [{"tool_slug": "X", "arguments": {}}]

    def test_exec_batch_form(self, mcp_client, auth_headers, composio):
        call_ok(mcp_client, "composio_exec", {"tools": [
            {"tool_slug": "A", "arguments": {"x": 1}},
            {"tool_slug": "B"},
        ]}, auth_headers)
        assert composio["exec"] == [
            {"tool_slug": "A", "arguments": {"x": 1}},
            {"tool_slug": "B", "arguments": {}},
        ]

    @pytest.mark.parametrize("arguments,expected", [
        ({}, "requires a tool name"),
        ({"tool_slug": "A", "tools": [{"tool_slug": "B"}]}, "not both"),
        ({"inputs": {"x": 1}, "tools": [{"tool_slug": "B"}]}, "inside tools instead"),
        ({"tools": [{"arguments": {}}]}, 'requires a non-empty "tool_slug"'),
        ({"tools": [{"tool_slug": "A"}] * 51}, "at most 50"),
    ])
    def test_exec_argument_validation(self, mcp_client, auth_headers, composio, arguments, expected):
        assert expected in call_err(mcp_client, "composio_exec", arguments, auth_headers)
        assert "exec" not in composio

    def test_requires_authentication(self, mcp_client, composio):
        message = call_err(mcp_client, "composio_search", {"use_case": "x"})
        assert "No authentication token" in message
        assert composio == {}


class TestAudit:
    def test_tool_calls_are_audited_against_the_caller(self, mcp_client, db, test_user, auth_headers):
        from models.system_audit_log import SystemAuditLog

        call_ok(mcp_client, "getme", headers=auth_headers)

        db.expire_all()
        log = db.query(SystemAuditLog).filter(SystemAuditLog.action == "post /api/v1/mcp").first()
        assert log is not None
        assert log.user_id == test_user.id
        assert log.resource_type == "mcp"
