---
name: skillhub
description: skillhub 官方基础skill,用于指导如何使用 skillhub 和 Composio 资源；
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
    skillhub --version                      Print the CLI version and exit
    skillhub

LIST COMMAND
    skillhub list [search_term]

    Lists all available skills or searches by skill name.
    Outputs: JSON with skill summary (id, name, description, category, tags, etc.)

INSTALL COMMAND
    skillhub install [skill_name]

    Downloads a skill from SkillHub and saves it to ./[skill_name]/SKILL.md

COMPOSIO COMMAND
    skillhub composio search "<use case>" [--known-fields '<k:v,...>']   COMPOSIO_SEARCH_TOOLS
    skillhub composio schema <TOOL_SLUG> [TOOL_SLUG ...]                 COMPOSIO_GET_TOOL_SCHEMAS
    skillhub composio exec <TOOL_SLUG> [--inputs '<json object>']        COMPOSIO_MULTI_EXECUTE_TOOL
    skillhub composio exec --tools '<json array>'                        COMPOSIO_MULTI_EXECUTE_TOOL (batch)

    Composio is a catalog of 500+ SaaS integrations (Jira, Slack, GitHub, Gmail,
    Google Workspace, Notion, Linear, ...). You never call those apps directly:
    you discover a tool, read its input schema, then execute it. SkillHub exposes
    exactly these three Composio meta-tools.

    All three go through the single, globally-configured resource of type
    'composio' - SkillHub permits only one such resource to exist. Auth is the
    usual SkillHub auth (-token / SKILLHUB_API_KEY); the Composio account itself
    (COMPOSIO_API_KEY / COMPOSIO_USER_ID) is stored on that resource and shared
    by all callers, so you never pass Composio credentials on the command line.

COMPOSIO WORKFLOW
    Always follow this order. Skipping step 1 does not work: a tool slug is only
    valid if a search returned it - never guess or invent one.

    1. search   Describe the goal in plain English. Returns candidate tool slugs,
                a suggested execution plan, common pitfalls, and each toolkit's
                connection status.
    2. schema   Fetch a tool's full input schema. Often skippable - search
                already embeds input_schema for its primary tools. Do call it
                when search returned a `schemaRef` instead of an `input_schema`,
                or when exec rejected your arguments.
    3. exec     Run the tool with strictly schema-compliant arguments.

    Before exec, check the toolkit's connection status in the search response
    (`toolkit_connection_statuses`). A toolkit that is not ACTIVE cannot be
    executed; it has to be connected in the Composio account first. SkillHub
    does not expose Composio's connection-management meta-tools, so that step
    is done by whoever administers the composio resource, not from this CLI.

    Each of the three CLI calls is independent: SkillHub does not thread
    Composio's workflow-level `session_id` from search into schema/exec. Do not
    rely on server-side state carrying over - pass complete arguments to exec.

