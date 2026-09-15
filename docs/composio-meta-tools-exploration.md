# Composio 元工具(Meta Tools)参数与 Schema 探索报告

> 调研日期:2026-09-15
> 参考资料:[[Composio-深度调研]](/Users/guisheng.guo/wiki/02-Wiki/AIAgent/Composio-深度调研.md)
> 使用的凭证:`backend/.env` 中配置的 `COMPOSIO_API_KEY` / `COMPOSIO_USER_ID`(本文档不记录任何实际密钥值)
> 探索对象:Composio Session 模式下暴露给 Agent 的 7 个 meta tools —— `COMPOSIO_SEARCH_TOOLS`、`COMPOSIO_GET_TOOL_SCHEMAS`、`COMPOSIO_MULTI_EXECUTE_TOOL`、`COMPOSIO_MANAGE_CONNECTIONS`、`COMPOSIO_WAIT_FOR_CONNECTIONS`、`COMPOSIO_REMOTE_WORKBENCH`、`COMPOSIO_REMOTE_BASH_TOOL`

## 1. 结论先行(TL;DR)

> **更新(换 key 之后)**:`backend/.env` 里的 `COMPOSIO_API_KEY` 已经换成一把有权限的 key,`session.execute` 和直连 `tools.execute` 都已经跑通并拿到了真实执行结果,完整过程见 **第 12 节**。以下 1-3 条是**换 key 之前**用受限 key 排查权限问题时的记录,保留作为过程记录。

1. **7 个元工具的完整输入/输出 JSON Schema 已经全部拿到**(见第 3 节起各小节),数据来源是 Composio 官方工具目录接口 `GET /api/v3.1/tools/{tool_slug}`,和 SDK 内部 `session.tools()` / 官方文档描述的 schema 是同一套数据源,权威、完整,不是靠试错猜出来的。
2. **`session.execute(...)` 没能真正跑通**——不是工具本身的问题,是**当时 `backend/.env` 里配置的 `COMPOSIO_API_KEY` 权限不够**:
   - 它是一个 **Scoped Project Key**,`session_management` 只给了**读**权限,没有**写**权限 → 调用 `composio.sessions.create(user_id=...)` 直接 403(创建 session 属于写操作)。
   - 退而求其次,绕开 session、直接用 `composio.tools.execute(tool_slug, user_id=..., arguments=...)` 也不行——这个 key 对 `tool_execution` **完全没有权限**(不是权限不够,是根本没给),对 `COMPOSIO_SEARCH_TOOLS`、`COMPOSIO_GET_TOOL_SCHEMAS`、`COMPOSIO_MANAGE_CONNECTIONS`、`COMPOSIO_REMOTE_BASH_TOOL` 四个工具分别验证过,报错完全一致(见第 2.3 节)。
   - 唯一能正常访问的是**只读的工具目录接口**(`GET /tools`、`GET /tools/{slug}`、`GET /tools/enum`),本文档的全部 schema 数据就是从这里拿到的。
3. ~~如果要真正跑通执行链路,需要去 Composio Dashboard 给这个 key 补上 `session_management:write` + `tool_execution:write` 权限~~ —— **已完成**,见第 12 节。

## 2. 方法与环境记录

### 2.1 为什么不能直接跑 `backend/.venv`

`backend/requirements.txt` 目前没有 `composio` 这个包(`.venv/bin/pip show composio` 确认未安装),仓库里也没有任何现有 Composio 集成代码。为了不污染项目的正式依赖,这次探索是在 `/tmp` 下新建了一个**隔离的一次性 venv**,`pip install composio`(拿到的是 0.21.1 版),只为了这次调研使用,**没有改动 `backend/requirements.txt` 或 `backend/.venv`**。

### 2.2 一个环境障碍:企业网络的 TLS 检查代理

第一次调用 `composio.sessions.create(...)` 时报 `SSL: CERTIFICATE_VERIFY_FAILED`。排查发现 `backend.composio.dev` 的证书链会经过公司的 **Zscaler TLS 检查代理**重签(`curl -v` 显示证书 `subject: CN=composio.dev; O=Zscaler Inc.`)。系统 `curl`/浏览器信任这张证书是因为 macOS 系统 Keychain 里有对应的 Zscaler Root CA(企业 MDM 下发),但 Python 的 `certifi` 证书包里没有。解决方式:用 `security find-certificate -a -c "Zscaler" -p /Library/Keychains/System.keychain` 从系统 Keychain 导出 Zscaler Root CA,追加进这个一次性 venv 的 `certifi/cacert.pem`。这个改动只影响临时 venv,不影响项目本身。

*(如果以后要在 `backend` 服务里正式集成 Composio,这个证书问题在生产环境不一定存在——取决于服务器出网是否也经过同样的 TLS 检查代理;本地开发机上如果遇到同样报错,可以参考这个解法。)*

### 2.3 权限验证:实际请求与响应

**Session 路径**(wiki 文档路径 A):

```python
from composio import Composio
composio = Composio(api_key=COMPOSIO_API_KEY)
session = composio.sessions.create(user_id=COMPOSIO_USER_ID)  # <-- 这一步就 403
```
```json
{
  "error": {
    "message": "This API key does not have the permissions required for POST /api/v3.1/tool_router/session. This route requires \"session_management\" write access, but the key has read access for \"session_management\".",
    "code": 812,
    "slug": "APIKey_InsufficientPermissions",
    "status": 403,
    "suggested_fix": "Grant the \"session_management\" permission with at least \"write\" access to this API key, or use a key that already has it."
  }
}
```

**直连路径**(wiki 文档路径 B,绕开 session):

```python
composio.tools.execute(
    "COMPOSIO_SEARCH_TOOLS",
    user_id=COMPOSIO_USER_ID,
    arguments={"queries": [{"use_case": "send an email"}]},
    dangerously_skip_version_check=True,  # 这几个 meta tool 版本号是 00000000_00,仍需显式传
)
```
第一次没传 `dangerously_skip_version_check` 时报 `ToolVersionRequiredError`(符合 wiki 里"直连执行必须显式指定 toolkit 版本"的提示);加上之后变成:
```json
{
  "error": {
    "message": "This API key does not have the permissions required for POST /api/v3.1/tools/execute/COMPOSIO_SEARCH_TOOLS. This route requires \"tool_execution\" write access, but the key has no access for \"tool_execution\".",
    "code": 812,
    "slug": "APIKey_InsufficientPermissions",
    "status": 403
  }
}
```
换成 `COMPOSIO_GET_TOOL_SCHEMAS`、`COMPOSIO_MANAGE_CONNECTIONS`、`COMPOSIO_REMOTE_BASH_TOOL` 分别重试,报错一模一样(只有 slug 名字不同),说明这是**账号级别的权限桶**(`tool_execution`),不是某个工具单独被禁用。

**只读目录接口**(正常):

```bash
curl https://backend.composio.dev/api/v3.1/tools/COMPOSIO_SEARCH_TOOLS -H "x-api-key: $COMPOSIO_API_KEY"
# -> 200,返回完整 schema(见下文各节)
```

## 3. `COMPOSIO_SEARCH_TOOLS`

