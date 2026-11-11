"""SkillHub MCP server (Streamable HTTP transport).

Exposes the SkillHub CLI (``scripts/skillhub``) as a standard MCP server at
``/api/v1/mcp`` so agents can connect with a plain MCP client instead of
shelling out to the CLI. Every CLI command maps to one tool, with the same
argument names and the same semantics:

    skillhub list [search_term] [-page N]            -> list
    skillhub install <skill_name> [--outdir <path>]  -> install
    skillhub getme                                   -> getme
    skillhub third <res_name> -method .. -inputs ..  -> third
    skillhub gateway <res_name> -method .. -path ..  -> gateway
    skillhub mcp <res_name> -mcptool .. -inputs ..   -> mcp
    skillhub composio search|schema|exec ...         -> composio_search|schema|exec

The tools call the same service layer the REST endpoints use, so the ACL rules,
token-placeholder substitution and visibility rules are identical to a CLI call.

CLI flags with no MCP equivalent:
    -token   -> the connection's ``Authorization: Bearer <token>`` header
    -v       -> not applicable (there is no curl command to echo)

The transport runs stateless with JSON responses: no session affinity is needed
between workers, and nothing is buffered awkwardly by a reverse proxy.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Annotated, Any, AsyncIterator, Optional
from urllib.parse import parse_qsl, urlencode

from fastapi.encoders import jsonable_encoder
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import TextContent, ToolAnnotations
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from core.deps import _authenticate_user
from core.exceptions import ExternalServiceException, ValidationException
from database import SessionLocal
from models.user import User
from schemas.auth import UserResponse
from schemas.skill_list import SkillListListResponse, SkillListSummary
from services.composio_service import ComposioService
from services.gateway_service import GatewayService
from services.mcp_service import MCPService
from services.skill_list_service import SkillListService

logger = logging.getLogger(__name__)

MCP_PATH = "/api/v1/mcp"

# Mirrors the CLI defaults.
DEFAULT_TIMEOUT = 30
DEFAULT_OUTDIR = "~/.agents/skills"
LIST_PAGE_SIZE = 20
COMPOSIO_MAX_TOOLS = 50
HTTP_METHODS = ("GET", "POST", "PUT", "DELETE")

AUTH_REQUIRED_MESSAGE = (
    "No authentication token found. Configure the MCP connection with an "
    "'Authorization: Bearer <SkillHub API key>' header."
)

INSTRUCTIONS = """\
SkillHub exposes skills (SKILL.md documents) and gateway resources.

- `list` / `install`: discover skills and fetch a skill's SKILL.md. `install` returns
  the file content; write it to the path it reports.
- `third`, `gateway`, `mcp`: invoke a SkillHub resource by name. A skill's SKILL.md
  tells you which resource name, method, path and inputs to use.
- `composio_search` -> `composio_schema` -> `composio_exec`: the built-in Composio
  integration. A tool slug is only valid if a search returned it - never invent one.
- `getme`: the user this connection is authenticated as.

