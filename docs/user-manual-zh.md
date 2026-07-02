# SkillHub 中文用户手册

> 适用版本：以当前项目中的前端页面与后端实现为准  
> 适用对象：普通用户、资源维护者、平台管理员

## 1. 文档说明

本文档是 SkillHub 的中文用户手册，重点说明登录后在 Web 界面中可以实际看到、点击和配置的功能。手册以当前前端页面为主线，同时结合后端实现说明字段含义、默认行为、典型填写方式，以及“系统支持但当前页面未开放”的差异。

本文档不作为 API 说明书使用，因此不会展开描述接口路径或鉴权细节。若页面行为与后端能力存在差异，文中会明确标注“当前前端限制”或“当前版本注意事项”。

## 2. 适用对象与访问前提

### 2.1 适用对象

- 普通用户：查看市场技能、管理个人技能、维护自己可见的资源、Token、ACL 规则，并在权限范围内查看审计日志。
- 管理员：除以上操作外，还更常使用全局资源治理、ACL 管理、API Keys 管理、全局审计日志查询等功能。

### 2.2 访问前提

1. 使用已开通的 SkillHub 账号登录系统。
2. 登录成功后进入主界面。
3. 不同角色看到的导航项和数据范围可能不同。

### 2.3 角色差异

- 所有登录用户都可以进入 `Skills`、`Resources`、`Tokens`、`ACL Rules`、`Settings`。
- `Users` 页面为管理员专属入口，不属于本文手册正文范围。
- `Audit Logs` 页面所有登录用户都可进入，但普通用户通常只能查看自己的日志，管理员可查看全局日志。

## 3. 平台界面总览

### 3.1 左侧导航结构

登录后，左侧导航通常包括以下入口：

- `Dashboard`
- `Skills`
- `Resources`
- `Tokens`
- `ACL Rules`
- `Settings`
- `Users`（仅管理员可见）

### 3.2 各入口职责概览

| 入口 | 主要用途 | 谁更常用 |
| --- | --- | --- |
| `Skills` | 浏览市场技能、维护个人技能、测试技能调用 | 所有用户 |
| `Resources` | 维护技能运行依赖的外部资源配置 | 资源维护者、管理员 |
| `Tokens` | 托管第三方访问凭证，供资源配置引用 | 资源维护者、管理员 |
| `ACL Rules` | 控制资源访问方式与条件 | 管理员、治理人员 |
| `Settings` | 管理 API Keys、查询 Audit Logs | 管理员更常用，普通用户也可使用部分能力 |

### 3.3 典型使用顺序

常见的使用顺序通常如下：

1. 先在 `Tokens` 中托管第三方密钥。
2. 再在 `Resources` 中配置可被 Skill 调用的资源。
3. 在 `Skills` 中创建或编辑技能，并关联资源。
4. 在 `ACL Rules` 中为资源补充访问模式和条件限制。
5. 如需程序化接入，再到 `Settings > API Keys` 创建外部调用凭证。
6. 出现问题或需要追踪操作时，到 `Settings > Audit Logs` 查询记录。

## 4. Skill 管理

### 4.1 页面入口与总体结构

从左侧点击 `Skills` 进入技能页。该页面顶部包含两个标签页：

- `Market`
- `Profile`

其中：

- `Market` 用于浏览系统中的已发布技能。
- `Profile` 用于维护当前用户自己的技能。

### 4.2 Market：浏览技能市场

在 `Market` 页签中，用户通常会看到：

- 搜索框
- 类别筛选器
- 技能卡片列表
- `View Details` 按钮

典型操作流程如下：

1. 进入 `Skills` 页面后停留在 `Market` 页签。
2. 在搜索框输入关键词，按技能名称或描述筛选结果。
3. 使用类别下拉框缩小范围。
4. 在技能卡片上点击 `View Details`，进入技能详情页。

适用说明：

- 普通用户更常在这里查找可复用的技能。
- 管理员也常用这里核查已发布技能的展示效果。