**一句话**(来自本次任务需求描述):Search the Composio catalog and return relevant tools for a user request, along with a suggested execution plan.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Search Composio Tools |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | important, openWorldHint, readOnlyHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_SEARCH_TOOLS`)**

> Tool Server Info: Composio connects 500+ apps—Slack, GitHub, Notion, Google Workspace (Gmail, Sheets, Drive, Calendar), Microsoft (Outlook, Teams), X/Twitter, Figma, Web Search / Deep research, Browser tool (scrape URLs, browser automation), Meta apps (Instagram, Meta Ads), TikTok, and more—for seamless cross-app automation.
>   Use this tool to discover relevant tools plus the recommended plan and common pitfalls for reliable execution.
>   Always call this tool first whenever a user mentions or implies an external app, service, or workflow—never say "I don't have access to X/Y app" before calling it.
> 
> Usage guidelines:
>   - Use this tool whenever kicking off a task. Re-run it when you need additional tools/plans due to missing details, errors, or a changed use case.
>   - Use search_strategy: "auto" normally. If the returned plan does not match the current request or an expected tool is missing, retry the same queries with search_strategy: "tool_search" to bypass cached plans and run direct tool search.
>   - If the user pivots to a different use case in same chat, you MUST call this tool again with the new use case and generate a new session_id.
>   - Specify the use_case with a normalized description of the problem, query, or task. Be clear and precise. Queries can be simple single-app actions or multiple linked queries for complex cross-app workflows.
>   - Pass known_fields along with use_case as a string of key–value hints (for example, "channel_name: general") to help the search resolve missing details such as IDs.
>   
> 
> Splitting guidelines (Important):
>   1. Atomic queries: 1 query = 1 tool call. Include hidden prerequisites (e.g., add "get Linear issue" before "update Linear issue").
>   2. Include app names: If user names a toolkit, include it in every sub query so intent stays scoped (e.g., "fetch Gmail emails", "reply to Gmail email").
>   3. English input: Translate non-English prompts while preserving intent and identifiers.
> 
>   Example:
>   User query: "send an email to John welcoming him and create a meeting invite for tomorrow"
>   Search call: queries: [
>     {use_case: "send an email to someone", known_fields: "recipient_name: John"},
>     {use_case: "create a meeting invite", known_fields: "meeting_date: tomorrow"}
>   ]
> 
> Plan review checklist (Important):
>   - The response includes a detailed execution plan and common pitfalls. You MUST review this plan carefully, adapt it to your current context, and generate your own final step-by-step plan before execution. Execute the steps in order to ensure reliable and accurate execution. Skipping or ignoring required steps can lead to unexpected failures.
>   - Check the plan and pitfalls for input parameter nuances (required fields, IDs, formats, limits). Before executing any tool, you MUST review its COMPLETE input schema and provide STRICTLY schema-compliant arguments to avoid invalid-input errors.
>   - Determine whether pagination is needed; if a response returns a pagination token and completeness is implied, paginate until exhaustion and do not return partial results.
> 
> Response:
>   - Tools & Input Schemas: The response lists toolkits (apps) and tools suitable for the task, along with their tool_slug, description, input schema / schemaRef, and related tools for prerequisites, alternatives, or next steps.
>     - NOTE: Tools with schemaRef instead of input_schema require you to call COMPOSIO_GET_TOOL_SCHEMAS first to load their full input_schema before use.
>   - Connection Info: If a toolkit has an active connection, the response includes it along with any available current user information. If no active connection exists, you MUST initiate a new connection via COMPOSIO_MANAGE_CONNECTIONS with the correct toolkit name. DO NOT execute any toolkit tool without an ACTIVE connection.
>   - Time Info: The response includes the current UTC time for reference. You can reference UTC time from the response if needed.
>   
>   - The tools returned to you through this are to be called via COMPOSIO_MULTI_EXECUTE_TOOL. Ensure each tool execution specifies the correct tool_slug and arguments exactly as defined by the tool's input schema.
>     - The response includes a memory parameter containing relevant information about the use case and the known fields that can be used to determine the flow of execution. Any user preferences in memory must be adhered to.
> 
> SESSION: ALWAYS set this parameter, first for any workflow. Pass session: {generate_id: true} for new workflows OR session: {id: "EXISTING_ID"} to continue. ALWAYS use the returned session_id in ALL subsequent meta tool calls.

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `queries` | ✅ | `array` | Structured English search queries to process in parallel. Split independent app/API actions into separate queries, including hidden prerequisites. Each query... |
| `session` |  | `object` | Session context for correlating meta tool calls within a workflow. Always pass this parameter. Use {generate_id: true} for new workflows or {id: "EXISTING_ID... |
| `model` |  | `string` | Client LLM model name (recommended). Used to optimize planning/search behavior. Ignored if omitted or invalid. |
| `search_strategy` |  | `string` | Search path to use. Use auto normally. If the returned plan does not match the current request or an expected tool is missing, retry with tool_search to bypa... |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "queries": {
      "type": "array",
      "description": "Structured English search queries to process in parallel. Split independent app/API actions into separate queries, including hidden prerequisites. Each query returns 4-6 tools.",
      "items": {
        "type": "object",
        "properties": {
          "use_case": {
            "description": "Provide a normalized English description of the complete use case to enable precise planning. Focus on the specific action and intended outcome. Include any specific apps if mentioned by user in each use_case. Do NOT include personal identifiers (names, emails, IDs) here — put those in known_fields.",
            "examples": [
              "send an email to someone",
              "search issues with label in jira toolkit",
              "put issue details in a google sheet",
              "post a formatted message to slack channel"
            ],
            "title": "Use Case",
            "type": "string",
            "maxLength": 1024
          },
          "known_fields": {
            "type": "string",
            "description": "Provide known workflow inputs as a single English string of comma-separated key:value pairs (not an array). Keep 1-2 short, structured items - stable identifiers, names, emails, or settings only. Omit if not relevant. No free-form or long text (messages, notes, descriptions).",
            "examples": [
              "channel_name:pod-sdk",
              "channel_id:123",
              "invitee_names:John,Maria, timezone:Asia/Kolkata"
            ]
          }
        },
        "required": [
          "use_case"
        ]
      },
      "minItems": 1,
      "title": "Queries"
    },
    "session": {
      "type": "object",
      "description": "Session context for correlating meta tool calls within a workflow. Always pass this parameter. Use {generate_id: true} for new workflows or {id: \"EXISTING_ID\"} to continue existing workflows.",
      "properties": {
        "id": {
          "type": "string",
          "description": "Existing session identifier for the current workflow to reuse across calls.",
          "title": "Session ID"
        },
        "generate_id": {
          "type": "boolean",
          "description": "Set to true for the first search call of a new usecase/workflow to generate a new session ID. When user pivots to a different task, set this true. If omitted or false with an existing session.id, the provided session ID will be reused.",
          "title": "Generate ID"
        }
      }
    },
    "model": {
      "type": "string",
      "description": "Client LLM model name (recommended). Used to optimize planning/search behavior. Ignored if omitted or invalid.",
      "examples": [
        "gpt-5.2",
        "claude-4.5-sonnet"
      ],
      "title": "Model"
    },
    "search_strategy": {
      "type": "string",
      "enum": [
        "auto",
        "tool_search"
      ],
      "default": "auto",
      "description": "Search path to use. Use auto normally. If the returned plan does not match the current request or an expected tool is missing, retry with tool_search to bypass cached plans and run direct tool search.",
      "title": "Search Strategy"
    }
  },
  "required": [
    "queries"
  ],
  "title": "SearchToolsRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "results": {
          "type": "array",
          "description": "Per-query search results with tools, reasoning, and memory. One entry per query in request order.",
          "items": {
            "type": "object",
            "properties": {
              "index": {
                "type": "integer",
                "description": "1-based index of the query in the request"
              },
              "use_case": {
                "type": "string",
                "description": "The use case that was searched"
              },
              "primary_tool_slugs": {
                "type": "array",
                "description": "List of main tool slugs matching the search criteria",
                "items": {
                  "type": "string"
                }
              },
              "related_tool_slugs": {
                "type": "array",
                "description": "List of related tool slugs that might be useful",
                "items": {
                  "type": "string"
                }
              },
              "toolkits": {
                "type": "array",
                "description": "List of unique toolkit slugs used by tools in this query",
                "items": {
                  "type": "string"
                }
              },
              "reasoning": {
                "type": "string",
                "description": "Reasoning for the search results"
              },
              "task_difficulty": {
                "type": "string",
                "description": "Assessment of task difficulty for this specific query"
              },
              "recommended_plan_steps": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Workflow steps from cached plan (only present when cached plan is available)"
              },
              "known_pitfalls": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Common pitfalls and considerations (only present when cached plan is available)"
              },
              "reference_workbench_snippets": {
                "type": "array",
                "description": "Reference Python code snippets for processing tool responses in the workbench (only present when cached plan is available)",
                "items": {
                  "type": "object",
                  "properties": {
                    "description": {
                      "type": "string",
                      "description": "Description of what the code snippet does"
                    },
                    "code": {
                      "type": "string",
                      "description": "Python code snippet for the workbench, wrapped in triple backticks"
                    }
                  },
                  "required": [
                    "description",
                    "code"
                  ]
                }
              },
              "memory": {
                "type": "object",
                "description": "Memory data relevant to this query, grouped by app",
                "additionalProperties": {
                  "type": "array"
                }
              },
              "error": {
                "type": "string",
                "nullable": true,
                "description": "Error message if the search failed, null otherwise"
              }
            },
            "required": [
              "index",
              "use_case",
              "primary_tool_slugs",
              "related_tool_slugs",
              "toolkits",
              "reasoning",
              "task_difficulty"
            ]
          }
        },
        "tool_schemas": {
          "type": "object",
          "description": "Deduplicated tool definitions keyed by tool_slug for O(1) lookup. Each tool appears once even if used in multiple queries.",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "tool_slug": {
                "type": "string",
                "description": "The slug of the tool"
              },
              "toolkit": {
                "type": "string",
                "description": "The slug of the toolkit that provides this tool"
              },
              "description": {
                "type": "string",
                "nullable": true,
                "description": "Description of the tool"
              },
              "input_schema": {
                "type": "object",
                "nullable": true,
                "description": "Input schema for the tool",
                "additionalProperties": true
              },
              "usage_guidelines": {
                "type": "string",
                "nullable": true,
                "description": "Practical usage notes and examples for the tool"
              }
            }
          }
        },
        "toolkit_connection_statuses": {
          "type": "array",
          "description": "Connection status for all toolkits mentioned across all queries, with descriptions merged in",
          "items": {
            "type": "object",
            "properties": {
              "toolkit": {
                "type": "string",
                "description": "The toolkit slug identifier (e.g., \"gmail\", \"slack\")"
              },
              "description": {
                "type": "string",
                "description": "Description of what the toolkit does and its capabilities"
              },
              "has_active_connection": {
                "type": "boolean",
                "description": "Whether an active connection exists for this toolkit"
              },
              "connection_details": {
                "type": "object",
                "description": "Connection details including auth config and connected account IDs",
                "additionalProperties": true
              },
              "current_user_info": {
                "type": "object",
                "nullable": true,
                "description": "Information about the currently connected user (email, name, etc.)",
                "additionalProperties": true
              },
              "account_type": {
                "type": "string",
                "enum": [
                  "PRIVATE",
                  "SHARED"
                ],
                "nullable": true,
                "description": "Sharing model for the connected account when has_active_connection is true. PRIVATE is owner-only; SHARED is reachable only when explicitly pinned to the session."
              },
              "status_message": {
                "type": "string",
                "description": "Human-readable message about the connection status and next steps"
              }
            },
            "required": [
              "toolkit",
              "description",
              "has_active_connection",
              "connection_details",
              "status_message"
            ]
          }
        },
        "time_info": {
          "type": "object",
          "description": "Time information for the query",
          "properties": {
            "current_time_utc": {
              "type": "string",
              "description": "Current time in ISO format (UTC)"
            },
            "current_time_utc_epoch_seconds": {
              "type": "integer",
              "description": "Current time as Unix epoch timestamp in seconds"
            },
            "message": {
              "type": "string",
              "description": "Important message about time handling and timezone considerations"
            }
          },
          "required": [
            "current_time_utc",
            "current_time_utc_epoch_seconds",
            "message"
          ]
        },
        "session": {
          "type": "object",
          "description": "Session info for correlating meta tool calls",
          "properties": {
            "id": {
              "type": "string",
              "description": "Session identifier to be passed to subsequent meta tool calls"
            },
            "generate_id": {
              "type": "boolean",
              "description": "Whether a fresh session id was generated in this call"
            },
            "instructions": {
              "type": "string",
              "description": "LLM-facing guidance on how to reuse this session id"
            }
          },
          "required": [
            "id",
            "generate_id",
            "instructions"
          ]
        },
        "next_steps_guidance": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Combined workflow guidance covering connections, planner, and memory usage. Each element is a step instruction."
        }
      },
      "required": [
        "results",
        "tool_schemas",
        "toolkit_connection_statuses",
        "time_info",
        "session",
        "next_steps_guidance"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution. Format: \"X out of Y searches failed, reasons: <details>\"",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether all searches completed successfully. False if any query failed",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "SearchToolsResponseWrapper",
  "type": "object"
}
```