Invocation is governed by each resource's ACL rule; a permission error means the
resource owner has not granted this user access.
"""

mcp_server = FastMCP(
    "skillhub",
    instructions=INSTRUCTIONS,
    # FastMCP turns on DNS-rebinding protection (localhost-only Host header)
    # whenever its own bind host is local. It never binds here - SkillHub serves
    # it under its public hostname - so that check would reject every real request.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

Inputs = Annotated[
    Optional[dict[str, Any] | str],
    Field(description="Parameters as a JSON object (a JSON-encoded string is accepted too)."),
]
Timeout = Annotated[
    int,
    Field(ge=1, description="Timeout in seconds for the whole call (CLI -timeout)."),
]

READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
INVOKES_RESOURCE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _extract_token(headers) -> tuple[Optional[str], bool]:
    """Return (token, malformed) from Authorization / X-API-Key headers."""
    authorization = headers.get("authorization")
    if authorization:
        scheme, _, value = authorization.partition(" ")
        value = value.strip()
        if scheme.lower() != "bearer" or not value:
            return None, True
        return value, False
    api_key = (headers.get("x-api-key") or "").strip()
    return (api_key or None), False


@contextlib.contextmanager
def _db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _optional_user(ctx: Context, db: Session) -> Optional[User]:
    """Authenticate the caller of the current tool call, or None if anonymous."""
    request = ctx.request_context.request
    if request is None:
        return None
    token, _ = _extract_token(request.headers)
    if not token:
        return None
    return _authenticate_user(db, token)


def _require_user(ctx: Context, db: Session) -> User:
    user = _optional_user(ctx, db)
    if user is None:
        raise ToolError(AUTH_REQUIRED_MESSAGE)
    return user


def _render(data: Any) -> str:
    """Render a result the way the CLI prints it: text as-is, anything else as JSON."""
    if isinstance(data, str):
        return data
    return json.dumps(jsonable_encoder(data), ensure_ascii=False, indent=2)


def _parse_inputs(inputs: Any, name: str = "inputs") -> Optional[dict[str, Any]]:
    """Accept a JSON object or a JSON-encoded string, as the CLI's -inputs does."""
    if inputs is None or inputs == "":
        return None
    if isinstance(inputs, str):
        try:
            inputs = json.loads(inputs)
        except json.JSONDecodeError as exc:
            raise ToolError(f"invalid JSON for {name}: {exc}")
    if not isinstance(inputs, dict):
        raise ToolError(f"{name} must be a JSON object")
    return inputs


def _normalize_method(method: str) -> str:
    normalized = (method or "").strip().upper()
    if normalized not in HTTP_METHODS:
        raise ToolError(f"Invalid method '{method}'. Must be one of: GET, POST, PUT, DELETE")
    return normalized


def _to_query_params(data: Optional[dict[str, Any]]) -> Optional[dict[str, str]]:
    """Flatten inputs exactly as the CLI's URL-encoding followed by the REST
    handler's ``dict(request.query_params)`` would."""
    if not data:
        return None
    return dict(parse_qsl(urlencode(data, doseq=True), keep_blank_values=True)) or None


async def _with_timeout(awaitable, timeout: int):
    try:
        return await asyncio.wait_for(awaitable, timeout)
    except asyncio.TimeoutError:
        raise ToolError(
            f"Request timed out after {timeout}s. Pass a larger `timeout` if the call is "
            "expected to be slow; it may still have completed upstream."
        )


def _raise_service_error(exc: Exception, upstream: str) -> None:
    """Translate service exceptions the way the REST handlers map them to HTTP codes."""
    message = str(exc)
    if isinstance(exc, ExternalServiceException):
        raise ToolError(f"{upstream} error: {message}")
    if "permission" in message.lower() or "access" in message.lower():
        raise ToolError(f"Permission denied: {message}")
    raise ToolError(message)


async def _call_gateway(
    db: Session,
    user: User,
    res_name: str,
    method: str,
    inputs: Optional[dict[str, Any]],
    path: str,
    timeout: int,
) -> str:
    """Shared by `third` and `gateway`: GET/DELETE send inputs as the query
    string, POST/PUT as the JSON body."""
    if method in ("GET", "DELETE"):
        params, body = _to_query_params(inputs), None
    else:
        params, body = None, inputs

    result = await _with_timeout(
        GatewayService.call_resource(
            db=db,
            resource_name=res_name,
            user=user,
            method=method,
            params=params,
            body=body,
            path=path,
        ),
        timeout,
    )

    if not result["success"]:
        error = result.get("error", "Unknown error")
        error_type = result.get("error_type", "internal_error")
        if error_type == "permission_denied":
            raise ToolError(f"Permission denied: {error}")
        if error_type == "resource_not_found":
            raise ToolError(f"Not found: {error}")
        raise ToolError(error)

    return _render(result["data"])