### 4.3 Profile：管理个人技能

切换到 `Profile` 页签后，页面通常包括：

- 搜索框
- `Create New Skill`
- 技能列表
- `View`
- `Edit`
- `Delete`

典型操作流程如下：

1. 点击 `Profile` 页签。
2. 使用搜索框按名称或描述筛选自己的技能。
3. 点击 `Create New Skill` 创建新技能。
4. 已有技能可点击 `View` 查看详情，点击 `Edit` 进入编辑页，点击 `Delete` 删除。
5. 删除操作通常会有确认流程，避免误删。

### 4.4 创建技能

进入 `Create New Skill` 后，页面会展示基础表单、内容编辑区，以及 AI 生成功能。

#### 4.4.1 创建步骤

1. 从 `Skills > Profile` 点击 `Create New Skill`。
2. 填写技能描述、分类、版本、标签等字段。
3. 在内容编辑区填写带 YAML frontmatter 的技能内容。
4. 如需 AI 生成，可选择生成模式并补充依赖信息。
5. 确认无误后保存。

#### 4.4.2 关键字段说明

| 字段 | 页面表现 | 说明 |
| --- | --- | --- |
| `Skill Name` | 只读 | 页面不直接允许输入，实际名称来自 `content` 中 YAML frontmatter 的 `name` |
| `description` | 可编辑 | 技能摘要说明，建议清楚写明用途、输入输出或适用场景 |
| `category` | 可编辑 | 技能分类，便于列表筛选与市场展示 |
| `tags` | 可编辑 | 标签集合，便于搜索与归类 |
| `version` | 可编辑 | 技能版本号，建议遵循团队统一版本规范 |
| `content` | 可编辑 | 技能正文内容，必须包含合法 YAML frontmatter |

#### 4.4.3 YAML frontmatter 要求

当前版本下，技能内容开头必须包含 YAML frontmatter，且至少包含：

- `name`
- `description`

推荐示例：

```yaml
---
name: order-risk-check
description: 检查订单风控信息并生成处理建议
---
```

重要说明：

- 页面上的 `Skill Name` 只是展示位，不能直接修改。
- 系统保存时会从 `content` 中提取 frontmatter 的 `name` 作为技能真实名称。
- 如果要修改技能名称，必须编辑 `content` 中的 frontmatter，再重新保存。

#### 4.4.4 AI 生成功能

技能创建页支持两种 AI 生成模式：

| 模式 | 依赖前提 | 必填内容 | 适用场景 |
| --- | --- | --- | --- |
| `Base Mode` | 已存在资源 | 选择 `resource_id_list` | 基于资源快速生成技能草稿 |
| `SOP Mode` | 已存在技能 | 选择 `skill_id_list`，填写 `userinput` | 基于现有技能组合或 SOP 场景生成技能 |

使用 `Base Mode` 的典型步骤：

1. 先确保 `Resources` 中已经创建所需资源。
2. 在创建技能页选择 `Base Mode`。
3. 选择一个或多个资源。
4. 触发生成后检查结果，再人工调整内容。

使用 `SOP Mode` 的典型步骤：

1. 先确保系统中已有可复用技能。
2. 选择 `SOP Mode`。
3. 选择一个或多个已有技能。
4. 在 `userinput` 中描述本次生成需求。
5. 触发生成并复核输出内容。

注意：

- `Base Mode` 不能脱离已创建资源单独使用。
- `SOP Mode` 不能只选技能不填 `userinput`。

### 4.5 查看技能详情

点击技能列表中的 `View Details` 或 `View` 后进入详情页，通常可执行以下操作：

- 查看技能名称、描述、分类、标签、版本等元信息
- 查看技能正文内容
- 打开 `Test` 弹窗进行调用测试

#### 4.5.1 Test 测试流程

1. 在技能详情页点击 `Test`。
2. 在弹窗中输入 JSON 参数。
3. 点击运行按钮。
4. 查看返回结果或错误信息。