## 4. `COMPOSIO_GET_TOOL_SCHEMAS`

**一句话**(来自本次任务需求描述):Fetch full input schemas for tool slugs returned by search.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Get Tool Schemas |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | readOnlyHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_GET_TOOL_SCHEMAS`)**

> Retrieve input schemas for tools by slug. Returns complete parameter definitions required to execute each tool. Only pass tool slugs returned by COMPOSIO_SEARCH_TOOLS — never guess or fabricate slugs. If unsure of the exact slug, call COMPOSIO_SEARCH_TOOLS first.

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `tool_slugs` | ✅ | `array` | Array of tool slugs to retrieve schemas for. Pass valid tool slugs; never invent. |
| `include` |  | `array` | Schema fields to include. Defaults to ["input_schema"]. Include "output_schema" when calling tools in the workbench to validate response structure. |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "tool_slugs": {
      "description": "Array of tool slugs to retrieve schemas for. Pass valid tool slugs; never invent.",
      "examples": [
        [
          "GMAIL_SEND_EMAIL",
          "SLACK_SEND_MESSAGE"
        ]
      ],
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "title": "Tool Slugs"
    },
    "include": {
      "description": "Schema fields to include. Defaults to [\"input_schema\"]. Include \"output_schema\" when calling tools in the workbench to validate response structure.",
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "input_schema",
          "output_schema"
        ]
      },
      "default": [
        "input_schema"
      ],
      "examples": [
        [
          "input_schema"
        ],
        [
          "input_schema",
          "output_schema"
        ]
      ]
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "tool_slugs"
  ],
  "title": "GetToolSchemasRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "success": {
          "description": "Whether all requested tool schemas were found",
          "type": "boolean"
        },
        "tool_schemas": {
          "description": "Tool definitions keyed by tool_slug for O(1) lookup. Same format as tool_schemas in search response.",
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "toolkit": {
                "type": "string",
                "description": "The slug of the toolkit that provides this tool"
              },
              "tool_slug": {
                "type": "string",
                "description": "The slug of the tool"
              },
              "description": {
                "type": "string",
                "description": "Description of the tool"
              },
              "input_schema": {
                "type": "object",
                "description": "Input schema for the tool"
              },
              "output_schema": {
                "type": "object",
                "description": "Output schema for the tool when requested via the include field"
              }
            },
            "required": [
              "toolkit",
              "tool_slug"
            ]
          }
        },
        "not_found": {
          "description": "Tool slugs that were not found",
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "suggestions": {
          "description": "For each not-found slug, a list of similar existing tool slugs (up to 3). Call again with the correct slugs to get their schemas.",
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        },
        "not_found_message": {
          "description": "Action message when slugs are not found. Check suggestions for possible matches and call again with correct slugs.",
          "type": "string"
        }
      },
      "required": [
        "success",
        "tool_schemas"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "GetToolSchemasResponseWrapper",
  "type": "object"
}
```

## 5. `COMPOSIO_MULTI_EXECUTE_TOOL`