# --------------------------------------------------------------------------- #
# Tools - one per CLI command
# --------------------------------------------------------------------------- #
@mcp_server.tool(
    name="list",
    title="List skills",
    annotations=READ_ONLY,
    structured_output=False,
)
async def list_skills(
    ctx: Context,
    search_term: Annotated[
        Optional[str], Field(description="Fuzzy match on the skill name. Omit to list everything.")
    ] = None,
    page: Annotated[Optional[int], Field(ge=1, description="Page number, starting at 1.")] = None,
) -> str:
    """List available skills, or search them by name (CLI: `skillhub list [search_term] [-page N]`).

    Returns JSON `{items, total, page, size}`; each item is a skill summary (id, name,
    description, category, tags, version, ...) without the SKILL.md body - use
    `install` to fetch that. Without authentication only `public` skills are listed.
    """
    page = page or 1
    with _db_session() as db:
        user = _optional_user(ctx, db)
        # Same visibility rules as GET /api/v1/skills/ with no explicit tags
        # filter: anonymous callers see public skills only; authenticated
        # callers get the published-or-own union.
        skills, total = SkillListService.list_with_filters(
            db,
            (page - 1) * LIST_PAGE_SIZE,
            LIST_PAGE_SIZE,
            None,
            "public" if user is None else None,
            None,
            search_term or None,
            current_user=user,
            apply_visibility=True,
            apply_tag_filter=user is None,
        )
        response = SkillListListResponse(
            items=[SkillListSummary.model_validate(s) for s in skills],
            total=total,
            page=page,
            size=LIST_PAGE_SIZE,
        )
        return _render(response)


@mcp_server.tool(
    name="install",
    title="Install a skill",
    annotations=READ_ONLY,
    structured_output=False,
)
async def install_skill(
    ctx: Context,
    skill_name: Annotated[str, Field(min_length=1, description="Skill name (or id) as shown by `list`.")],
    outdir: Annotated[
        Optional[str],
        Field(description=f"Install directory on your machine. Defaults to {DEFAULT_OUTDIR}."),
    ] = None,
) -> list[TextContent]:
    """Fetch a skill's SKILL.md so you can install it locally
    (CLI: `skillhub install <skill_name> [--outdir <path>]`).

    The server cannot write to your filesystem. It returns two text blocks: the
    target path `<outdir>/<skill_name>/SKILL.md`, then the exact file content.
    Create the directory if needed and write the content there unchanged,
    overwriting any existing SKILL.md.
    """
    with _db_session() as db:
        user = _optional_user(ctx, db)
        if len(skill_name) == 36:
            skill = SkillListService.get_by_id(db, skill_name)
        else:
            skill = SkillListService.get_by_name(db, skill_name)

        if not skill:
            raise ToolError(f"Skill with id/name '{skill_name}' not found")
        if user is None and (not skill.tags or "public" not in skill.tags):
            raise ToolError(
                "Skill not found or access denied. Public skills only for unauthenticated users."
            )
        content = skill.content or ""

    if not content:
        raise ToolError("Failed to get skill content. Check if skill exists and you have access.")

    target = f"{(outdir or DEFAULT_OUTDIR).rstrip('/')}/{skill_name}/SKILL.md"
    return [
        TextContent(
            type="text",
            text=(
                f"Write the next block, unchanged, to {target} "
                "(create the directory if missing; overwrite an existing SKILL.md)."
            ),
        ),
        TextContent(type="text", text=content),
    ]


@mcp_server.tool(
    name="getme",
    title="Get current user",
    annotations=READ_ONLY,
    structured_output=False,
)
async def getme(ctx: Context) -> str:
    """Return the profile of the user this connection is authenticated as
    (CLI: `skillhub getme`): id, username, email, roles and permissions."""
    with _db_session() as db:
        user = _require_user(ctx, db)
        return _render(UserResponse.model_validate(user))