这里的输入参数需要是合法 JSON，例如：

```json
{
  "query": "请分析最近一周的工单异常"
}
```

### 4.6 编辑技能

从 `Profile` 列表点击 `Edit` 可进入编辑页。

编辑页与创建页整体结构相似，重点区别如下：

- 可以修改描述、分类、版本、标签、内容等信息。
- `Skill Name` 仍然是只读展示字段。
- 如果要改名，必须修改 `content` 中 frontmatter 的 `name`，再保存。

### 4.7 删除技能

删除通常从 `Profile` 列表发起。建议在删除前确认以下事项：

- 技能是否仍被团队成员引用
- 技能是否用于 SOP 生成或联动流程
- 是否需要先备份内容

## 5. 资源管理

### 5.1 页面入口与总体结构

从左侧点击 `Resources` 进入资源管理页。页面通常包括：

- 搜索框
- 类型筛选
- 资源列表
- `New Resource`
- 编辑按钮
- 删除按钮

删除操作通常会带二次确认，以避免误删。

### 5.2 页面操作流程

典型操作流程如下：

1. 进入 `Resources` 页面。
2. 使用搜索框按名称或描述筛选资源。
3. 使用类型筛选查看 `gateway`、`third` 或 `mcp` 资源。
4. 点击 `New Resource` 新建资源。
5. 如需修改，点击编辑按钮进入表单。
6. 如需删除，点击删除并在确认后执行。

### 5.3 通用字段说明

无论哪类资源，表单中通常都会出现以下字段：

| 字段 | 说明 | 典型填写方式 |
| --- | --- | --- |
| `Name` | 资源名称，建议能体现业务用途 | 例如 `crm-gateway-prod` |
| `Type` | 资源类型 | `gateway`、`third`、`mcp` |
| `URL` | 资源访问地址 | `gateway`、`third` 通常必填 |
| `Description` | 资源说明 | 写清用途、环境、依赖系统 |
| `Visibility` | 可见范围 | 常见值为 `public` 或 `private` |
| `API Documentation` | 资源接口说明文档 | 可填写文档地址或简要说明 |
| `Extended Properties (JSON)` | 扩展配置 JSON | 用于补充高级参数，如 header、timeout |

关于 `Visibility`：

- 前端新建时通常以 `public` 作为初始表现值。
- 最终以实际提交值为准。
- 不同版本后端默认值可能不同，因此创建时建议显式确认。

### 5.4 三类资源的差异

#### 5.4.1 `gateway` 资源

`gateway` 适合配置通过网关代理访问的资源。

页面特点：

- 需要填写 `URL`
- 可填写 `API Documentation`
- 高级参数主要通过 `Extended Properties (JSON)` 填写

`ext` 中常见字段：

| 字段 | 说明 |
| --- | --- |
| `headers` | 请求头补充配置 |
| `timeout` | 超时时间，当前按秒生效 |

典型示例：

```json
{
  "headers": {
    "Authorization": "Bearer {crm_token}"
  },
  "timeout": 30
}
```

说明：

- `timeout` 当前按秒生效。
- 如果未显式填写，系统运行时默认按 `30` 秒处理。

#### 5.4.2 `third` 资源

`third` 适合直连第三方 HTTP 接口。

页面特点：

- 需要填写 `URL`
- 页面会单独提供 `HTTP Method` 选择器
- 选中的方法最终写入 `ext.method`
- 可通过 `ext.timeout`、`ext.headers` 补充高级行为

常见字段含义：

| 字段 | 说明 |
| --- | --- |
| `HTTP Method` | 页面选择项，最终写入 `ext.method` |
| `ext.timeout` | 请求超时时间，当前按秒生效 |
| `ext.headers` | 自定义请求头 |

典型示例：

```json
{
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "{vendor_api_key}"
  },
  "timeout": 15
}
```