**一句话**(来自本次任务需求描述):Execute one or more discovered tools in parallel across connected apps (up to 50 per call).

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Multi Execute Composio Tools |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | openWorldHint, destructiveHint, important |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_MULTI_EXECUTE_TOOL`)**

> Fast and parallel tool executor for tools discovered through COMPOSIO_SEARCH_TOOLS. Use this tool to execute up to 50 tools in parallel across apps only when they're logically independent (no ordering/output dependencies). Response contains structured outputs ready for immediate analysis - avoid reprocessing them via remote bash/workbench tools.
> 
> Prerequisites:
> - Always use valid tool slugs and their arguments. NEVER invent tool slugs or argument fields. ALWAYS pass STRICTLY schema-compliant arguments with each tool execution.
> - Ensure an ACTIVE connection exists for the toolkits that are going to be executed. If none exists, MUST initiate one via COMPOSIO_MANAGE_CONNECTIONS before execution.
> - Only batch tools that are logically independent - no ordering, no output-to-input dependencies, and no intra-call chaining (tools in one call can't use each other's outputs). DO NOT pass dummy or placeholder inputs; always resolve required inputs using appropriate tools first.
> 
> Usage guidelines:
> - If COMPOSIO_SEARCH_TOOLS returns a tool that can perform the task, prefer calling it via this executor. Do not write custom API calls or ad-hoc scripts for tasks that can be completed by available Composio tools.
> - Prefer parallel execution: group independent tools into a single multi-execute call where possible.
> - Predictively set sync_response_to_workbench=true if the response may be large or needed for later scripting. It still shows response inline; if the actual response data turns out small and easy to handle, keep everything inline and SKIP workbench usage.
> - Responses contain structured outputs for each tool. RULE: Small data - process yourself inline; large data - process in the workbench.
> - ALWAYS include inline references/links to sources in MARKDOWN format directly next to the relevant text. Eg provide slack thread links alongside with summary, render document links instead of raw IDs.
> 
> Restrictions: Some tools or toolkits may be disabled in this environment. If the response indicates a restriction, inform the user and STOP execution immediately. Do NOT attempt workarounds or speculative actions.
> 
> 
> - CRITICAL: You MUST always include the 'memory' parameter - never omit it. Even if you think there's nothing to remember, include an empty object {} for memory.
> 
> Memory Storage:
> - CRITICAL FORMAT: Memory must be a dictionary where keys are app names (strings) and values are arrays of strings. NEVER pass nested objects or dictionaries as values.
> - CORRECT format: {"slack": ["Channel general has ID C1234567"], "gmail": ["John's email is john@example.com"]}
> - Write memory entries in natural, descriptive language - NOT as key-value pairs. Use full sentences that clearly describe the relationship or information.
> - ONLY store information that will be valuable for future tool executions - focus on persistent data that saves API calls.
> - STORE: ID mappings, entity relationships, configs, stable identifiers.
> - DO NOT STORE: Action descriptions, temporary status updates, logs, or "sent/fetched" confirmations.
> - Examples of GOOD memory (store these):
>   * "The important channel in Slack has ID C1234567 and is called #general"
>   * "The team's main repository is owned by user 'teamlead' with ID 98765"
>   * "The user prefers markdown docs with professional writing, no emojis" (user_preference)
> - Examples of BAD memory (DON'T store these):
>   * "Successfully sent email to john@example.com with message hi"
>   * "Fetching emails from last day (Sep 6, 2025) for analysis"
> - Do not repeat the memories stored or found previously.

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `tools` | ✅ | `array` | List of logically independent tools to execute in parallel. |
| `thought` |  | `string` | One-sentence, concise, high-level rationale (no step-by-step). |
| `sync_response_to_workbench` | ✅ | `boolean` | Predictively set true when the response may be large or needed for later scripting. Saves the full response to the workbench while returning an inline previe... |
| `memory` |  | `object` | CRITICAL: Memory must be a dictionary with app names as keys and string arrays as values. NEVER use nested objects. Format: {"app_name": ["string1", "string2... |
| `current_step` |  | `string` | Short enum for current step of the workflow execution. Eg FETCHING_EMAILS, GENERATING_REPLIES. Always include to keep execution aligned with the workflow. |
| `current_step_metric` |  | `string` | Progress metrics for the current step - use to track how far execution has advanced. Format as a string "done/total units" - example "10/100 emails", "0/n me... |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "tools": {
      "description": "List of logically independent tools to execute in parallel.",
      "items": {
        "properties": {
          "tool_slug": {
            "description": "The slug of the tool to execute — must be a valid tool slug; never invent.",
            "examples": [
              "GMAIL_SEND_EMAIL",
              "SLACK_SEND_MESSAGE",
              "GITHUB_CREATE_AN_ISSUE"
            ],
            "minLength": 1,
            "title": "Tool Slug",
            "type": "string"
          },
          "arguments": {
            "additionalProperties": true,
            "description": "The arguments to pass to the tool. Use exact field names and types; do not diverge from the tool's argument schema.",
            "examples": [
              {
                "body": "This is a test",
                "subject": "Hello",
                "to": "test@gmail.com"
              },
              {
                "channel": "#general",
                "text": "Hello from Composio!"
              },
              {
                "body": "Description of the issue",
                "labels": [
                  "bug"
                ],
                "title": "Bug Report"
              }
            ],
            "title": "Arguments",
            "type": "object"
          }
        },
        "required": [
          "tool_slug",
          "arguments"
        ],
        "title": "MultiExecuteToolItem",
        "type": "object"
      },
      "maxItems": 50,
      "minItems": 1,
      "title": "Tools",
      "type": "array"
    },
    "thought": {
      "description": "One-sentence, concise, high-level rationale (no step-by-step).",
      "title": "Thought",
      "type": "string"
    },
    "sync_response_to_workbench": {
      "description": "Predictively set true when the response may be large or needed for later scripting. Saves the full response to the workbench while returning an inline preview. If the result is small, keep it inline. Default false.",
      "title": "Sync Response To Workbench",
      "type": "boolean"
    },
    "memory": {
      "type": "object",
      "description": "CRITICAL: Memory must be a dictionary with app names as keys and string arrays as values. NEVER use nested objects. Format: {\"app_name\": [\"string1\", \"string2\"]}. Store durable facts - stable IDs, mappings, roles, preferences. Exclude ephemeral data like message IDs or temp links. Use full sentences describing relationships. Always include this parameter.",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "string",
          "description": "Natural language memory string - e.g., \"John's user ID in Slack is 12345\", \"Venky's project MyProject has ID proj_abc123\""
        }
      }
    },
    "current_step": {
      "description": "Short enum for current step of the workflow execution. Eg FETCHING_EMAILS, GENERATING_REPLIES. Always include to keep execution aligned with the workflow.",
      "title": "Current Step",
      "type": "string"
    },
    "current_step_metric": {
      "description": "Progress metrics for the current step - use to track how far execution has advanced. Format as a string \"done/total units\" - example \"10/100 emails\", \"0/n messages\", \"3/10 pages\".",
      "title": "Current Step Metric",
      "type": "string"
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "tools",
    "sync_response_to_workbench"
  ],
  "title": "MultiExecuteToolRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "error_count": {
          "description": "Number of failed tool executions",
          "title": "Error Count",
          "type": "integer"
        },
        "results": {
          "description": "List of responses from executing the tools. Order matches the input order.",
          "examples": [
            [
              {
                "error": null,
                "index": 0,
                "response": {
                  "data": {
                    "response": {
                      "data": {
                        "id": "123",
                        "title": "Issue created",
                        "url": "https://github.com/org/repo/issues/123"
                      }
                    }
                  },
                  "error": null,
                  "log_id": "log_XYZ789",
                  "successful": true
                },
                "tool_slug": "GITHUB_CREATE_AN_ISSUE"
              },
              {
                "error": "No active connected account found for toolkit: gmail",
                "index": 1,
                "response": null,
                "tool_slug": "GMAIL_SEND_EMAIL"
              }
            ]
          ],
          "items": {
            "properties": {
              "error": {
                "default": null,
                "description": "Error message if the tool execution failed",
                "nullable": true,
                "title": "Error",
                "type": "string"
              },
              "index": {
                "description": "Original index of the tool in the request",
                "title": "Index",
                "type": "integer"
              },
              "response": {
                "additionalProperties": true,
                "default": null,
                "description": "The response from executing the tool if successful",
                "nullable": true,
                "title": "Response",
                "type": "object"
              },
              "tool_slug": {
                "description": "The slug of the tool that was executed",
                "title": "Tool Slug",
                "type": "string"
              }
            },
            "required": [
              "tool_slug",
              "index"
            ],
            "title": "MultiExecuteToolItemResponse",
            "type": "object"
          },
          "title": "Results",
          "type": "array"
        },
        "success_count": {
          "description": "Number of successful tool executions",
          "title": "Success Count",
          "type": "integer"
        },
        "total_count": {
          "description": "Total number of tools executed",
          "title": "Total Count",
          "type": "integer"
        },
        "session": {
          "additionalProperties": false,
          "default": null,
          "description": "Session info echoed back to reinforce reuse: { id: string, instructions: string }",
          "nullable": true,
          "properties": {
            "id": {
              "type": "string"
            },
            "instructions": {
              "type": "string"
            }
          },
          "title": "Session",
          "type": "object"
        },
        "remote_file_info": {
          "additionalProperties": true,
          "default": null,
          "description": "Information about the complete response saved to a remote file when response is too large or when sync_response_to_workbench is true",
          "nullable": true,
          "title": "Remote File Info",
          "type": "object"
        },
        "next_steps": {
          "default": null,
          "description": "Next steps for the caller",
          "nullable": true,
          "title": "Next Steps",
          "type": "string"
        }
      },
      "required": [
        "results",
        "total_count",
        "success_count",
        "error_count"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "MultiExecuteActionResponseWrapper",
  "type": "object"
}
```

