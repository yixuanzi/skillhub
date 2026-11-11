# SkillHub 产品需求文档 (PRD)

**文档版本**: v1.0  
**创建日期**: 2024-02-27  
**维护者**: traceless G

---

## 📋 目录

- [产品概述](#产品概述)
- [核心功能](#核心功能)
- [资源类型](#资源类型)
- [用户角色与权限](#用户角色与权限)
- [使用场景](#使用场景)
- [技术要求](#技术要求)
- [里程碑规划](#里程碑规划)

---

## 产品概述

### 产品定位

SkillHub 是一个**企业级内部技能生态系统平台**，旨在为企业提供统一的技能构建、发布和调用管理能力。

### 核心价值

1. **统一管理**：集中管理企业内部的所有技能和 API 资源
2. **安全可控**：精细化的访问控制和权限管理
3. **快速集成**：支持 Dify/n8n 等低代码平台快速构建 API
4. **标准化流程**：规范化的技能构建和发布流程

### 目标用户

- **开发团队**：构建和发布内部技能
- **业务团队**：使用内部技能支持业务流程
- **运维团队**：管理技能调用和资源分配
- **安全团队**：配置访问控制策略

---

## 核心功能

### 1. Internal Skill Build & Publish（内部技能构建与发布）

#### 1.1 功能描述

提供完整的技能生命周期管理，从代码开发到生产发布的全流程支持。

#### 1.2 构建流程（Build）

```
代码上传 → 代码验证 → 依赖解析 → 构建执行 → 测试验证 → 产物打包
```

**核心能力**：

| 功能 | 描述 |
|------|------|
| 代码管理 | 支持 Git 仓库、ZIP 包上传 |
| 代码验证 | 语法检查、安全扫描、依赖审计 |
| 依赖管理 | 自动解析和安装依赖包 |
| 多运行时 | 支持 Node.js, Python, Go |
| 测试验证 | 单元测试、集成测试 |
| 产物打包 | Docker 镜像、无服务器函数 |

**技能类型**：

- **业务逻辑函数**：数据验证、格式转换、计算逻辑
- **API 代理**：第三方 API 封装和代理
- **AI/LLM 能力**：文本生成、摘要、翻译
- **数据处理**：数据清洗、统计分析、报表生成

#### 1.3 发布流程（Publish）

```
版本检查 → 版本号生成 → 元数据更新 → 环境部署 → 健康检查 → 发布完成
```

**核心能力**：

| 功能 | 描述 |
|------|------|
| 版本控制 | 语义化版本（SemVer）管理 |
| 元数据管理 | 技能描述、参数定义、返回值 Schema |
| 环境隔离 | 开发、测试、生产环境 |
| 灰度发布 | 金丝雀发布、蓝绿部署 |
| 回滚机制 | 一键回滚到历史版本 |

#### 1.4 关键指标

- **构建成功率**: ≥ 95%
- **平均构建时间**: < 5 分钟
- **发布可用性**: 99.9%

---

### 2. Gateway Call（网关调用）

#### 2.1 功能描述

SkillHub 作为所有内部技能调用的统一入口，提供统一的 API 接口、请求路由和负载均衡能力。

#### 2.2 架构设计

```
┌──────────────┐
│   客户端      │
└──────┬───────┘
       │
┌──────▼───────────────────────────────────┐
│        SkillHub Gateway                   │
│  ┌────────────────────────────────────┐  │
│  │  认证（JWT Token 验证）            │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  ACL 权限检查（any / RBAC）        │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  资源路由                          │  │
│  │  • 内部托管 API                    │  │
│  │  • 内部独立 API                    │  │
│  │  • 第三方 API URL                  │  │
│  └────────────────────────────────────┘  │
└──────┬───────────────────────────────────┘
       │
┌──────▼───────────────────────────────────┐
│         后端资源服务                      │
└──────────────────────────────────────────┘
```

#### 2.3 统一 API 接口

**快速构建平台集成**：
- **Dify**: 用于 LLM 能力和 AI 工作流编排
- **n8n**: 用于自动化工作流和 API 集成

**请求格式**：

```json
{
  "skillId": "weather-forecast",
  "version": "1.2.0",
  "params": {
    "city": "Beijing",
    "days": 3
  },
  "context": {
    "requestId": "req-12345",
    "traceId": "trace-67890"
  }
}
```

**响应格式**：

```json
{
  "success": true,
  "data": {
    "forecast": [...]
  },
  "metadata": {
    "executionTime": 150,
    "version": "1.2.0",
    "cached": false
  },
  "requestId": "req-12345"
}
```

#### 2.4 托管应用令牌（Managed App Token）

**流程设计**：

```
┌──────────┐
│ 应用系统  │
└─────┬────┘
      │ 1. 调用请求 (携带 App ID + App Secret)
      ▼
┌─────────────────────┐
│  SkillHub Gateway   │
└─────┬───────────────┘
      │ 2. 验证 App 凭证
      ▼
┌──────────────────────┐
│  Token 管理器         │
│  • 生成资源 Token     │
│  • 缓存 Token         │
└─────┬────────────────┘
      │ 3. 返回托管应用令牌
      ▼
┌──────────────────────┐
│  资源服务             │
│  (内部 API / 第三方)  │
└──────────────────────┘
```

**令牌类型**：

| 令牌类型 | 用途 | 有效期 | 管理方式 |
|---------|------|--------|---------|
| App Token | 应用系统访问网关 | 15 分钟 | 自动刷新 |
| Resource Token | 访问具体资源 | 1 小时 | 托管管理 |
| Third-party Token | 访问第三方 API | 根据提供方 | 加密存储 |

**关键特性**：
- 每类资源拥有独立 API 调用入口
- Token 自动刷新和续期
- Token 加密存储和传输
- Token 撤销和黑名单机制

#### 2.5 关键指标

- **API 可用性**: 99.9%
- **响应时间 (P99)**: < 200ms
- **吞吐量**: > 10,000 QPS

---

### 3. Call ACL（调用访问控制列表）

#### 3.1 功能描述

网关在处理调用请求时，严格检查预设的访问控制列表（ACL），实现精细化的权限管理。

#### 3.2 访问模式

##### 模式 1: Any（任意访问）

**适用场景**：
- 公开 API
- 内部公共服务
- 无敏感数据的资源

**配置示例**：

```yaml
resource: public-weather-api
accessMode: any
conditions:
  - rateLimit: 100/minute
  - ipWhitelist:
      - 10.0.0.0/8
      - 192.168.0.0/16
```

##### 模式 2: RBAC（基于角色的访问控制）

**适用场景**：
- 敏感数据访问
- 特权操作
- 需要审批的流程

**配置示例**：

```yaml
resource: internal-payment-api
accessMode: rbac
conditions:
  users: [alice, bob]            # 用户名白名单
  roles: [admin, payment-team]   # 角色白名单：内置角色或自定义角色，写名称或 ID 均可
roleBindings:                    # 也可以通过角色绑定授权，效果与角色白名单相同
  - role: payment-ops
```

命中用户白名单、角色白名单、角色绑定中的任意一项即允许调用，否则拒绝。新建资源时系统会自动生成一条 RBAC 规则，并把创建者加入用户白名单。

#### 3.3 ACL 规则结构

```typescript
interface ACLRule {
  id: string;
  resourceId: string;            // 资源标识
  resourceName: string;          // 资源名称
  accessMode: 'any' | 'rbac';    // 访问模式
  
  // RBAC 配置（仅当 accessMode = 'rbac'）
  rbacConfig?: {
    roles: RolePermission[];
    defaultRole?: string;
  };
  
  // 附加条件
  conditions?: {
    rateLimit?: string;          // 例如: "100/minute"
    ipWhitelist?: string[];      // IP 白名单
    timeWindow?: {               // 时间窗口限制
      start: string;             // 例如: "09:00"
      end: string;               // 例如: "18:00"
    };
    customRules?: string[];      // 自定义规则
  };
  
  // 生效时间
  effectiveFrom?: Date;
  effectiveUntil?: Date;
}
```

> **现状说明**：当前实现只判断“调用者是否被这条规则授权”。`rateLimit`、`ipWhitelist`、`timeWindow` 等附加条件，以及角色绑定上的 `permissions` 字段，可以保存但尚未生效；`effectiveFrom` / `effectiveUntil`、审批流程未实现。

#### 3.4 权限检查流程

```
请求到达
    ↓
提取请求信息 (用户、资源、操作)
    ↓
查找 ACL 规则
    ↓
判断访问模式
    ├─ 没有规则 → 拒绝
    ├─ Any → 允许（调用者需已登录）
    └─ RBAC → 用户白名单 / 角色白名单 / 角色绑定，命中任意一项 → 允许，否则拒绝
    ↓
记录审计日志
    ↓
返回结果
```

#### 3.5 审计日志

所有访问请求都会记录审计日志：

```typescript
interface AccessAuditLog {
  timestamp: Date;
  userId: string;
  resourceId: string;
  accessMode: 'any' | 'rbac';
  result: 'allow' | 'deny';
  reason?: string;
  ipAddress: string;
  userAgent: string;
  requestId: string;
}
```

---

## 资源类型

SkillHub 平台支持两类核心资源：

### 资源分类

```
SkillHub 资源
├── 内部资源
│   ├── 内部托管 API（SkillHub 托管的技能）
│   └── 内部独立 API（企业内部独立服务）
└── 外部资源
    └── 第三方 API URL（外部服务接口）
```

### 资源类型 1: 内部托管 API

**定义**: 完全由 SkillHub 平台托管和运行的技能 API。

**特点**:
- 由 SkillHub 构建和发布
- 运行在 SkillHub 的运行时环境中
- 生命周期完全由平台管理
- 支持版本控制和灰度发布

**示例**:
```yaml
resource:
  type: internal_hosted
  skillId: data-validation
  version: 1.0.0
  runtime: nodejs
  endpoint: /api/v1/skills/data-validation/invoke
```

**调用流程**:
```
客户端 → SkillHub Gateway → ACL 检查 → Skill Runtime → 返回结果
```

---

### 资源类型 2: 内部独立 API

**定义**: 企业内部独立部署的服务，通过 SkillHub 进行统一管理和调用。

**特点**:
- 独立部署和运行
- SkillHub 作为代理网关
- 统一的认证和授权
- 统一的监控和日志

**示例**:
```yaml
resource:
  type: internal_standalone
  name: payment-service
  baseUrl: http://payment-service.internal:8080
  auth:
    type: api_key
    header: X-API-Key
  endpoints:
    - path: /api/payments
      methods: [GET, POST]
    - path: /api/payments/{id}
      methods: [GET, PUT, DELETE]
```

**调用流程**:
```
客户端 → SkillHub Gateway → ACL 检查 → Token 转换 → 内部服务 → 返回结果
```

---

### 资源类型 3: 第三方 API URL

**定义**: 外部第三方服务的 API，通过 SkillHub 进行统一代理和 Token 管理。

**特点**:
- 托管第三方 API 的认证凭证
- 统一的 Token 获取和刷新
- 请求和响应的转换
- 调用监控和限流

**示例**:
```yaml
resource:
  type: third_party
  name: openai-api
  baseUrl: https://api.openai.com/v1
  auth:
    type: oauth2
    tokenUrl: https://auth.openai.com/oauth/token
    clientId: ${OPENAI_CLIENT_ID}
    clientSecret: ${OPENAI_CLIENT_SECRET}
  endpoints:
    - path: /chat/completions
      methods: [POST]
      rateLimit: 60/minute
```

**调用流程**:
```
客户端 → SkillHub Gateway → ACL 检查 → 获取托管 Token → 第三方 API → 返回结果
```

---

### 资源管理对比

| 特性 | 内部托管 API | 内部独立 API | 第三方 API |
|------|-------------|-------------|-----------|
| 托管方式 | 完全托管 | 代理转发 | 代理转发 |
| 运行环境 | SkillHub Runtime | 独立服务 | 外部服务 |
| 认证管理 | 平台统一 | Token 转换 | Token 托管 |
| 版本控制 | ✅ | ❌ | ❌ |
| 灰度发布 | ✅ | ❌ | ❌ |
| 调用监控 | ✅ | ✅ | ✅ |
| ACL 控制 | ✅ | ✅ | ✅ |

---

## 用户角色与权限

### 4. 用户认证和 RBAC 权限设置

#### 4.1 用户认证

**登录流程**:

```
用户输入用户名/密码
    ↓
认证服务验证
    ↓
生成 JWT Token
    ├─ Access Token (60 分钟)
    └─ Refresh Token (7 天)
    ↓
返回 Token 给客户端
```

**JWT Token 结构**:

```json
{
  "sub": "user-123",
  "username": "john.doe",
  "exp": 1709053200
}
```

Token 中不携带角色，角色在每次请求时从数据库读取，因此调整角色后无需重新登录即可生效。

#### 4.2 角色模型

SkillHub 不使用权限矩阵。一次操作是否被允许，只取决于三个问题：

1. **是不是你的**：技能、资源、ACL 规则、API Key、托管令牌，由创建者自己管理。这是普通用户的全部规则。
2. **是不是管理员**：`admin` 和 `super_admin` 可以额外查看并管理他人的技能、资源和 ACL 规则，查看全部审计日志，管理用户和角色。
3. **能不能调用**：只看资源的 ACL 规则（见第 3 节），任何角色都没有调用特权，管理员也不例外。

**内置角色**:

| 角色名称 | 描述 | 说明 |
|---------|------|------|
| `super_admin` | 超级管理员 | 拥有 `admin` 的全部能力，并且可以管理 `super_admin` 账号 |
| `admin` | 管理员 | 有限的管理权限：不能授予 `super_admin` 角色，也不能编辑、删除 `super_admin` 账号或调整其角色 |
| `user` | 普通用户 | 每个账号的默认角色（注册、SSO 首次登录、管理员创建时自动赋予），只管理自己的东西 |

角色本身不带任何权限点。三个内置角色不能改名、删除，其名称也不能被新建角色占用。

**自定义角色**：管理员可以创建任意名称的角色并把用户加入其中。自定义角色不带来任何管理能力，唯一用途是在 ACL 规则里作为“一组用户”被授权调用某个资源。

#### 4.3 谁能做什么

| 操作 | `user` | `admin` | `super_admin` |
|------|--------|---------|---------------|
| 创建技能、资源、API Key、托管令牌 | ✅ | ✅ | ✅ |
| 查看技能 | 已发布的，以及自己创建的 | 全部 | 全部 |
| 查看资源 | public 的、自己创建的、ACL 授权给自己的 | 全部 | 全部 |
| 编辑、删除技能和资源 | 仅自己创建的 | 全部 | 全部 |
| 配置资源的 ACL 规则 | 仅自己资源的 | 全部 | 全部 |
| 调用资源 | 由该资源的 ACL 规则决定 | 同左，无特权 | 同左，无特权 |
| 管理 API Key、托管令牌 | 仅自己的 | 仅自己的 | 仅自己的 |
| 查看审计日志 | 仅自己的 | 全部 | 全部 |
| 管理用户（创建、编辑、停用、删除、分配角色） | ❌ | ✅，`super_admin` 账号除外 | ✅ |
| 授予或收回 `super_admin` 角色 | ❌ | ❌ | ✅ |
| 创建、改名、删除自定义角色 | ❌ | ✅ | ✅ |

没有归属人的资源（历史数据）只有管理员可以编辑和删除。

#### 4.4 资源的访问授权

谁可以调用某个资源，由资源的创建者（或管理员）在该资源的 ACL 规则中配置：

```yaml
resource:
  name: payment-api
  accessMode: rbac
  conditions:
    users: [alice]              # 直接授权给用户
    roles: [payment-team]       # 授权给一个角色下的所有用户
```

要让所有登录用户都能调用，把 `accessMode` 设为 `any`。把资源设为 public 只影响“能否看到”，不影响“能否调用”。

---

## 使用场景

### 场景 1: 开发者发布新技能

**角色**: 普通用户（技能的创建者）

**流程**:
```
1. 开发者编写技能代码
2. 通过 Web UI 或 CLI 上传代码到 SkillHub
3. SkillHub 自动构建和测试
4. 测试通过后，开发者发布到测试环境
5. QA 验证通过后，开发者发布到生产环境
6. 创建者（或管理员）配置 ACL 规则，控制访问权限
```

**ACL 配置**:
```yaml
resource: new-skill-api
accessMode: rbac
conditions:
  roles: [tester, ops-team]   # 自定义角色
```

---

### 场景 2: 业务系统调用技能

**角色**: 应用系统

**流程**:
```
1. 应用系统使用 App ID + Secret 调用网关
2. 网关验证 App 凭证
3. ACL 检查 App 是否有权限访问该资源
4. 获取托管的应用令牌
5. 使用令牌调用实际的资源服务
6. 返回结果给应用系统
```

**ACL 配置**:
```yaml
resource: business-logic-api
accessMode: any
conditions:
  - rateLimit: 1000/hour
  - ipWhitelist:
      - 10.0.0.0/8
```

---

### 场景 3: 管理员配置权限

**角色**: 系统管理员 (admin)

**流程**:
```
1. 管理员登录管理后台
2. 创建自定义角色 "data_analyst"
3. 将用户分配到该角色
4. 在需要开放的资源的 ACL 规则中授权该角色
```

**ACL 配置**:
```yaml
resource: data-analysis-api
accessMode: rbac
conditions:
  roles: [data_analyst]
```

---

### 场景 4: 集成第三方 API

**角色**: 系统管理员 (admin)

**流程**:
```
1. 管理员在 SkillHub 中添加第三方 API 配置
2. 配置认证信息（OAuth2、API Key 等）
3. 配置 ACL 规则
4. 开发者在 SkillHub 中使用该第三方 API
5. SkillHub 自动管理 Token 的获取和刷新
```

**配置示例**:
```yaml
resource:
  type: third_party
  name: salesforce-api
  baseUrl: https://api.salesforce.com
  auth:
    type: oauth2
    tokenUrl: https://login.salesforce.com/oauth/token
    clientId: ${SF_CLIENT_ID}
    clientSecret: ${SF_CLIENT_SECRET}
  acl:
    accessMode: rbac
    roles:
      - name: crm_integration
        permissions: [read, write]
```

---

## 技术要求

### 性能要求

| 指标 | 要求 |
|------|------|
| API 响应时间 (P99) | < 200ms |
| 技能调用吞吐量 | > 10,000 QPS |
| 系统可用性 | 99.9% |
| 构建成功率 | ≥ 95% |
| 平均构建时间 | < 5 分钟 |

### 安全要求

- 所有通信使用 TLS 1.3
- JWT Token 有效期：15 分钟
- Refresh Token 有效期：7 天
- 密码存储：bcrypt 哈希
- 敏感数据加密存储
- 完整的审计日志

### 可扩展性要求

- 支持水平扩展
- 无状态服务设计
- 数据库读写分离
- 多级缓存策略

---

## 里程碑规划

### Phase 1: MVP（4 周）

**目标**: 基础功能可用

- [ ] 用户认证和 JWT Token 管理
- [ ] 基础的角色体系（super_admin / admin / user）
- [ ] 技能构建和发布（支持 Node.js）
- [ ] 简单的网关调用
- [ ] ACL 规则管理（Any 模式）
- [ ] 基础的 Web 管理界面

### Phase 2: 核心功能完善（4 周）

**目标**: 核心功能完整

- [ ] 完整的 ACL 规则管理（RBAC 模式）
- [ ] 技能版本控制和灰度发布
- [ ] 内部独立 API 资源支持
- [ ] Dify 平台集成
- [ ] 托管应用令牌管理
- [ ] 审计日志和监控

### Phase 3: 高级功能（4 周）

**目标**: 增强平台能力

- [ ] 第三方 API URL 资源支持
- [ ] n8n 平台集成
- [ ] 高级 ACL 条件（时间窗口、自定义规则）
- [ ] 技能市场 UI
- [ ] SDK 和 CLI 工具
- [ ] 性能优化

### Phase 4: 企业级特性（4 周）

**目标**: 生产环境就绪

- [ ] 多租户支持
- [ ] 高可用部署
- [ ] 灾备和备份
- [ ] 安全加固
- [ ] 性能测试和优化
- [ ] 文档完善

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Skill | 技能，封装了特定业务逻辑或功能的可调用单元 |
| ACL | Access Control List，访问控制列表 |
| RBAC | Role-Based Access Control，基于角色的访问控制 |
| JWT | JSON Web Token，用于身份认证的令牌 |
| Dify | 低代码 AI 应用开发平台 |
| n8n | 开源的工作流自动化工具 |

### B. 相关文档

- [系统架构设计](./architecture.md)
- [核心模块设计](./modules.md)
- [API 接口设计](./api-design.md)
- [数据模型设计](./data-model.md)
- [安全设计](./security.md)
- [技术栈选型](./tech-stack.md)

---

**文档历史**:

| 版本 | 日期 | 修改人 | 修改内容 |
|------|------|--------|----------|
| v1.0 | 2024-02-27 | traceless G | 初始版本 |

---

*本文档由 小黑 🐕 协助创建*