#### 5.4.3 `mcp` 资源

`mcp` 使用专用 MCP 配置区，不完全依赖普通 `URL + ext` 方式。

页面中通常包括以下 MCP 专有字段：

| 字段 | 说明 |
| --- | --- |
| `transport` | 传输方式 |
| `endpoint` | MCP 服务地址 |
| `timeout` | 超时时间，单位为毫秒 |
| `headers` | 请求头 JSON |

当前前端界面中可见的 `transport` 选项通常包括：

- `sse`
- `httpstream`
- `stdio`
- `ws`

但当前版本建议如下：

- `sse`、`httpstream` 可作为主用方式。
- `stdio`、`ws` 在界面中虽然可见，但当前标记为不支持，不建议在生产场景依赖。

MCP 典型示例：

```json
{
  "transport": "sse",
  "endpoint": "https://mcp.example.com/sse",
  "timeout": 30000,
  "headers": {
    "Authorization": "Bearer ${token:mcp_service_token}"
  }
}
```

### 5.5 `ext` 扩展 JSON 说明

`Extended Properties (JSON)` 是资源配置中的扩展区，用于补充表单未直接暴露的高级参数。对 `gateway` 和 `third` 而言，它尤其重要。

常见用途如下：

| 用途 | 典型字段 |
| --- | --- |
| 补充鉴权信息 | `headers` |
| 指定请求方式 | `method` |
| 控制超时 | `timeout` |

典型示例 1：为 `gateway` 配置鉴权头和超时

```json
{
  "headers": {
    "Authorization": "Bearer {gateway_token}"
  },
  "timeout": 20
}
```

典型示例 2：为 `third` 配置 POST 方法

```json
{
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "timeout": 10
}
```

典型示例 3：附加业务头

```json
{
  "headers": {
    "X-App-Id": "skillhub",
    "X-Env": "prod"
  }
}
```

### 5.6 资源超时设置的关键差异

这是资源配置中最容易混淆的部分：

| 资源类型 | 超时字段 | 单位 | 当前默认行为 |
| --- | --- | --- | --- |
| `gateway` | `ext.timeout` | 秒 | 未填写时默认 `30` 秒 |
| `third` | `ext.timeout` | 秒 | 未填写时默认 `30` 秒 |
| `mcp` | `mcp_config.timeout` | 毫秒 | 默认值为 `30000` 毫秒 |

使用建议：

- `gateway`、`third` 中填写 `timeout: 30` 时，通常表示 30 秒。
- `mcp` 中填写 `timeout: 30000` 时，表示 30000 毫秒，即 30 秒。
- 同样写“30”在这两类资源里不是同一个含义。

## 6. Token 托管

### 6.1 页面入口与总体结构

从左侧点击 `Tokens` 进入托管 Token 页面。页面通常包括：

- 搜索框
- 按 `app_name` 的筛选器
- Token 列表
- `New Token`
- 编辑按钮
- 删除按钮
- 显示/隐藏值按钮

### 6.2 典型操作流程

1. 进入 `Tokens` 页面。
2. 通过搜索框按名称搜索。
3. 通过 `app_name` 筛选同一业务分组下的 Token。
4. 点击 `New Token` 新建。
5. 在列表中按需编辑、删除，或切换密钥显示状态。

### 6.3 字段说明

| 字段 | 说明 | 建议 |
| --- | --- | --- |
| `app_name` | 应用或业务分组名 | 例如 `crm`、`openai`、`mcp_ops` |
| `key_name` | Token 引用名 | 建议短、稳定、便于在资源里引用 |
| `value` | 密钥值本体 | 粘贴真实 token、secret 或 API key |
| `desc` | 描述说明 | 写清用途、环境、过期时间、维护人 |

### 6.4 前端页面行为

当前前端有两个值得注意的行为：

1. `key_name` 会自动过滤为字母、数字、下划线。
2. Token 值在列表中默认掩码显示，可手动切换为明文查看。