## 6. `COMPOSIO_MANAGE_CONNECTIONS`

**一句话**(来自本次任务需求描述):Create, list, rename, or remove OAuth connections to upstream apps.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Manage connections |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | openWorldHint, destructiveHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_MANAGE_CONNECTIONS`)**

> Create or manage connections to user's apps. Returns a branded authentication link that works for OAuth, API keys, and all other auth types.
> 
> Call policy:
> - First call COMPOSIO_SEARCH_TOOLS for the user's query.
> - If COMPOSIO_SEARCH_TOOLS indicates there is no active connection for a toolkit, call COMPOSIO_MANAGE_CONNECTIONS with the exact toolkit name(s) returned.
> - Use exact toolkit slugs returned by COMPOSIO_SEARCH_TOOLS; never invent toolkit names.
> - NEVER execute any toolkit tool without an ACTIVE connection.
> 
> Tool Behavior:
> - If a connection is Active, the tool returns the connection details. Always use this to verify connection status and fetch metadata.
> - If a connection is not Active, returns a authentication link (redirect_url) to create new connection.
> - If reinitiate_all is true, the tool forces reconnections for all toolkits, even if they already have active connections.
> 
> Workflow after initiating connection:
> - Always show the returned redirect_url as a FORMATTED MARKDOWN LINK to the user, and ask them to click on the link to finish authentication.
> - Begin executing tools only after the connection for that toolkit is confirmed Active.

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `toolkits` | ✅ | `array` | Toolkit slugs to check or connect. Must be valid toolkit slugs; never invent. Missing connections initiate auth. Examples: ['gmail', 'github', 'slack', 'goog... |
| `reinitiate_all` |  | `boolean` | Force reconnection for all listed toolkits, even if active connections already exist. Use when credentials may be stale, you need fresh credentials/settings,... |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "toolkits": {
      "description": "Toolkit slugs to check or connect. Must be valid toolkit slugs; never invent. Missing connections initiate auth. Examples: ['gmail', 'github', 'slack', 'googlesheets', 'outlook'].",
      "items": {
        "properties": {},
        "type": "string"
      },
      "title": "Toolkits",
      "type": "array"
    },
    "reinitiate_all": {
      "default": false,
      "description": "Force reconnection for all listed toolkits, even if active connections already exist. Use when credentials may be stale, you need fresh credentials/settings, or you are troubleshooting connection issues. This replaces existing active connections with new auth-link flows. Default false.",
      "title": "Reinitiate All",
      "type": "boolean"
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "toolkits"
  ],
  "title": "ManageConnectionsRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "message": {
          "description": "Overall status message",
          "title": "Message",
          "type": "string"
        },
        "results": {
          "additionalProperties": {
            "description": "Result for a single toolkit connection attempt",
            "properties": {
              "has_active_connection": {
                "description": "Whether an active connection exists",
                "title": "Has Active Connection",
                "type": "boolean"
              },
              "auth_config_id": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Auth config ID when a new auth config is created or used",
                "title": "Auth Config Id"
              },
              "connected_account_id": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Connected account ID if available",
                "title": "Connected Account Id"
              },
              "created_at": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Creation time (ISO 8601) for the connection if available",
                "title": "Created At"
              },
              "current_user_info": {
                "additionalProperties": true,
                "default": null,
                "description": "Information about the currently connected user (email, name, etc.)",
                "nullable": true,
                "title": "Current User Info",
                "type": "object"
              },
              "error_message": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Error message if status is 'failed'",
                "title": "Error Message"
              },
              "instruction": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Instructions for user if status is 'initiated'",
                "title": "Instruction"
              },
              "redirect_url": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Authentication link URL if status is 'initiated'. Always show this as a formatted markdown link to the user.",
                "title": "Redirect Url"
              },
              "status": {
                "description": "Status of the connection attempt",
                "enum": [
                  "active",
                  "initiated",
                  "failed"
                ],
                "title": "Status",
                "type": "string"
              },
              "toolkit": {
                "description": "Name of the toolkit",
                "title": "Toolkit",
                "type": "string"
              },
              "was_reinitiated": {
                "anyOf": [
                  {
                    "type": "boolean"
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Whether this connection was reinitiated (vs newly created)",
                "title": "Was Reinitiated"
              },
              "account_type": {
                "anyOf": [
                  {
                    "type": "string",
                    "enum": [
                      "PRIVATE",
                      "SHARED"
                    ]
                  },
                  {
                    "type": "null"
                  }
                ],
                "default": null,
                "description": "Sharing model for the connected account. PRIVATE is owner-only; SHARED is reachable only when explicitly pinned to the session.",
                "title": "Account Type"
              }
            },
            "required": [
              "toolkit",
              "status"
            ],
            "title": "ToolkitConnectionResult",
            "type": "object"
          },
          "description": "Connection results for each toolkit",
          "title": "Results",
          "type": "object"
        },
        "summary": {
          "additionalProperties": false,
          "description": "Summary of results by status type",
          "properties": {
            "total_toolkits": {
              "type": "integer"
            },
            "active_connections": {
              "type": "integer"
            },
            "initiated_connections": {
              "type": "integer"
            },
            "failed_connections": {
              "type": "integer"
            }
          },
          "required": [],
          "title": "Summary",
          "type": "object"
        },
        "session": {
          "additionalProperties": false,
          "description": "Session info echoed back to reinforce reuse: { id: string, instructions: string }",
          "properties": {
            "id": {
              "type": "string"
            },
            "instructions": {
              "type": "string"
            }
          },
          "required": [
            "id",
            "instructions"
          ],
          "title": "Session",
          "type": "object"
        }
      },
      "required": [
        "message",
        "results"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "ManageConnectionResponseWrapper",
  "type": "object"
}
```

## 7. `COMPOSIO_WAIT_FOR_CONNECTIONS`

**一句话**(来自本次任务需求描述):Wait for a user to complete an OAuth flow before the agent continues.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Wait for connection |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | readOnlyHint, idempotentHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_WAIT_FOR_CONNECTIONS`)**

> Wait for user auth to finish. Call ONLY after you have shown the Auth link from COMPOSIO_MANAGE_CONNECTIONS.
> Wait until mode=any/all toolkits reach a terminal state (ACTIVE/FAILED) or timeout.
> 
> Example Input: { toolkits: ["gmail","outlook"], mode: "any" }

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `toolkits` | ✅ | `array` | List of toolkit slugs to wait for. |
| `mode` |  | `string` | Wait for ANY connection or ALL connections to reach active/failed state (default: any) |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "toolkits": {
      "description": "List of toolkit slugs to wait for.",
      "items": {
        "properties": {},
        "type": "string"
      },
      "minItems": 1,
      "title": "Toolkits",
      "type": "array"
    },
    "mode": {
      "default": "any",
      "description": "Wait for ANY connection or ALL connections to reach active/failed state (default: any)",
      "enum": [
        "any",
        "all"
      ],
      "title": "Mode",
      "type": "string"
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "toolkits"
  ],
  "title": "WaitForConnectionRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "description": "Data from the action execution",
      "properties": {
        "message": {
          "description": "Status message summarizing connection statuses",
          "type": "string"
        },
        "results": {
          "description": "Connection status for each toolkit (keyed by toolkit slug)",
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "toolkit": {
                "type": "string"
              },
              "status": {
                "type": "string",
                "description": "Connection status: ACTIVE=ready, INITIATED=auth pending, FAILED=auth failed/expired, NOT_FOUND=no connection exists"
              },
              "has_active_connection": {
                "type": "boolean"
              },
              "connected_account_id": {
                "type": "string"
              },
              "auth_config_id": {
                "type": "string"
              },
              "created_at": {
                "type": "string"
              },
              "current_user_info": {
                "type": "object",
                "additionalProperties": true
              },
              "error_message": {
                "type": "string"
              }
            }
          }
        },
        "session": {
          "description": "Session info echoed back for correlation",
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "instructions": {
              "type": "string"
            }
          }
        }
      },
      "required": [
        "message",
        "results"
      ],
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "WaitForConnectionResponseWrapper",
  "type": "object"
}
```