COMPOSIO META-TOOL REFERENCE

  1) search -> COMPOSIO_SEARCH_TOOLS
     Search the Composio catalog and return relevant tools plus a suggested
     execution plan for a described task.

     CLI       skillhub composio search "<use case>" [--known-fields '<k:v,...>']
     HTTP      POST /api/v1/gateway/composio/search

     | Parameter      | Required | Type   | Notes                                                   |
     |----------------|----------|--------|---------------------------------------------------------|
     | use_case       | yes      | string | The quoted positional argument. Composio caps it at 1024 chars. |
     | known_fields   | no       | string | CLI: --known-fields (also -known-fields). Omitted when unset. |

     use_case      A normalized English description of one action and its
                   intended outcome. Keep it atomic: one use_case = one tool
                   call. Name the app if it matters ("search issues in jira",
                   "post a message to a slack channel"). Include hidden
                   prerequisites as their own search (e.g. search "get linear
                   issue" before "update linear issue"). Translate non-English
                   prompts. Do NOT put identifiers (names, emails, keys, IDs)
                   in here - they belong in known_fields.
     known_fields  Comma-separated `key:value` hints as a single string, e.g.
                   --known-fields 'project_key:VMS' or
                   --known-fields 'channel_name:general, timezone:Asia/Shanghai'.
                   1-2 short, stable identifiers only - never free-form text
                   such as message bodies or descriptions. Helps the search
                   resolve missing IDs.

     Composio's own optional parameters - `session`, `search_strategy`, `model`
     - are NOT accepted here. SkillHub issues one query per call with defaults.

     Useful fields in the response:
       data.results[0].primary_tool_slugs      -> the slugs to use with schema/exec
       data.results[0].related_tool_slugs      -> prerequisites, alternatives, next steps
       data.results[0].recommended_plan_steps  -> read before executing
       data.results[0].known_pitfalls          -> read before executing
       data.results[0].reasoning               -> why these tools were picked
       data.tool_schemas[SLUG].input_schema    -> full schema, often already present
                                                  so step 2 becomes unnecessary
       data.toolkit_connection_statuses        -> must be ACTIVE before exec

  2) schema -> COMPOSIO_GET_TOOL_SCHEMAS
     Retrieve the complete input schema for one or more tool slugs.

     CLI       skillhub composio schema <TOOL_SLUG> [TOOL_SLUG ...]
     HTTP      POST /api/v1/gateway/composio/schema

     | Parameter   | Required | Type     | Notes                                            |
     |-------------|----------|----------|--------------------------------------------------|
     | tool_slugs  | yes      | string[] | One or more space-separated positional arguments. |

     tool_slugs    Must be slugs returned by a prior search. Never invent one.
                   Request order is preserved. Batch related slugs into one
                   call rather than invoking schema repeatedly.

     Composio's optional `include` (defaults to ["input_schema"]; "output_schema"
     is also available) and `session_id` are NOT exposed - SkillHub always
     requests the default field set.

  3) exec -> COMPOSIO_MULTI_EXECUTE_TOOL
     Execute discovered tools. This is the only one of the three that causes
     side effects in the connected app.

     CLI       skillhub composio exec <TOOL_SLUG> [--inputs '<json object>']   (single)
               skillhub composio exec --tools '<json array>'                  (batch)
     HTTP      POST /api/v1/gateway/composio/exec

     | Parameter         | Required | Type     | Notes                                          |
     |-------------------|----------|----------|------------------------------------------------|
     | tools             | yes      | object[] | 1-50 entries, executed in parallel.            |
     | tools[].tool_slug | yes      | string   | Single form: the positional argument.          |
     | tools[].arguments | no       | object   | Single form: --inputs. Omitted -> `{}`.        |

     --inputs     A JSON **object** holding that tool's own arguments, exactly
                  as its input schema defines them - not a wrapper, and not a
                  JSON array. Match the schema strictly (required fields, enum
                  values, formats, limits); most exec failures are
                  schema-compliance failures, not auth failures.
     --tools      The batch form: a JSON array of
                  {"tool_slug": "...", "arguments": {...}} objects, max 50, run
                  in parallel. `arguments` may be omitted and defaults to `{}`.
                  Mutually exclusive with the positional slug and --inputs.

     Both forms are validated by the CLI before any request is sent: malformed
     JSON, a non-object `--inputs`, a non-array `--tools`, a missing or empty
     `tool_slug`, a non-object `arguments`, or more than 50 entries all fail
     locally with a message naming the offending index.

     Composio's optional `thought`, `current_step`, `current_step_metric`,
     `memory` and `session_id` are NOT exposed. SkillHub always sends
     `sync_response_to_workbench: false` and an empty `memory`, so the full
     response comes back inline rather than being parked in Composio's remote
     workbench.

     Useful fields in the response (results order matches the request order):
       data.error_count                      -> how many entries failed
       data.results[0].tool_slug             -> which tool this entry is for
       data.results[0].error                 -> failure reason, null on success
       data.results[0].response              -> null when that tool failed
       data.results[0].response.successful   -> per-tool success flag
       data.results[0].response.data         -> the payload from the app; its
                                                inner shape varies per tool, so
                                                inspect it rather than assuming

     Note: Composio rejects COMPOSIO_MULTI_EXECUTE_TOOL outside a Tool Router
     session - unlike search and schema, which also work on the direct path.
     That transport-level session is a different thing from the workflow-level
     `session_id` above, and is not something you pass: SkillHub creates and
     caches it per (resource, user), and retries once with a fresh session if a
     cached one has expired. So this is handled for you - but it is why exec is
     slower than search/schema, and why a first exec after idle time can take
     noticeably longer.