因此，创建时建议使用如下命名方式：

- `app_name`：用于业务分组，例如 `crm`
- `key_name`：用于配置引用，例如 `crm_api_token`
- `desc`：用于说明“生产环境 CRM Token，2026-12-31 到期”

### 6.5 与资源配置的关系

托管 Token 主要用于被资源配置引用，而不是给用户手工复制粘贴使用。

当前典型引用方式如下：

| 使用位置 | 引用写法 |
| --- | --- |
| `gateway` / `third` | `{token_name}` |
| `mcp` | `${token:token_name}` |

示例 1：在 `gateway` 资源的 header 中引用

```json
{
  "headers": {
    "Authorization": "Bearer {crm_api_token}"
  }
}
```

示例 2：在 `mcp` 资源的 header 中引用

```json
{
  "Authorization": "Bearer ${token:mcp_service_token}"
}
```

## 7. ACL 管理

### 7.1 页面入口与总体结构

从左侧点击 `ACL Rules` 进入访问控制规则页。页面通常包括：

- 搜索框
- `Access Mode` 筛选器
- 规则表格
- `New Rule`

### 7.2 页面操作流程

1. 进入 `ACL Rules` 页面。
2. 通过搜索框按资源名称或关联信息筛选。
3. 通过访问模式筛选 `any` 或 `rbac` 规则。
4. 点击 `New Rule` 创建新规则。
5. 在表格中编辑或删除已有规则。

### 7.3 创建与编辑规则

当前创建/编辑弹窗支持的内容主要有：

- 选择 `Resource`
- 选择 `Access Mode`
- 填写 `Conditions JSON`

重要限制：

- 创建规则时可以选择资源。
- 编辑已有规则时，通常只能修改访问模式和条件，不能改绑定资源。

### 7.4 访问模式说明

| 模式 | 含义 | 典型使用场景 |
| --- | --- | --- |
| `any` | 公开访问，但仍可叠加条件 | 对内公共资源、低风险接口 |
| `rbac` | 角色型访问控制 | 高风险资源、敏感数据接口 |

关于 `any` 的理解：

- `any` 不等于“毫无限制”。
- 即使是 `any`，仍可在 `Conditions JSON` 中叠加 IP、限流、时间窗等约束。

### 7.5 `Conditions JSON` 字段说明

`Conditions JSON` 是 ACL 规则最核心的配置区。当前应重点理解以下字段：

| 字段 | 说明 |
| --- | --- |
| `users` | 允许访问的用户列表 |
| `roles` | 允许访问的角色列表 |
| `ip_whitelist` | 允许访问的 IP 白名单 |
| `rate_limit.requests` | 窗口期内允许的请求次数 |
| `rate_limit.window` | 限流窗口大小 |
| `time_windows` | 允许访问的时间窗 |
| `metadata` | 补充业务侧元信息 |

典型示例：

```json
{
  "users": ["alice", "bob"],
  "roles": ["ops", "admin"],
  "ip_whitelist": ["10.0.0.1", "10.0.0.2"],
  "rate_limit": {
    "requests": 100,
    "window": "1m"
  },
  "time_windows": [
    {
      "start": "09:00",
      "end": "18:00",
      "timezone": "Asia/Shanghai"
    }
  ],
  "metadata": {
    "remark": "工作时间内允许运营团队访问"
  }
}
```

### 7.6 当前前端限制：`role_bindings`

这是 ACL 页面中最需要额外说明的实现差异：

- 系统后端支持 `role_bindings` 的增删改查。
- ACL 列表中也能看到 `role_bindings` 的展示信息。
- 但当前前端创建/编辑弹窗没有提供 `role_bindings` 的维护入口。

因此：

- 手册中可以将 `role_bindings` 视为“系统支持，但当前前端暂未开放编辑”的能力。
- 如果团队依赖该能力，通常需要等待前端补齐或通过其他管理方式处理。

## 8. Settings 总览

