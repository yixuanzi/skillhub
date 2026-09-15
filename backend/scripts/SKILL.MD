---
name: skillhub
description: skillhub 官方基础skill,用于指导如何使用 skillhub cli
---

# SkillHub CLI Tool Usage

DESCRIPTION
    A command-line interface for interacting with SkillHub gateway resources.
    Supports three resource types: third-party APIs, gateway resources, and MCP servers,
    plus a dedicated 'composio' command for the built-in Composio integration.

USAGE
    skillhub list [search_term] [-page <number>]             List all skills or search by name
    skillhub install [skill_name]           Install a skill to local directory
    skillhub [res_type] [res_name] [options] Invoke a resource
    skillhub composio [search|schema|exec] [options] Call the composio integration
    skillhub getme                          Get current authenticated user info
    skillhub -h
    skillhub

LIST COMMAND
    skillhub list [search_term]

    Lists all available skills or searches by skill name.
    Outputs: JSON with skill summary (id, name, description, category, tags, etc.)

INSTALL COMMAND
    skillhub install [skill_name]

    Downloads a skill from SkillHub and saves it to ./[skill_name]/SKILL.md

COMPOSIO COMMAND
    skillhub composio search "<search field>"                 Search the Composio tool catalog (COMPOSIO_SEARCH_TOOLS)
    skillhub composio schema "<tool_name>"                    Get a tool's full input schema (COMPOSIO_GET_TOOL_SCHEMAS)
    skillhub composio exec "<tool_name>" --inputs '<json>'    Execute a tool (COMPOSIO_MULTI_EXECUTE_TOOL)

    Calls the single, globally-configured 'composio' resource (type=composio) - there
    can only ever be one such resource in SkillHub. Still requires -token / SKILLHUB_API_KEY
    for SkillHub auth as usual; the Composio account itself (COMPOSIO_API_KEY /
    COMPOSIO_USER_ID) is configured on that resource, not per CLI user.

ARGUMENTS
    res_type        Resource type (required): third, gateway, mcp
    res_name        Resource name (required): name of the resource to call

OPTIONS
    -method <method>    HTTP method: GET, POST, PUT, DELETE (required for third/gateway)
    -path <path>        Resource access path (required for gateway)
    -mcptool <tool>     MCP tool/method name (required for mcp)
    -inputs <json>      JSON string of parameters (optional)
    -token <token>      SkillHub API token (optional, defaults to SKILLHUB_API_KEY env var)
    -timeout <seconds>  Request timeout in seconds (optional, default: 30)
    -v                  Verbose mode: show curl command being executed (optional)

EXAMPLES

    # List all skills
    skillhub list

    # Search skills by name
    skillhub list weather
    skillhub list ai -token your-api-token

    # Install a skill
    skillhub install weather-skill
    skillhub install customer-support -token your-api-token

    # Third-party API call
    skillhub third weather-api -method GET -inputs '{"city":"Beijing"}'
    skillhub third user-service -method POST -inputs '{"name":"John","email":"john@example.com"}'

    # Gateway resource call
    skillhub gateway my-api -method GET -path users/123
    skillhub gateway backend-api -method POST -path users -inputs '{"name":"Jane"}'
    skillhub gateway backend-api -method PUT -path users/123 -inputs '{"name":"Jane Updated"}'
    skillhub gateway backend-api -method DELETE -path users/123

    # MCP server call
    skillhub mcp my-mcp-server -mcptool test -inputs '{"name":"weather_tool","arguments":{"location":"Tokyo"}}'
    skillhub mcp my-mcp-server -mcptool tool_name2

    # Composio meta-tool calls
    skillhub composio search "search Jira issues in project VMS created in the last 5 days"
    skillhub composio schema JIRA_SEARCH_ISSUES
    skillhub composio exec JIRA_SEARCH_ISSUES --inputs '{"project_key":"VMS","created_after":"-5d"}'

    # Using custom token
    skillhub third weather-api -method GET -inputs '{"city":"Shanghai"}' -token your-api-token-here

ENVIRONMENT VARIABLES
    SKILLHUB_API_KEY   Default API token if -token is not provided
    SKILLHUB_URL       Override the default SkillHub URL 

RESOURCE TYPES
    third       Third-party API resources (requires -method)
    gateway     Gateway resources with path support (requires -method and -path)
    mcp         MCP server resources (requires -mcptool)
    composio    Built-in Composio integration, singleton, invoked via 'skillhub composio ...' (see COMPOSIO COMMAND)

AUTHENTICATION
    Token priority:
    1. Token provided via -token option
    2. SKILLHUB_API_KEY environment variable
    3. Error if neither is available