## 8. `COMPOSIO_REMOTE_WORKBENCH`

**一句话**(来自本次任务需求描述):Run Python in a remote sandbox for bulk operations or processing large tool responses.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Execute Code remotely in work bench |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | destructiveHint, openWorldHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_REMOTE_WORKBENCH`)**

> Process **REMOTE FILES** or script BULK TOOL EXECUTIONS using Python code IN A REMOTE SANDBOX. If you can see the data in chat, DON'T USE THIS TOOL.
> **ONLY** use this when processing **data stored in a remote file** or when scripting bulk tool executions.
> 
> DO NOT USE
> - When the complete response is already inline/in-memory, or you only need quick parsing, summarization, or basic math.
> 
> USE IF
> - To parse/analyze tool outputs saved by COMPOSIO_MULTI_EXECUTE_TOOL to a remote file in the sandbox or to script multi-tool chains there.
> - For bulk or repeated executions of known Composio tools (e.g., add a label to 100 emails).
> - To call APIs via proxy_execute when no Composio tool exists for that API.
> 
> 
> OUTPUTS
> - Returns a compact result or, if too long, artifacts under `/mnt/files/.composio/output` (cloud-backed FUSE mount, persisted across sandbox restarts).
> 
> IMPORTANT CODING RULES:
>   1. Stepwise Execution: Split work into small steps. Save intermediate outputs to `/mnt/files/` (cloud-backed, persisted across failures/timeouts) or variables. Call COMPOSIO_REMOTE_WORKBENCH again for the next step.
>   2. Notebook Persistence: This is a persistent Jupyter notebook cell: variables, functions, imports, and in-memory state persist across executions. Helper functions are preloaded.
>   3. Top-level cells: Do not use `return`; Jupyter only allows it inside functions. For final values, end with `output` or `print(output)`, not `return output`.
>   4. Parallelism & Timeout (CRITICAL): There is a **hard 3-minute (180s) execution limit** per cell. Always prioritize PARALLEL execution using ThreadPoolExecutor for bulk operations - e.g., call run_composio_tool or invoke_llm across rows. If data is large, split it into smaller batches across cells.
>   5. Checkpoints: Save checkpoints to `/mnt/files/` so that long runs can be resumed from the last completed step, even after a timeout or sandbox restart.
>   6. Schema Safety: Never assume the response schema for run_composio_tool if not known already from previous tools. To inspect schema, either run a simple request **outside** the workbench or use invoke_llm helper.
>   7. LLM Helpers: Always use invoke_llm helper for summary, analysis, or field extraction on results; prefer it for much better results over ad hoc filtering.
>   8. Avoid Meta Loops: Do not use run_composio_tool to call COMPOSIO_* meta tools. Only use it for app tools.
>   9. Pagination: Use when data spans multiple pages. Continue fetching pages with the returned next_page_token or cursor until none remains. Parallelize page fetches when the tool supports page_number.
>   10. No Hardcoding: Never hardcode data. Load it from files or tool responses, iterating to construct intermediate or final inputs/outputs.
>   11. If the final output is in a workbench file, use upload_local_file to download it - never expose the raw workbench file path to the user. Prefer to download useful artifacts after task is complete.
> 
> 
> ENV & HELPERS:
> - Home directory: `/home/user`.
> - NOTE: Helper functions already initialized in the workbench - DO NOT import or redeclare them:
>     - 
> `run_composio_tool(tool_slug: str, arguments: dict) -> tuple[Dict[str, Any], str]`: Execute a known Composio **app** tool. Do not invent names; match the tool input schema. Use for loops/parallel/bulk calls.
>       i) run_composio_tool returns JSON with top-level "data". Parse carefully—structure may be nested.
>     
>     - 
> `invoke_llm(query: str) -> tuple[str, str]`: Invoke an LLM for semantic tasks. Pass MAX 200k characters.
>       i) NOTE Prompting guidance: When building prompts for invoke_llm, prefer f-strings (or concatenation) so literal braces stay intact. If using str.format, escape braces by doubling them ({{ }}).
>       ii) Define the exact JSON schema you want and batch items into smaller groups to stay within token limit.
> 
>     - `upload_local_file(*file_paths) -> tuple[Dict[str, Any], str]`: Upload sandbox files to Composio S3/R2 storage for user-downloadable artifacts.
>     - `proxy_execute(method, endpoint, toolkit, query_params=None, body=None, headers=None) -> tuple[Any, str]`: Call a toolkit API directly when no Composio tool exists. Only one toolkit can be invoked with proxy_execute per workbench call
>     - `web_search(query: str) -> tuple[str, str]`: Search the web for information.
>     - `smart_file_extract(sandbox_file_path: str, show_preview: bool = True) -> tuple[str, str]`: Extracts text from files in the sandbox (e.g., PDF, image).
>   All helper functions return a tuple (result, error). Always check error before using result.
> 
> ## Python Helper Functions for LLM Scripting
> 
> 
> ### run_composio_tool
> Executes a known Composio tool via backend API. Do NOT call COMPOSIO_* meta tools to avoid cycles.
> 
>     def run_composio_tool(tool_slug: str, arguments: Dict[str, Any]) -> tuple[Dict[str, Any], str]
>     # Returns: (tool_response_dict, error_message)
>     #   Success: ({"data": {actual_data}}, "") - Note the top-level data
>     #   Error:   ({}, "error_message") or (response_data, "error_message")
> 
>     result, error = run_composio_tool("GMAIL_FETCH_EMAILS", {"max_results": 1, "user_id": "me"})
>     if error:
>         print("GMAIL_FETCH_EMAILS error:", error)
>     else:
>         email_data = result.get("data", {})
>         print("Fetched:", email_data)
>     
> 
> 
> ### invoke_llm
> Calls LLM for reasoning, analysis, and semantic tasks. Pass MAX 200k characters.
> 
>     # Returns: (llm_response, error_message)
> 
>     # Example: analyze tool response with LLM
>     tool_resp, err = run_composio_tool("GMAIL_FETCH_EMAILS", {"max_results": 5, "user_id": "me"})
>     if not err:
>       parsed = tool_resp.get("data", {})
>       resp, err2 = invoke_llm(f"Summarize these emails: {parsed}")
>       if not err2:
>         print(resp)
>     # TIP: batch prompts to reduce LLM calls.
>     
> 
> 
> ### upload_local_file
> Uploads sandbox files to Composio S3/R2 storage for upload/download requests involving generated sandbox artifacts. Single files upload directly; multiple files are auto-zipped.
> 
>     # Returns: (result_dict, error_string)
>     # Success: ({"s3_url": str, "uploaded_file": str, "type": str, "id": str, "s3key": str, "message": str}, "")
>     # Error: ({}, "error_message")
> 
>     # Single file
>     result, error = upload_local_file("/path/to/report.pdf")
> 
>     # Multiple files are auto-zipped
>     result, error = upload_local_file("/home/user/doc1.txt", "/home/user/doc2.txt")
> 
>     if not error:
>       print("Uploaded:", result["s3_url"])
> 
> 
> ### proxy_execute
> Direct API call to a connected toolkit service.
> 
>     def proxy_execute(
>         method: Literal["GET","POST","PUT","DELETE","PATCH"],
>         endpoint: str,
>         toolkit: str,
>         query_params: Optional[Dict[str, str]] = None,
>         body: Optional[object] = None,
>         headers: Optional[Dict[str, str]] = None,
>     ) -> tuple[Any, str]
>     # Returns: (response_data, error_message)
> 
>     # Example: GET request with query parameters
>     query_params = {"q": "is:unread", "maxResults": "10"}
>     data, error = proxy_execute("GET", "/gmail/v1/users/me/messages", "gmail", query_params=query_params)
>     if not error:
>       print("Success:", data)
> 
> 
> ### web_search
> Searches the web via Exa AI.
> 
>     # Returns: (search_results_text, error_message)
> 
>     results, error = web_search("latest developments in AI")
>     if not error:
>         print("Results:", results)
> 
> ## Best Practices
> 
> 
> ### Error-first pattern and Defensive parsing (print keys while narrowing)
>     res, err = run_composio_tool("GMAIL_FETCH_EMAILS", {"max_results": 5})
>     if err:
>         print("error:", err)
>     elif isinstance(res, dict):
>         print("res keys:", list(res.keys()))
>         data = res.get("data") or {}
>         print("data keys:", list(data.keys()))
>         msgs = data.get("messages") or []
>         print("messages count:", len(msgs))
>         for m in msgs:
>             print("subject:", m.get("subject", "<missing>"))
> 
> ### Parallelize within the 3-minute cell timeout
> Adjust concurrency so all tasks finish within 3 minutes.
> 
>     import concurrent.futures
> 
>     MAX_CONCURRENCY = 10 # Adjust as needed
> 
>     def process_one(item):
>         result, error = run_composio_tool("GMAIL_SEND_EMAIL", item)
>         if error:
>             return {"status": "failed", "error": error}
>         return {"status": "ok", "data": result}
> 
>     with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as ex:
>         results = list(ex.map(process_one, items))

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `code_to_execute` | ✅ | `string` | Python to run inside the persistent **remote Jupyter sandbox**. State (imports, variables, files) is preserved across executions. Keep code concise. Avoid un... |
| `thought` |  | `string` | Brief objective for this step. |
| `current_step` |  | `string` | Short enum for current step of the workflow execution. Eg FETCHING_EMAILS, GENERATING_REPLIES. Always include to keep execution aligned with the workflow. |
| `current_step_metric` |  | `string` | Progress metrics for the current step - use to track how far execution has advanced. Format as a string "done/total units" - example "10/100 emails", "0/n me... |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "description": "Remote Workbench - Run Python in a persistent remote sandbox for remote artifacts or scripted Composio tool calls. Avoid when needed data is already inline.",
  "properties": {
    "code_to_execute": {
      "description": "Python to run inside the persistent **remote Jupyter sandbox**. State (imports, variables, files) is preserved across executions. Keep code concise. Avoid unnecessary comments. **Hard 3-minute (180s) execution limit** — break large tasks into smaller cells.",
      "examples": [
        "import json, glob\npaths = glob.glob(file_path)\n...",
        "result, error = run_composio_tool(tool_slug='SLACK_SEARCH_MESSAGES', arguments={'query': 'Rube'})\nif error:\n    print(error)\nelse:\n    messages = result.get('data', {}).get('messages', [])"
      ],
      "title": "Code To Execute",
      "type": "string"
    },
    "thought": {
      "description": "Brief objective for this step.",
      "title": "Thought",
      "type": "string"
    },
    "current_step": {
      "description": "Short enum for current step of the workflow execution. Eg FETCHING_EMAILS, GENERATING_REPLIES. Always include to keep execution aligned with the workflow.",
      "title": "Current Step",
      "type": "string"
    },
    "current_step_metric": {
      "description": "Progress metrics for the current step - use to track how far execution has advanced. Format as a string \"done/total units\" - example \"10/100 emails\", \"0/n messages\", \"3/10 pages\".",
      "title": "Current Step Metric",
      "type": "string"
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "code_to_execute"
  ],
  "title": "RemoteWorkbenchRequest",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "error": {
          "default": "",
          "description": "Error message if any",
          "title": "Error",
          "type": "string"
        },
        "results": {
          "description": "The results of the code execution",
          "title": "Results",
          "type": "string"
        },
        "results_file_path": {
          "description": "Path to file containing full results if output was truncated",
          "title": "Results File Path",
          "type": "string"
        },
        "session": {
          "description": "Session info echoed back to reinforce reuse: { id: string, instructions: string }",
          "additionalProperties": false,
          "properties": {
            "id": {
              "type": "string"
            },
            "instructions": {
              "type": "string"
            }
          },
          "required": [
            "id",
            "instructions"
          ],
          "title": "Session",
          "type": "object"
        },
        "stderr": {
          "description": "The standard error output from the command",
          "title": "Stderr",
          "type": "string"
        },
        "stderr_file_path": {
          "description": "Path to file containing full stderr if output was truncated",
          "title": "Stderr File Path",
          "type": "string"
        },
        "stdout": {
          "description": "The standard output from the command",
          "title": "Stdout",
          "type": "string"
        },
        "stdout_file_path": {
          "description": "Path to file containing full stdout if output was truncated",
          "title": "Stdout File Path",
          "type": "string"
        },
        "sandbox_id_suffix": {
          "description": "Last 4 digits of the sandbox ID for easier reference",
          "title": "Sandbox ID Suffix",
          "type": "string"
        }
      },
      "required": [
        "results",
        "stdout",
        "stderr"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "RemoteWorkbenchResponseWrapper",
  "type": "object"
}
```