### 8.1 页面结构

从左侧点击 `Settings` 后，进入的是一个页内双标签容器，而不是单一功能页。页面顶部通常有两个 tab：

- `API Keys`
- `Audit Logs`

### 8.2 两个子模块的用途

| Tab | 主要用途 |
| --- | --- |
| `API Keys` | 给外部程序创建调用 SkillHub API 的接入凭证 |
| `Audit Logs` | 查询系统中的操作与访问记录 |

### 8.3 与其他模块的关系

- `API Keys` 是程序接入 SkillHub 的凭证，不等同于 `Tokens` 中托管的第三方密钥。
- `Tokens` 主要是供资源配置引用第三方凭据。
- `Audit Logs` 可用于回溯技能、资源、ACL、API Key 等对象的操作记录。

## 9. API Keys 管理

### 9.1 页面入口

进入路径为：

1. 左侧点击 `Settings`
2. 切换到 `API Keys` tab

### 9.2 页面元素总览

当前页面通常包括：

- 说明卡片
- `Create New Key`
- Key 列表
- `Rotate`
- `Revoke`
- 创建或轮换成功后的展示弹窗

### 9.3 创建 API Key

点击 `Create New Key` 后，弹窗通常需要填写以下字段：

| 字段 | 说明 | 典型建议 |
| --- | --- | --- |
| `Key Name` | 当前 key 的用途名称 | 例如 `ci-readonly`、`ops-automation` |
| `Expiration` | 过期策略 | 按用途选择是否长期有效 |
| `Permissions (Scopes)` | 允许的能力范围 | 按最小权限原则选择 |

#### 9.3.1 Expiration 可选项

当前前端通常提供以下选项：

- `Never`
- `30 days`
- `90 days`
- `1 year`

建议：

- 自动化脚本优先设置明确过期时间。
- 长期凭证要配合定期轮换制度。

#### 9.3.2 Scopes 可选项

当前前端创建弹窗中可选的 scopes 通常包括：

- `resources:read`
- `resources:write`
- `skills:read`
- `skills:call`
- `skills:write`
- `acl:read`
- `acl:write`
- `users:read`
- `audit:read`

作用示例：

| Scope | 典型用途 |
| --- | --- |
| `resources:read` | 读取资源列表或详情 |
| `resources:write` | 新建、修改资源 |
| `skills:read` | 读取技能信息 |
| `skills:call` | 调用技能 |
| `skills:write` | 创建或编辑技能 |
| `acl:read` | 查看 ACL 规则 |
| `acl:write` | 创建或修改 ACL 规则 |
| `users:read` | 读取用户信息 |
| `audit:read` | 查询审计日志 |

当前实现差异：

- 后端 scope 定义中还支持 `tokens:read` 与 `tokens:write`。
- 但当前前端创建弹窗没有提供这两个 scope 选项。

因此，本文档应以“当前页面可选项”为准，同时保留这一差异提示。

### 9.4 创建成功后的完整 Key 展示

无论是创建还是轮换成功，系统都会弹出完整 key 展示弹窗。

该弹窗通常支持：

- 显示/隐藏完整 key
- 一键复制
- 关闭弹窗

最重要的行为说明如下：

1. API key 完整值只会在创建成功或轮换成功后展示一次。
2. 关闭弹窗后，后续无法再次查看完整 key。
3. 如果丢失完整 key，通常只能重新 `Rotate` 生成新的。

### 9.5 列表字段说明

API key 列表中常见字段如下：

| 字段 | 说明 |
| --- | --- |
| `name` | key 名称 |
| `key_prefix` | key 前缀，用于识别是哪一把 key |
| `scopes` | 当前 key 具备的权限范围 |
| `expires_at` | 过期时间 |
| `last_used_at` | 最近使用时间 |
| `is_active` | 当前是否有效 |

### 9.6 Revoke 与 Rotate 的区别

这两个按钮容易混淆，建议明确区分：