@mcp_server.tool(
    name="third",
    title="Call a third-party API resource",
    annotations=INVOKES_RESOURCE,
    structured_output=False,
)
async def call_third(
    ctx: Context,
    res_name: Annotated[str, Field(min_length=1, description="Name of the resource to call.")],
    method: Annotated[str, Field(description="HTTP method: GET, POST, PUT or DELETE.")],
    inputs: Inputs = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """Call a third-party API resource
    (CLI: `skillhub third <res_name> -method <METHOD> [-inputs '<json>']`).

    `inputs` is sent as the query string for GET/DELETE and as the JSON body for
    POST/PUT. Returns the upstream response body.
    """
    method = _normalize_method(method)
    data = _parse_inputs(inputs)
    # The CLI hits /gateway/<name>/<method>; only /get and /post are dedicated
    # routes, so PUT/DELETE reach the generic path route with the method as path.
    path = "" if method in ("GET", "POST") else method.lower()
    with _db_session() as db:
        user = _require_user(ctx, db)
        return await _call_gateway(db, user, res_name, method, data, path, timeout)


@mcp_server.tool(
    name="gateway",
    title="Call a gateway resource",
    annotations=INVOKES_RESOURCE,
    structured_output=False,
)
async def call_gateway(
    ctx: Context,
    res_name: Annotated[str, Field(min_length=1, description="Name of the resource to call.")],
    method: Annotated[str, Field(description="HTTP method: GET, POST, PUT or DELETE.")],
    path: Annotated[
        str,
        Field(min_length=1, description="Path appended to the resource's base URL, e.g. `users/123`."),
    ],
    inputs: Inputs = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """Call a gateway resource at a sub-path
    (CLI: `skillhub gateway <res_name> -method <METHOD> -path <path> [-inputs '<json>']`).

    `inputs` is sent as the query string for GET/DELETE and as the JSON body for
    POST/PUT. Returns the upstream response body.

    For an MCP-type resource, method `GET` with path `mcp/tools` lists the tool
    names that the `mcp` tool can call on it.
    """
    method = _normalize_method(method)
    data = _parse_inputs(inputs)
    clean_path = path[1:] if path.startswith("/") else path
    if not clean_path:
        raise ToolError("res_type 'gateway' requires a non-empty path")

    with _db_session() as db:
        user = _require_user(ctx, db)

        # GET /gateway/<name>/mcp/tools is a dedicated REST route, not a proxied path.
        if method == "GET" and clean_path == "mcp/tools":
            try:
                tools = await _with_timeout(
                    MCPService.list_tools(db=db, resource_name=res_name, user=user), timeout
                )
            except (ValidationException, ExternalServiceException) as exc:
                _raise_service_error(exc, "MCP server")
            return _render({"tools": tools})

        return await _call_gateway(db, user, res_name, method, data, clean_path, timeout)


@mcp_server.tool(
    name="mcp",
    title="Call an MCP server resource",
    annotations=INVOKES_RESOURCE,
    structured_output=False,
)
async def call_mcp(
    ctx: Context,
    res_name: Annotated[str, Field(min_length=1, description="Name of the MCP-type resource.")],
    mcptool: Annotated[
        str, Field(min_length=1, description="Name of the tool to call on that MCP server.")
    ],
    inputs: Inputs = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """Call a tool on an MCP server registered in SkillHub
    (CLI: `skillhub mcp <res_name> -mcptool <tool> [-inputs '<json>']`).

    `inputs` holds that tool's own arguments. To discover tool names, call
    `gateway` with method `GET` and path `mcp/tools` on the same resource.
    """
    params = _parse_inputs(inputs) or {}
    with _db_session() as db:
        user = _require_user(ctx, db)
        try:
            result = await _with_timeout(
                MCPService.call_mcp_resource(
                    db=db, resource_name=res_name, method=mcptool, params=params, user=user
                ),
                timeout,
            )
        except (ValidationException, ExternalServiceException) as exc:
            _raise_service_error(exc, "MCP server")
        return _render(result)


@mcp_server.tool(
    name="composio_search",
    title="Composio: search tools",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    structured_output=False,
)
async def composio_search(
    ctx: Context,
    use_case: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "One action and its outcome in plain English, e.g. 'search issues in jira'. "
                "No identifiers here - put those in known_fields."
            ),
        ),
    ],
    known_fields: Annotated[
        Optional[str],
        Field(description="Comma-separated key:value identifier hints, e.g. 'project_key:VMS'."),
    ] = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """COMPOSIO_SEARCH_TOOLS - find Composio tools for a task
    (CLI: `skillhub composio search "<use case>" [--known-fields '<k:v,...>']`).

    Step 1 of search -> schema -> exec. Returns candidate tool slugs, a suggested
    plan, known pitfalls and each toolkit's connection status (must be ACTIVE
    before exec). The response often already embeds each tool's input_schema, in
    which case the schema step can be skipped.
    """
    with _db_session() as db:
        user = _require_user(ctx, db)
        try:
            result = await _with_timeout(
                ComposioService.search_tools(
                    db=db, user=user, use_case=use_case, known_fields=known_fields or None
                ),
                timeout,
            )
        except (ValidationException, ExternalServiceException) as exc:
            _raise_service_error(exc, "Composio")
        return _render(result)


@mcp_server.tool(
    name="composio_schema",
    title="Composio: get tool schemas",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    structured_output=False,
)
async def composio_schema(
    ctx: Context,
    tool_slugs: Annotated[
        list[str],
        Field(min_length=1, description="Tool slugs returned by a prior composio_search."),
    ],
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """COMPOSIO_GET_TOOL_SCHEMAS - fetch the full input schema for tool slugs
    (CLI: `skillhub composio schema <TOOL_SLUG> [TOOL_SLUG ...]`).

    Only pass slugs a search returned. Batch related slugs into one call.
    """
    slugs = [slug for slug in tool_slugs if slug]
    if not slugs:
        raise ToolError("composio schema requires at least one tool name")
    with _db_session() as db:
        user = _require_user(ctx, db)
        try:
            result = await _with_timeout(
                ComposioService.get_tool_schemas(db=db, user=user, tool_slugs=slugs), timeout
            )
        except (ValidationException, ExternalServiceException) as exc:
            _raise_service_error(exc, "Composio")
        return _render(result)


def _normalize_composio_tools(tools: Any) -> list[dict[str, Any]]:
    """Validate the batch form exactly as the CLI's --tools does."""
    if isinstance(tools, str):
        try:
            tools = json.loads(tools)
        except json.JSONDecodeError as exc:
            raise ToolError(f"invalid JSON for tools: {exc}")
    if not isinstance(tools, list) or not tools:
        raise ToolError(
            'tools must be a non-empty JSON array, e.g. [{"tool_slug":"X","arguments":{}}]'
        )
    if len(tools) > COMPOSIO_MAX_TOOLS:
        raise ToolError(f"tools accepts at most {COMPOSIO_MAX_TOOLS} entries, got {len(tools)}")

    normalized = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ToolError(f"tools[{index}] must be a JSON object")
        slug = tool.get("tool_slug")
        if not isinstance(slug, str) or not slug:
            raise ToolError(f'tools[{index}] requires a non-empty "tool_slug"')
        arguments = tool.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ToolError(f"tools[{index}].arguments must be a JSON object")
        normalized.append({"tool_slug": slug, "arguments": arguments})
    return normalized


@mcp_server.tool(
    name="composio_exec",
    title="Composio: execute tools",
    annotations=INVOKES_RESOURCE,
    structured_output=False,
)
async def composio_exec(
    ctx: Context,
    tool_slug: Annotated[
        Optional[str],
        Field(description="Single form: the tool slug to execute (from a prior composio_search)."),
    ] = None,
    inputs: Annotated[
        Optional[dict[str, Any] | str],
        Field(description="Single form: that tool's own arguments as a JSON object. Omitted -> {}."),
    ] = None,
    tools: Annotated[
        Optional[list[dict[str, Any]] | str],
        Field(
            description=(
                'Batch form: array of {"tool_slug": "...", "arguments": {...}} (max 50), run in '
                "parallel. Mutually exclusive with tool_slug and inputs."
            )
        ),
    ] = None,
    timeout: Timeout = DEFAULT_TIMEOUT,
) -> str:
    """COMPOSIO_MULTI_EXECUTE_TOOL - run one or more discovered Composio tools
    (CLI: `skillhub composio exec <TOOL_SLUG> [--inputs '<json>']` or
    `skillhub composio exec --tools '<json array>'`).

    The only Composio step with side effects in the connected app. Pass either
    `tool_slug` (+ optional `inputs`) or `tools`, never both. Arguments must
    follow the tool's input schema exactly.
    """
    if tools is not None and tools != "":
        if tool_slug:
            raise ToolError("composio exec takes either a tool name or tools, not both")
        if inputs not in (None, ""):
            raise ToolError("inputs applies to a single tool name; put arguments inside tools instead")
        normalized = _normalize_composio_tools(tools)
    else:
        if not tool_slug:
            raise ToolError("composio exec requires a tool name (tool_slug) or tools")
        normalized = [
            {"tool_slug": tool_slug, "arguments": _parse_inputs(inputs) or {}}
        ]

    with _db_session() as db:
        user = _require_user(ctx, db)
        try:
            result = await _with_timeout(
                ComposioService.multi_execute_tool(db=db, user=user, tools=normalized), timeout
            )
        except (ValidationException, ExternalServiceException) as exc:
            _raise_service_error(exc, "Composio")
        return _render(result)


# --------------------------------------------------------------------------- #
# ASGI endpoint
# --------------------------------------------------------------------------- #
def _jsonrpc_error(status_code: int, message: str, headers: Optional[dict[str, str]] = None) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": message}},
        status_code=status_code,
        headers=headers,
    )


class SkillHubMCPApp:
    """ASGI app serving the MCP Streamable HTTP endpoint.

    Auth mirrors the CLI: a missing token connects anonymously (only `list` and
    `install` of public skills work), while a token that is present but invalid
    is rejected up front with 401 so a misconfigured key fails at connect time
    instead of on the first tool call.
    """

    def __init__(self) -> None:
        self._manager: Optional[StreamableHTTPSessionManager] = None

    @contextlib.asynccontextmanager
    async def run(self) -> AsyncIterator[None]:
        """Run the session manager; enter this from the application lifespan.

        A manager instance cannot be restarted, so each lifespan gets its own.
        """
        manager = StreamableHTTPSessionManager(
            app=mcp_server._mcp_server,
            json_response=True,
            stateless=True,
        )
        async with manager.run():
            self._manager = manager
            try:
                yield
            finally:
                self._manager = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)

        # Stateless server: there is no server-initiated stream to open (GET)
        # and no session to terminate (DELETE). 405 is the spec's answer to both.
        if request.method != "POST":
            response = _jsonrpc_error(405, "Method not allowed", {"Allow": "POST"})
            await response(scope, receive, send)
            return

        token, malformed = _extract_token(request.headers)
        if token:
            with _db_session() as db:
                authenticated = _authenticate_user(db, token) is not None
        else:
            authenticated = not malformed
        if not authenticated:
            response = _jsonrpc_error(
                401, "Invalid authentication credentials", {"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return

        manager = self._manager
        if manager is None:
            response = _jsonrpc_error(503, "MCP server is not running")
            await response(scope, receive, send)
            return

        await manager.handle_request(scope, receive, send)


skillhub_mcp_app = SkillHubMCPApp()