## 9. `COMPOSIO_REMOTE_BASH_TOOL`

**一句话**(来自本次任务需求描述):Run bash in a remote sandbox for file processing and large data handling.

**官方元数据**

| 字段 | 值 |
|---|---|
| name | Run bash commands |
| toolkit | `composio` |
| version | `00000000_00`(available: `00000000_00`) |
| no_auth | `True` |
| tags | destructiveHint, openWorldHint |
| is_deprecated | `False` |

**官方描述(原文,来自 `GET /api/v3.1/tools/COMPOSIO_REMOTE_BASH_TOOL`)**

> Execute bash commands in a REMOTE sandbox for file operations, data processing, and system tasks. Essential for handling large tool responses saved to remote files. **Hard 3-minute (180s) execution limit** — break large tasks into smaller commands.
>   PRIMARY USE CASES:
> - Process large tool responses saved by COMPOSIO_MULTI_EXECUTE_TOOL to remote sandbox
> - File system operations, extract specific information from JSON with shell tools like jq, awk, sed, grep, etc.
> - Commands run from /home/user directory by default

**输入参数一览**

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `command` | ✅ | `string` | The bash command to execute. **Hard 3-minute (180s) execution limit** — break large tasks into smaller commands. |
| `session_id` |  | `string` | Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call. |

**输入 JSON Schema(完整)**

```json
{
  "properties": {
    "command": {
      "description": "The bash command to execute. **Hard 3-minute (180s) execution limit** — break large tasks into smaller commands.",
      "title": "Command",
      "type": "string"
    },
    "session_id": {
      "description": "Pass the session_id if you received one from a prior COMPOSIO_SEARCH_TOOLS call.",
      "title": "Session ID",
      "type": "string"
    }
  },
  "required": [
    "command"
  ],
  "title": "RemoteBashToolInput",
  "type": "object"
}
```

**输出 JSON Schema(完整)**

```json
{
  "properties": {
    "data": {
      "additionalProperties": false,
      "description": "Data from the action execution",
      "properties": {
        "session": {
          "description": "Session info echoed back to reinforce reuse: { id: string, instructions: string }",
          "additionalProperties": false,
          "properties": {
            "id": {
              "type": "string"
            },
            "instructions": {
              "type": "string"
            }
          },
          "required": [
            "id",
            "instructions"
          ],
          "title": "Session",
          "type": "object"
        },
        "stderr": {
          "description": "The standard error output from the command, possibly truncated for brevity.",
          "title": "Stderr",
          "type": "string"
        },
        "stderrLines": {
          "description": "Total number of lines in original stderr, even if truncated",
          "title": "Stderr Lines",
          "type": "integer"
        },
        "stderr_file_path": {
          "description": "Path to file containing full stderr if output was truncated",
          "title": "Stderr File Path",
          "type": "string"
        },
        "stdout": {
          "description": "The standard output from the command, possibly truncated for brevity.",
          "title": "Stdout",
          "type": "string"
        },
        "stdoutLines": {
          "description": "Total number of lines in original stdout, even if truncated",
          "title": "Stdout Lines",
          "type": "integer"
        },
        "stdout_file_path": {
          "description": "Path to file containing full stdout if output was truncated",
          "title": "Stdout File Path",
          "type": "string"
        },
        "sandbox_id_suffix": {
          "description": "Last 4 digits of the sandbox ID for easier reference",
          "title": "Sandbox ID Suffix",
          "type": "string"
        }
      },
      "required": [
        "stdout",
        "stdoutLines",
        "stderr",
        "stderrLines"
      ],
      "title": "Data",
      "type": "object"
    },
    "error": {
      "default": null,
      "description": "Error if any occurred during the execution of the action",
      "nullable": true,
      "title": "Error",
      "type": "string"
    },
    "successful": {
      "description": "Whether or not the action execution was successful or not",
      "title": "Successful",
      "type": "boolean"
    }
  },
  "required": [
    "data",
    "successful"
  ],
  "title": "RemoteBashToolOutputWrapper",
  "type": "object"
}
```