| 操作 | 含义 | 结果 |
| --- | --- | --- |
| `Revoke` | 使当前 key 失效 | key 不再可用，但不等同于物理删除记录 |
| `Rotate` | 生成新 key，并废弃旧 key | 会返回新的完整 key，旧 key 立即作废 |

使用建议：

- 不再需要的 key 使用 `Revoke`。
- 怀疑泄露、到期更替或例行轮换时使用 `Rotate`。

## 10. Audit Logs 查询

### 10.1 页面入口

进入路径为：

1. 左侧点击 `Settings`
2. 切换到 `Audit Logs` tab

### 10.2 页面元素总览

当前页面通常包括：

- 筛选区
- 结果统计
- 日志表格
- `Details` 弹窗
- 分页
- `Export Logs` 按钮

### 10.3 筛选区字段说明

当前筛选区通常支持以下字段：

| 字段 | 说明 |
| --- | --- |
| `User ID / Username` | 按用户 ID 或用户名筛选 |
| `Resource Type` | 按资源类型筛选 |
| `Status` | 按成功、失败等状态筛选 |
| `From` | 起始时间 |
| `To` | 截止时间 |
| `Action` | 按动作名筛选 |
| `Resource ID` | 按资源标识筛选 |

典型使用流程如下：

1. 进入 `Audit Logs` 页面。
2. 在筛选区输入或选择条件。
3. 点击查询或等待列表刷新。
4. 在结果统计区查看当前页显示范围与总日志数。
5. 结合结果统计与分页查看匹配记录。
6. 如需深入排查，点击 `Details` 查看单条详情。

结果统计通常会以“当前显示第 X 到第 Y 条，共 Z 条日志”的形式出现，用于帮助用户确认筛选是否生效。

### 10.4 分页说明

当日志数量较多时，页面会提供：

- 页码按钮
- `Previous`
- `Next`

普通用户更常用分页查看自己的调用记录，管理员则更常结合筛选条件逐步缩小全局结果集。

### 10.5 表格字段说明

日志表格中常见字段如下：

| 字段 | 说明 |
| --- | --- |
| `Timestamp` | 日志时间 |
| `Action` | 动作名 |
| `User` | 操作用户 |
| `IP Address` | 来源 IP |
| `Status` | 执行状态 |
| `Details` | 查看详情入口 |

### 10.6 Details 弹窗内容

点击单条日志的 `Details` 后，弹窗中通常会展示以下信息：

| 字段 | 说明 |
| --- | --- |
| 状态 | 成功或失败状态 |
| 日志编号缩略值 | 日志 ID 的简写形式 |
| 时间 | 记录时间 |
| Action 原文 | 原始动作名 |
| User | 操作用户 |
| Resource Type / Resource ID | 关联资源信息 |
| IP | 来源 IP |
| User Agent | 客户端标识 |
| Error | 错误信息 |
| `details` JSON | 附加详情数据 |

### 10.7 权限差异

当前版本中：

- 普通用户通常只能查看自己的审计日志。
- 管理员可以查看全局日志。

因此，普通用户即使能进入该页面，也不代表能看到全平台所有记录。

### 10.8 Export Logs 当前状态

页面中虽然已有 `Export Logs` 按钮，但当前版本应视为占位能力：

- 按钮已存在。
- 当前版本暂未提供真正可用的导出结果。

手册使用时建议明确说明：

> 当前版本暂不提供可用的审计日志导出文件，请以页面筛选和详情查看为主。

### 10.9 常见 `Action` 含义

下表列出常见动作名及其大致含义：

| Action | 含义 |
| --- | --- |
| `skill.create` | 创建技能 |
| `skill.update` | 更新技能 |
| `skill.call` | 调用技能 |
| `resource.create` | 创建资源 |
| `acl.update` | 更新 ACL 规则 |
| `api_key.rotate` | 轮换 API key |
| `gateway.request` | 网关发起请求 |
| `gateway.proxy` | 网关执行代理转发 |