COMPOSIO TROUBLESHOOTING
    "Composio error: ..."           HTTP 502 - the call reached Composio and
                                    failed there. The message carries the
                                    underlying cause (TLS, DNS, timeout, or
                                    Composio's own error text).
    403 / permission denied         The composio resource's ACL does not grant
                                    you access, or no composio resource exists.
    Tool slug not found             The slug did not come from a search, or it
                                    was typed from memory. Re-run search.
    Toolkit not ACTIVE              The Composio account has no live connection
                                    for that app. Cannot be fixed from this CLI.
    Argument validation errors      Re-read the schema (step 2) and send exactly
                                    the fields it declares.
    Timeouts                        search does server-side planning and exec
                                    runs inside a session; both are much slower
                                    than a plain proxy call. Raise -timeout.

ARGUMENTS
    res_type        Resource type (required): third, gateway, mcp
    res_name        Resource name (required): name of the resource to call

OPTIONS
    -method <method>    HTTP method: GET, POST, PUT, DELETE (required for third/gateway)
    -path <path>        Resource access path (required for gateway)
    -mcptool <tool>     MCP tool/method name (required for mcp)
    -inputs <json>      JSON string of parameters (optional)
                        For 'composio exec' this is also spelled --inputs
    --known-fields <s>  Identifier hints for 'composio search' (optional)
    --tools <json>      JSON array of tools for 'composio exec' batch form (optional)
    -token <token>      SkillHub API token (optional, defaults to SKILLHUB_API_KEY env var)
    -timeout <seconds>  Request timeout in seconds (optional, default: 30)
    -v                  Verbose mode: show curl command being executed (optional)
    --version           Print the CLI version and exit (also -version).
                        Note: the version flag is --version, not -v - -v is verbose.

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

    # Composio: full three-step workflow
    # 1. discover - note the returned slug and connection status
    skillhub composio search "search issues in jira created recently" --known-fields 'project_key:VMS'
    # 2. read the schema (skip if search already returned input_schema)
    skillhub composio schema JIRA_SEARCH_ISSUES
    # 3. execute with schema-compliant arguments
    skillhub composio exec JIRA_SEARCH_ISSUES --inputs '{"project_key":"VMS","created_after":"-5d","max_results":50}'

    # Composio: several schemas in one call
    skillhub composio schema JIRA_SEARCH_ISSUES SLACK_SEND_MESSAGE

    # Composio: several tools in parallel
    skillhub composio exec --tools '[{"tool_slug":"JIRA_SEARCH_ISSUES","arguments":{"project_key":"VMS"}},
                                     {"tool_slug":"SLACK_SEND_MESSAGE","arguments":{"channel":"general","text":"done"}}]'

    # Composio: exec with no arguments (--inputs omitted -> arguments = {})
    skillhub composio exec SOME_SLUG_RETURNED_BY_SEARCH

    # Composio: slower calls need a bigger timeout
    skillhub composio exec JIRA_SEARCH_ISSUES --inputs '{"project_key":"VMS"}' -timeout 120

    # Using custom token
    skillhub third weather-api -method GET -inputs '{"city":"Shanghai"}' -token your-api-token-here

ENVIRONMENT VARIABLES
    SKILLHUB_API_KEY   Default API token if -token is not provided

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