## 10. 原始数据文件

本文档每个工具的 `input_parameters` / `output_parameters` 就是 `GET /api/v3.1/tools/{slug}` 的原样返回;完整的 7 个工具原始 JSON(含 `scopes`、`scope_requirements`、`deprecated` 等本文档表格里没展开的字段)另存为同目录下的 [composio-meta-tools-schemas.json](composio-meta-tools-schemas.json),供后续写代码时直接读取。

## 11. 下一步建议

1. 去 Composio Dashboard → 对应 Project → API Keys,给 `backend/.env` 里这把 `COMPOSIO_API_KEY` 补上 `tool_execution:write` 和 `session_management:write`(或者新建一把带这两个权限的 key),这样才能真正跑 `session.execute` 拿到执行期返回值,而不只是 schema。
2. 如果只是想验证"搜索 → 拿 schema"这两步(不需要真正执行工具),当前权限已经完全够用——`COMPOSIO_SEARCH_TOOLS` 和 `COMPOSIO_GET_TOOL_SCHEMAS` 的完整 schema 已经在第 3、4 节。
3. `COMPOSIO_MANAGE_CONNECTIONS` / `COMPOSIO_WAIT_FOR_CONNECTIONS` 一旦能执行,建议先在 `toolkits` 里选一个低风险的 toolkit(比如只读类的公开 API)做首次连通测试,避免一上来就对高权限应用(如 Gmail/GitHub 有写权限的 toolkit)发起授权。

## 12. 真实执行验证(换用有权限的 key 之后)

`backend/.env` 里的 `COMPOSIO_API_KEY` 换成一把带 `session_management:write` + `tool_execution:write` 权限的 key 后,重新验证了 Session 路径和直连路径,并用 `COMPOSIO_SEARCH_TOOLS` → `COMPOSIO_GET_TOOL_SCHEMAS` → `COMPOSIO_MULTI_EXECUTE_TOOL` 三个元工具串联执行了一次真实业务查询(Jira 已连接账号下,某项目近 5 天的 issue)。

> 本节不贴具体查询返回的业务数据(工单标题、经办人等) —— 那属于公司内部 Jira 的真实业务内容,不适合写进提交到 git 的文档;实际查询结果已经在对话里回复给你了。这里只记录**方法本身跑没跑通、返回结构长什么样、踩了什么坑**。

### 12.1 Session 路径:三步全部跑通

```python
from composio import Composio
composio = Composio(api_key=COMPOSIO_API_KEY)
session = composio.sessions.create(user_id=COMPOSIO_USER_ID)   # OK,拿到 session.session_id

# 1) 搜索
r1 = session.execute("COMPOSIO_SEARCH_TOOLS", arguments={
    "queries": [{"use_case": "...", "known_fields": "project_key:VMS"}],
    "session": {"generate_id": True},
})
# r1.data.session.id -> 一个工作流级别的 session_id(注意:和上面 session.session_id 是两个不同概念!)
# r1.data.toolkit_connection_statuses -> 确认 jira 是 ACTIVE 连接
# r1.data.results[0].primary_tool_slugs -> ["JIRA_SEARCH_ISSUES"]
# r1.data.tool_schemas["JIRA_SEARCH_ISSUES"] -> 连完整 input_schema 都一起返回了,不用再单独调 GET_TOOL_SCHEMAS

# 2) 取 schema(即使 search 已经带回来了,仍按需求单独调用验证)
r2 = session.execute("COMPOSIO_GET_TOOL_SCHEMAS", arguments={
    "tool_slugs": ["JIRA_SEARCH_ISSUES"],
    "session_id": r1["data"]["session"]["id"],   # 必须带上 search 返回的这个 workflow session id
})

# 3) 执行
r3 = session.execute("COMPOSIO_MULTI_EXECUTE_TOOL", arguments={
    "tools": [{"tool_slug": "JIRA_SEARCH_ISSUES", "arguments": {
        "project_key": "VMS", "created_after": "-5d",
        "fields": ["key","summary","status","assignee","created","issuetype","priority"],
        "max_results": 50,
    }}],
    "sync_response_to_workbench": False,
    "memory": {},
    "session_id": r1["data"]["session"]["id"],
})
# r3.data.results[0].response.data -> 真实 Jira 搜索结果(issues 数组 + jql_used + total)
```

**三步全部返回 `successful: true`**,`JIRA_SEARCH_ISSUES` 的 `jql_used` 字段确认服务端把结构化过滤参数翻译成了 `project = VMS AND created >= -5d ORDER BY created DESC`。

**一个容易踩的坑**:`COMPOSIO_SEARCH_TOOLS` 返回的 `session.id`(工作流级别,例子里类似 `"gate"`/`"lead"` 这种短字符串)和顶层 `composio.sessions.create()` 返回的 `session.session_id`(`trs_xxx` 格式)是**两个不同的东西**,必须把前者原样传给后续 `COMPOSIO_GET_TOOL_SCHEMAS` / `COMPOSIO_MULTI_EXECUTE_TOOL` 调用的 `session_id` 参数,才能让服务端识别为同一个工作流(否则会拿不到 search 阶段生成的执行计划缓存)。

### 12.2 直连路径:`SEARCH_TOOLS` / `GET_TOOL_SCHEMAS` 可以直连,`MULTI_EXECUTE_TOOL` 不行

```python
composio.tools.execute("COMPOSIO_SEARCH_TOOLS", user_id=USER_ID, arguments={...},
                        dangerously_skip_version_check=True)      # successful: true
composio.tools.execute("COMPOSIO_GET_TOOL_SCHEMAS", user_id=USER_ID, arguments={...},
                        dangerously_skip_version_check=True)      # successful: true
composio.tools.execute("COMPOSIO_MULTI_EXECUTE_TOOL", user_id=USER_ID, arguments={...},
                        dangerously_skip_version_check=True)
# -> successful: false
# -> error: "Invalid request for COMPOSIO_MULTI_EXECUTE_TOOL: COMPOSIO_MULTI_EXECUTE_TOOL can only be called inside a tool-router session."
```

**重要发现,和权限无关**:换了有全部权限的 key 之后,`COMPOSIO_SEARCH_TOOLS`、`COMPOSIO_GET_TOOL_SCHEMAS` 两个工具直连(不经过 `session = composio.sessions.create()`)也能正常跑;但 **`COMPOSIO_MULTI_EXECUTE_TOOL` 服务端强制要求必须在 Tool Router session 内调用**,直连会被明确拒绝(`400`,报错信息里直说了原因),这是一个和 key 权限无关的架构限制,不是配置问题。也就是说:**只要工作流里用到 `COMPOSIO_MULTI_EXECUTE_TOOL`(真正执行工具这一步),就必须走 Session 路径**;`SEARCH_TOOLS`/`GET_TOOL_SCHEMAS` 这两个纯查询类元工具两条路径都能用。

### 12.3 结论更新

- Session 路径(wiki 路径 A):`session.execute` 对这 3 个元工具**全部验证通过**,且真实跑通了一次"搜索 → 取 schema → 执行"的完整业务查询(Jira 项目近 5 天 issue,结果已在对话中回复)。
- 直连路径(wiki 路径 B):`COMPOSIO_SEARCH_TOOLS`、`COMPOSIO_GET_TOOL_SCHEMAS` 可以直连执行;`COMPOSIO_MULTI_EXECUTE_TOOL` **不可以**,服务端强制要求 Tool Router session。这一点 wiki 笔记里没有明确提到,是这次实测才确认的边界。
