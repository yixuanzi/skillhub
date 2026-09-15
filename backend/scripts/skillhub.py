#!/usr/bin/env python3

"""SkillHub CLI Tool (Python version).

This script mirrors backend/scripts/skillhub behavior and CLI contract.
Only Python standard library is used.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple


SKILLHUB_URL = "{PLACEHOLDER_SKILLHUB_URL}"

# Colors for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def error(message: str) -> None:
    print(f"{RED}Error: {message}{NC}", file=sys.stderr)
    sys.exit(1)


def success(message: str) -> None:
    print(f"{GREEN}{message}{NC}")


def warning(message: str) -> None:
    print(f"{YELLOW}Warning: {message}{NC}")


def info(message: str) -> None:
    print(f"{BLUE}{message}{NC}")


def show_help() -> None:
    print(f"{GREEN}SkillHub CLI Tool{NC}\n")
    print(f"{BLUE}DESCRIPTION{NC}")
    print("    A command-line interface for interacting with SkillHub gateway resources.")
    print("    Supports three resource types: third-party APIs, gateway resources, and MCP servers,")
    print("    plus a dedicated 'composio' command for the built-in Composio integration.\n")
    print(f"{BLUE}USAGE{NC}")
    print("    skillhub list [search_term]              List all skills or search by name")
    print("    skillhub install [skill_name]           Install a skill to local directory")
    print("    skillhub getme                          Get current user info")
    print("    skillhub [res_type] [res_name] [options] Invoke a resource")
    print("    skillhub composio [search|schema|exec] [options] Call the composio integration")
    print("    skillhub -h")
    print("    skillhub\n")
    print(f"{BLUE}LIST COMMAND{NC}")
    print("    skillhub list [search_term] [-page <number>]\n")
    print("    Lists all available skills or searches by skill name.")
    print("    Outputs: JSON with skill summary (id, name, description, category, tags, etc.)\n")
    print(f"{BLUE}INSTALL COMMAND{NC}")
    print("    skillhub install [skill_name]\n")
    print("    Downloads a skill from SkillHub and saves it to ./[skill_name]/SKILL.md\n")
    print(f"{BLUE}GETME COMMAND{NC}")
    print("    skillhub getme [-token <token>]\n")
    print("    Returns the current authenticated user's profile information.\n")
    print(f"{BLUE}COMPOSIO COMMAND{NC}")
    print('    skillhub composio search "<search field>"                 Search the Composio tool catalog (COMPOSIO_SEARCH_TOOLS)')
    print('    skillhub composio schema "<tool_name>"                    Get a tool\'s full input schema (COMPOSIO_GET_TOOL_SCHEMAS)')
    print("    skillhub composio exec \"<tool_name>\" --inputs '<json>'    Execute a tool (COMPOSIO_MULTI_EXECUTE_TOOL)\n")
    print("    Calls the single, globally-configured 'composio' resource (type=composio) -")
    print("    there can only ever be one such resource in SkillHub. Still requires -token /")
    print("    SKILLHUB_API_KEY for SkillHub auth as usual; the Composio account itself")
    print("    (COMPOSIO_API_KEY / COMPOSIO_USER_ID) is configured on that resource, not per CLI user.\n")
    print(f"{BLUE}ARGUMENTS{NC}")
    print("    res_type        Resource type (required): third, gateway, mcp")
    print("    res_name        Resource name (required): name of the resource to call\n")
    print(f"{BLUE}OPTIONS{NC}")
    print("    -method <method>    HTTP method: GET, POST, PUT, DELETE (required for third/gateway)")
    print("    -path <path>        Resource access path (required for gateway)")
    print("    -mcptool <tool>     MCP tool/method name (required for mcp)")
    print("    -inputs <json>      JSON string of parameters (optional)")
    print("    -token <token>      SkillHub API token (optional, defaults to SKILLHUB_API_KEY env var)")
    print("    -timeout <seconds>  Request timeout in seconds (optional, default: 30)")
    print("    -page <number>      Page number for list command (optional)")
    print("    -v                  Verbose mode: show curl command being executed (optional)\n")
    print(f"{BLUE}EXAMPLES{NC}\n")
    print(f"    {YELLOW}# List all skills{NC}")
    print("    skillhub list\n")
    print(f"    {YELLOW}# Search skills by name{NC}")
    print("    skillhub list weather")
    print("    skillhub list ai -token your-api-token")
    print("    skillhub list ai -page 2\n")
    print(f"    {YELLOW}# Install a skill{NC}")
    print("    skillhub install weather-skill")
    print("    skillhub install customer-support -token your-api-token\n")
    print(f"    {YELLOW}# Third-party API call{NC}")
    print("    skillhub third weather-api -method GET -inputs '{\"city\":\"Beijing\"}'")
    print("    skillhub third user-service -method POST -inputs '{\"name\":\"John\",\"email\":\"john@example.com\"}'\n")
    print(f"    {YELLOW}# Gateway resource call{NC}")
    print("    skillhub gateway my-api -method GET -path users/123")
    print("    skillhub gateway backend-api -method POST -path users -inputs '{\"name\":\"Jane\"}'")
    print("    skillhub gateway backend-api -method PUT -path users/123 -inputs '{\"name\":\"Jane Updated\"}'")
    print("    skillhub gateway backend-api -method DELETE -path users/123\n")
    print(f"    {YELLOW}# MCP server call{NC}")
    print("    skillhub mcp my-mcp-server -mcptool test -inputs '{\"name\":\"weather_tool\",\"arguments\":{\"location\":\"Tokyo\"}}'")
    print("    skillhub mcp my-mcp-server -mcptool tool_name2\n")
    print(f"    {YELLOW}# Composio meta-tool calls{NC}")
    print('    skillhub composio search "search Jira issues in project VMS created in the last 5 days"')
    print("    skillhub composio schema JIRA_SEARCH_ISSUES")
    print("    skillhub composio exec JIRA_SEARCH_ISSUES --inputs '{\"project_key\":\"VMS\",\"created_after\":\"-5d\"}'\n")
    print(f"    {YELLOW}# Get current user info{NC}")
    print("    skillhub getme")
    print("    skillhub getme -token your-api-token\n")
    print(f"    {YELLOW}# Using custom token{NC}")
    print("    skillhub third weather-api -method GET -inputs '{\"city\":\"Shanghai\"}' -token your-api-token-here\n")
    print(f"{BLUE}ENVIRONMENT VARIABLES{NC}")
    print("    SKILLHUB_API_KEY   Default API token if -token is not provided")
    print("    SKILLHUB_URL       Override the default SkillHub URL \n")
    print(f"{BLUE}RESOURCE TYPES{NC}")
    print("    third       Third-party API resources (requires -method)")
    print("    gateway     Gateway resources with path support (requires -method and -path)")
    print("    mcp         MCP server resources (requires -mcptool)")
    print("    composio    Built-in Composio integration, singleton, invoked via 'skillhub composio ...' (see COMPOSIO COMMAND)\n")
    print(f"{BLUE}AUTHENTICATION{NC}")
    print("    Token priority:")
    print("    1. Token provided via -token option")
    print("    2. SKILLHUB_API_KEY environment variable")
    print("    3. Error if neither is available")


def _parse_timeout(timeout_value: str) -> float:
    try:
        return float(timeout_value)
    except Exception:
        raise RuntimeError(f"Invalid timeout value: {timeout_value}")


def _http_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    timeout_value: str,
    body: Optional[str] = None,
) -> Tuple[int, str]:
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url=url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=_parse_timeout(timeout_value)) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            return resp.getcode(), text
    except urllib.error.HTTPError as e:
        raw = e.read()
        text = raw.decode("utf-8", errors="replace")
        return e.code, text
    except Exception as e:
        raise RuntimeError(str(e))


def json_to_query_params(raw_json: str) -> Optional[str]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON for -inputs: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict):
        print("Error: -inputs must be a JSON object", file=sys.stderr)
        return None

    return urllib.parse.urlencode(data, doseq=True)


def getme_user(token: str, timeout_value: str) -> None:
    if not token:
        token = os.environ.get("SKILLHUB_API_KEY", "")

    if not token:
        error("No authentication token found. Please provide via -token option or set SKILLHUB_API_KEY environment variable")

    api_url = f"{SKILLHUB_URL}/api/v1/auth/me/"

    try:
        _status, response = _http_request(
            method="GET",
            url=api_url,
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout_value=timeout_value,
        )
    except Exception:
        error("Failed to fetch user info from API")

    try:
        parsed = json.loads(response)
        pretty = json.dumps(parsed, indent=4, ensure_ascii=False)
        print(pretty)
    except Exception:
        print(response)


def install_skill(skill_name: str, token: str, timeout_value: str) -> None:
    if not skill_name:
        error("install command requires a skill name")

    if not token:
        token = os.environ.get("SKILLHUB_API_KEY", "")

    info(f"Installing skill: {skill_name}")

    skillhub_home = os.path.join(os.path.expanduser("~"), ".agents", "skills")
    actual_dir = os.path.join(skillhub_home, skill_name)

    if not os.path.isdir(skillhub_home):
        try:
            os.makedirs(skillhub_home, exist_ok=True)
        except Exception:
            error(f"Failed to create directory: {skillhub_home}")

    if os.path.isdir(actual_dir):
        warning(f"Directory {actual_dir} already exists. Overwriting SKILL.md")
    else:
        try:
            os.makedirs(actual_dir, exist_ok=True)
        except Exception:
            error(f"Failed to create directory: {actual_dir}")

    api_url = f"{SKILLHUB_URL}/api/v1/skills/{skill_name}/?install=true"
    info(f"Fetching skill from: {api_url}")

    try:
        status, body = _http_request(
            method="GET",
            url=api_url,
            headers={
                "accept": "text/plain",
                "Authorization": f"Bearer {token}",
            },
            timeout_value=timeout_value,
        )
    except Exception:
        error("Failed to fetch skill from API")

    if str(status) != "200":
        if body:
            error(f"Failed to install skill '{skill_name}' (HTTP {status}): {body}")
        else:
            error(f"Failed to install skill '{skill_name}' (HTTP {status}). Check if the skill exists and you have access.")

    if not body:
        error("Failed to get skill content. Check if skill exists and you have access.")

    target_file = os.path.join(actual_dir, "SKILL.md")
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(body)
    except Exception:
        error(f"Failed to write to {target_file}")

    success("Skill installed successfully:")
    print(f"  Actual: {actual_dir}")


def list_skills(search_term: str, page: str, token: str, timeout_value: str) -> None:
    if not token:
        token = os.environ.get("SKILLHUB_API_KEY", "")

    api_url = f"{SKILLHUB_URL}/api/v1/skills/"
    query_params = ""

    if search_term:
        query_params = f"?search={search_term}"
        info(f"Searching for skills matching: {search_term}")
    else:
        info("Listing all skills")

    if page:
        if query_params:
            query_params = f"{query_params}&page={page}"
        else:
            query_params = f"?page={page}"
        info(f"Page: {page}")

    api_url = f"{api_url}{query_params}"
    info(f"Fetching skills from {api_url}")

    try:
        _status, response = _http_request(
            method="GET",
            url=api_url,
            headers={
                "accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout_value=timeout_value,
        )
    except Exception:
        error("Failed to fetch skills from API")

    if '"detail"' in response:
        error(f"API Error: {response}")

    try:
        parsed = json.loads(response)
        pretty = json.dumps(parsed, indent=4, ensure_ascii=False)
        print(pretty)
    except Exception:
        print(response)


def composio_call(endpoint: str, body: dict, token: str, timeout_value: str, verbose: int) -> None:
    if not token:
        token = os.environ.get("SKILLHUB_API_KEY", "")
    if not token:
        error("No authentication token found. Please provide via -token option or set SKILLHUB_API_KEY environment variable")

    api_url = f"{SKILLHUB_URL}/api/v1/gateway/composio/{endpoint}"
    payload = json.dumps(body)

    if verbose == 1:
        info(
            f"curl --max-time {timeout_value} -sS -L -X 'POST' '{api_url}' "
            f"-H 'Content-Type: application/json' -H 'Authorization: Bearer {token}' -d '{payload}'"
        )

    try:
        _status, resp_body = _http_request(
            method="POST",
            url=api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout_value=timeout_value,
            body=payload,
        )
    except Exception as exc:
        error(str(exc))
        return

    try:
        parsed = json.loads(resp_body)
        print(json.dumps(parsed, indent=4, ensure_ascii=False))
    except Exception:
        print(resp_body)


def normalize_method(method: str) -> str:
    m = method.strip().upper()
    if m not in ("GET", "POST", "PUT", "DELETE"):
        error(f"Invalid method '{method}'. Must be one of: GET, POST, PUT, DELETE")
    return m


def method_to_lower(method: str) -> str:
    if method == "GET":
        return "get"
    if method == "POST":
        return "post"
    if method == "PUT":
        return "put"
    if method == "DELETE":
        return "delete"
    return ""


def main() -> None:
    args = sys.argv[1:]

    res_type = ""
    res_name = ""
    method = ""
    rpath = ""
    mcptool = ""
    inputs = ""
    token = ""
    timeout_value = "30"
    verbose = 0

    if len(args) == 0 or args[0] in ("-h", "--help"):
        show_help()
        sys.exit(0)

    if args[0] == "install":
        rest = args[1:]
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "-token":
                if i + 1 >= len(rest):
                    error("Option -token requires a value")
                token = rest[i + 1]
                i += 2
            elif a == "-timeout":
                if i + 1 >= len(rest):
                    error("Option -timeout requires a value")
                timeout_value = rest[i + 1]
                i += 2
            elif a.startswith("-"):
                error(f"Unknown option for install command: {a}")
            else:
                install_skill(a, token, timeout_value)
                sys.exit(0)
        error("install command requires a skill name")

    if args[0] == "getme":
        rest = args[1:]
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "-token":
                if i + 1 >= len(rest):
                    error("Option -token requires a value")
                token = rest[i + 1]
                i += 2
            elif a == "-timeout":
                if i + 1 >= len(rest):
                    error("Option -timeout requires a value")
                timeout_value = rest[i + 1]
                i += 2
            else:
                error(f"Unknown option for getme command: {a}")
        getme_user(token, timeout_value)
        sys.exit(0)

    if args[0] == "list":
        rest = args[1:]
        search_term = ""
        page = ""
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "-token":
                if i + 1 >= len(rest):
                    error("Option -token requires a value")
                token = rest[i + 1]
                i += 2
            elif a == "-timeout":
                if i + 1 >= len(rest):
                    error("Option -timeout requires a value")
                timeout_value = rest[i + 1]
                i += 2
            elif a == "-page":
                if i + 1 >= len(rest):
                    error("Option -page requires a value")
                if re.fullmatch(r"[0-9]+", rest[i + 1]) is None:
                    error(f"Option -page requires a numeric value, got: {rest[i + 1]}")
                page = rest[i + 1]
                i += 2
            elif a.startswith("-"):
                error(f"Unknown option for list command: {a}")
            else:
                search_term = a
                list_skills(search_term, page, token, timeout_value)
                sys.exit(0)
        list_skills("", page, token, timeout_value)
        sys.exit(0)

    if args[0] == "composio":
        rest = args[1:]
        if len(rest) == 0:
            error("composio command requires a subcommand: search, schema, exec")
        subcmd = rest[0]
        rest = rest[1:]

        arg_value = ""
        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "-token":
                if i + 1 >= len(rest):
                    error("Option -token requires a value")
                token = rest[i + 1]
                i += 2
            elif a == "-timeout":
                if i + 1 >= len(rest):
                    error("Option -timeout requires a value")
                timeout_value = rest[i + 1]
                i += 2
            elif a in ("--inputs", "-inputs"):
                if i + 1 >= len(rest):
                    error("Option --inputs requires a value")
                inputs = rest[i + 1]
                i += 2
            elif a == "-v":
                verbose = 1
                i += 1
            elif a.startswith("-"):
                error(f"Unknown option for composio command: {a}")
            else:
                if arg_value:
                    error(f"Unexpected extra argument for composio command: {a}")
                arg_value = a
                i += 1

        if subcmd == "search":
            if not arg_value:
                error('composio search requires a search field, e.g. skillhub composio search "send an email"')
            composio_call("search", {"use_case": arg_value}, token, timeout_value, verbose)
        elif subcmd == "schema":
            if not arg_value:
                error("composio schema requires a tool name, e.g. skillhub composio schema JIRA_SEARCH_ISSUES")
            composio_call("schema", {"tool_slugs": [arg_value]}, token, timeout_value, verbose)
        elif subcmd == "exec":
            if not arg_value:
                error("composio exec requires a tool name, e.g. skillhub composio exec JIRA_SEARCH_ISSUES --inputs '{...}'")
            if inputs:
                try:
                    arguments = json.loads(inputs)
                except json.JSONDecodeError as exc:
                    error(f"Invalid JSON for --inputs: {exc}")
                    return
                if not isinstance(arguments, dict):
                    error("--inputs must be a JSON object")
                    return
            else:
                arguments = {}
            composio_call(
                "exec",
                {"tools": [{"tool_slug": arg_value, "arguments": arguments}]},
                token, timeout_value, verbose,
            )
        else:
            error(f"Unknown composio subcommand '{subcmd}'. Must be one of: search, schema, exec")
        sys.exit(0)

    res_type = args[0]
    rest = args[1:]

    if res_type not in ("third", "gateway", "mcp"):
        error(f"Invalid res_type '{res_type}'. Must be one of: third, gateway, mcp")

    if len(rest) == 0:
        error("res_name is required")

    res_name = rest[0]
    rest = rest[1:]

    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "-method":
            if i + 1 >= len(rest):
                error("Option -method requires a value")
            method = rest[i + 1]
            i += 2
        elif a == "-path":
            if i + 1 >= len(rest):
                error("Option -path requires a value")
            rpath = rest[i + 1]
            i += 2
        elif a == "-mcptool":
            if i + 1 >= len(rest):
                error("Option -mcptool requires a value")
            mcptool = rest[i + 1]
            i += 2
        elif a == "-inputs":
            if i + 1 >= len(rest):
                error("Option -inputs requires a value")
            inputs = rest[i + 1]
            i += 2
        elif a == "-token":
            if i + 1 >= len(rest):
                error("Option -token requires a value")
            token = rest[i + 1]
            i += 2
        elif a == "-timeout":
            if i + 1 >= len(rest):
                error("Option -timeout requires a value")
            timeout_value = rest[i + 1]
            i += 2
        elif a == "-v":
            verbose = 1
            i += 1
        else:
            error(f"Unknown option: {a}")

    if not token:
        token = os.environ.get("SKILLHUB_API_KEY", "")

    if not token:
        error("No authentication token found. Please provide via -token option or set SKILLHUB_API_KEY environment variable")

    if res_type == "third":
        if not method:
            error("res_type 'third' requires -method option (GET, POST, PUT, DELETE)")
        method = normalize_method(method)
    elif res_type == "gateway":
        if not method:
            error("res_type 'gateway' requires -method option (GET, POST, PUT, DELETE)")
        if not rpath:
            error("res_type 'gateway' requires -path option")
        method = normalize_method(method)
    elif res_type == "mcp":
        if not mcptool:
            error("res_type 'mcp' requires -mcptool option")

    method_lower = method_to_lower(method)

    if res_type == "third":
        url = f"{SKILLHUB_URL}/api/v1/gateway/{res_name}/{method_lower}"
        curl_cmd = f"curl --max-time {timeout_value} -sS -L -X '{method}' '{url}'"
        curl_cmd = f"{curl_cmd} -H 'Content-Type: application/json'"
        curl_cmd = f"{curl_cmd} -H 'Authorization: Bearer {token}'"

        body = None
        if inputs:
            if method in ("GET", "DELETE"):
                query_params = json_to_query_params(inputs)
                if query_params:
                    url = f"{url}?{query_params}"
                    curl_cmd = (
                        f"curl --max-time {timeout_value} -L -X '{method}' '{url}' "
                        f"-H 'Content-Type: application/json' -H 'Authorization: Bearer {token}'"
                    )
            else:
                body = inputs
                curl_cmd = f"{curl_cmd} -d '{inputs}'"

        if verbose == 1:
            info(curl_cmd)

        try:
            _status, resp_body = _http_request(
                method=method,
                url=url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout_value=timeout_value,
                body=body,
            )
            print(resp_body, end="" if resp_body.endswith("\n") else "\n")
        except Exception as exc:
            error(str(exc))

    elif res_type == "gateway":
        clean_path = rpath[1:] if rpath.startswith("/") else rpath
        url = f"{SKILLHUB_URL}/api/v1/gateway/{res_name}/{clean_path}"
        curl_cmd = f"curl --max-time {timeout_value} -sS -L -X '{method}' '{url}'"
        curl_cmd = f"{curl_cmd} -H 'Content-Type: application/json'"
        curl_cmd = f"{curl_cmd} -H 'Authorization: Bearer {token}'"

        body = None
        if inputs:
            if method in ("GET", "DELETE"):
                query_params = json_to_query_params(inputs)
                if query_params:
                    url = f"{url}?{query_params}"
                    curl_cmd = (
                        f"curl --max-time {timeout_value} -L -X '{method}' '{url}' "
                        f"-H 'Content-Type: application/json' -H 'Authorization: Bearer {token}'"
                    )
            else:
                body = inputs
                curl_cmd = f"{curl_cmd} -d '{inputs}'"

        if verbose == 1:
            info(curl_cmd)

        try:
            _status, resp_body = _http_request(
                method=method,
                url=url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout_value=timeout_value,
                body=body,
            )
            print(resp_body, end="" if resp_body.endswith("\n") else "\n")
        except Exception as exc:
            error(str(exc))

    elif res_type == "mcp":
        url = f"{SKILLHUB_URL}/api/v1/gateway/{res_name}/mcp"
        if inputs:
            request_body = f'{{"method": "{mcptool}", "params": {inputs}}}'
        else:
            request_body = f'{{"method": "{mcptool}", "params": {{}}}}'

        curl_cmd = (
            f"curl --max-time {timeout_value} -sS -L -X 'POST' '{url}' "
            f"-H 'Content-Type: application/json' -H 'Authorization: Bearer {token}' -d '{request_body}'"
        )
        if verbose == 1:
            info(curl_cmd)

        try:
            _status, resp_body = _http_request(
                method="POST",
                url=url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout_value=timeout_value,
                body=request_body,
            )
            print(resp_body, end="" if resp_body.endswith("\n") else "\n")
        except Exception as exc:
            error(str(exc))


if __name__ == "__main__":
    main()