## 11. 常见限制与注意事项

以下内容是当前版本最需要提前告知用户的注意事项：

1. ACL 的 `role_bindings` 后端已支持，但当前前端没有编辑入口。
2. `Export Logs` 按钮当前未实现真正的导出能力。
3. API Key 前端创建弹窗未开放 `tokens:read`、`tokens:write` scopes。
4. `gateway`、`third` 的 `timeout` 按秒配置，`mcp` 的 `timeout` 按毫秒配置。
5. Skill 名称由 `content` 中 YAML frontmatter 的 `name` 决定，不由表单直接输入决定。
6. MCP 当前更建议使用 `sse` 或 `httpstream`，`stdio`、`ws` 虽可见但当前不建议依赖。
7. API key 完整值只在创建或轮换成功后展示一次，关闭后无法再次查看。
8. `Settings` 是双 tab 容器页，不是独立单功能页面。
9. `Visibility` 的前端初始表现值和后端默认值可能不完全一致，创建资源时建议显式确认。

## 12. 附录：字段速查表

### 12.1 业务对象字段速查

#### 12.1.1 Resource

| 字段 | 说明 |
| --- | --- |
| `Name` | 资源名称 |
| `Type` | `gateway` / `third` / `mcp` |
| `URL` | 资源地址 |
| `Description` | 资源用途说明 |
| `Visibility` | 可见范围 |
| `API Documentation` | 文档说明 |
| `Extended Properties (JSON)` | 扩展配置 |

#### 12.1.2 ACL Rule

| 字段 | 说明 |
| --- | --- |
| `Resource` | 被控制的资源 |
| `Access Mode` | `any` / `rbac` |
| `Conditions JSON` | 条件限制 JSON |

#### 12.1.3 Token

| 字段 | 说明 |
| --- | --- |
| `app_name` | 业务分组 |
| `key_name` | 引用名 |
| `value` | 密钥值 |
| `desc` | 说明 |

#### 12.1.4 Skill

| 字段 | 说明 |
| --- | --- |
| `Skill Name` | 只读展示位，真实值来自 frontmatter |
| `description` | 技能描述 |
| `category` | 分类 |
| `tags` | 标签 |
| `version` | 版本 |
| `content` | 技能正文与 frontmatter |

### 12.2 Settings 字段速查

#### 12.2.1 API Key

| 字段 | 说明 |
| --- | --- |
| `Key Name` | key 名称 |
| `Expiration` | 过期策略 |
| `Permissions (Scopes)` | 权限范围 |
| `key_prefix` | key 前缀 |
| `expires_at` | 到期时间 |
| `last_used_at` | 最近使用时间 |
| `is_active` | 是否有效 |

#### 12.2.2 Audit Log 筛选字段

| 字段 | 说明 |
| --- | --- |
| `User ID / Username` | 用户筛选 |
| `Resource Type` | 资源类型筛选 |
| `Status` | 状态筛选 |
| `From` | 起始时间 |
| `To` | 截止时间 |
| `Action` | 动作筛选 |
| `Resource ID` | 资源标识筛选 |

### 12.3 典型 JSON 片段速查

#### 12.3.1 `ext` 示例

```json
{
  "method": "POST",
  "headers": {
    "Authorization": "Bearer {vendor_token}",
    "Content-Type": "application/json"
  },
  "timeout": 15
}
```

#### 12.3.2 ACL `conditions` 示例

```json
{
  "roles": ["admin", "ops"],
  "rate_limit": {
    "requests": 60,
    "window": "1m"
  },
  "ip_whitelist": ["10.0.0.10"]
}
```

#### 12.3.3 Skill frontmatter 示例

```yaml
---
name: weekly-report-assistant
description: 汇总周报输入并生成结构化周报草稿
---
```

---

如需将本文档用于正式交付，建议在每次前端页面字段、弹窗标题或权限策略变更后同步复核本手册内容。
