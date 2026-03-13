---
name: skillhub
description: skillhub 官方基础skill,用于指导如何使用 skillhub cli
---

# SkillHub CLI Tool Usage

DESCRIPTION
    A command-line interface for interacting with SkillHub gateway resources.
    Supports three resource types: third-party APIs, gateway resources, and MCP servers.

USAGE
    skillhub.sh list [search_term]              List all skills or search by name
    skillhub.sh install [skill_name]           Install a skill to local directory
    skillhub.sh [res_type] [res_name] [options] Invoke a resource
    skillhub.sh -h
    skillhub.sh

LIST COMMAND
    skillhub.sh list [search_term]

    Lists all available skills or searches by skill name.
    Outputs: JSON with skill summary (id, name, description, category, tags, etc.)

INSTALL COMMAND
    skillhub.sh install [skill_name]

    Downloads a skill from SkillHub and saves it to ./[skill_name]/SKILL.md

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
    skillhub.sh list

    # Search skills by name
    skillhub.sh list weather
    skillhub.sh list ai -token your-api-token

    # Install a skill
    skillhub.sh install weather-skill
    skillhub.sh install customer-support -token your-api-token

    # Third-party API call
    skillhub.sh third weather-api -method GET -inputs '{"city":"Beijing"}'
    skillhub.sh third user-service -method POST -inputs '{"name":"John","email":"john@example.com"}'

    # Gateway resource call
    skillhub.sh gateway my-api -method GET -path users/123
    skillhub.sh gateway backend-api -method POST -path users -inputs '{"name":"Jane"}'
    skillhub.sh gateway backend-api -method PUT -path users/123 -inputs '{"name":"Jane Updated"}'
    skillhub.sh gateway backend-api -method DELETE -path users/123

    # MCP server call
    skillhub.sh mcp my-mcp-server -mcptool test -inputs '{"name":"weather_tool","arguments":{"location":"Tokyo"}}'
    skillhub.sh mcp my-mcp-server -mcptool tool_name2

    # Using custom token
    skillhub.sh third weather-api -method GET -inputs '{"city":"Shanghai"}' -token your-api-token-here

ENVIRONMENT VARIABLES
    SKILLHUB_API_KEY   Default API token if -token is not provided
    SKILLHUB_URL       Override the default SkillHub URL 

RESOURCE TYPES
    third       Third-party API resources (requires -method)
    gateway     Gateway resources with path support (requires -method and -path)
    mcp         MCP server resources (requires -mcptool)

AUTHENTICATION
    Token priority:
    1. Token provided via -token option
    2. SKILLHUB_API_KEY environment variable
    3. Error if neither is available