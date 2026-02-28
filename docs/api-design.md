# SkillHub API 设计文档 (MVP)

## 1. 概述

本文档描述 SkillHub MVP 的 RESTful API 设计。所有 API 端点遵循统一的请求/响应格式，使用 JWT Token 进行身份认证。

### 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://localhost:8000/api/v1` |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | JWT Bearer Token |

### API 文档

FastAPI 自动生成交互式 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 2. 统一响应格式

### 2.1 成功响应

```json
{
  "success": true,
  "data": { ... }
}
```

或直接返回数据对象。

### 2.2 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  }
}
```

### 2.3 标准 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | OK - 请求成功 |
| 201 | Created - 资源创建成功 |
| 204 | No Content - 删除成功 |
| 400 | Bad Request - 请求参数错误 |
| 401 | Unauthorized - 未认证或 Token 无效 |
| 403 | Forbidden - 无权限访问 |
| 404 | Not Found - 资源不存在 |
| 409 | Conflict - 资源冲突（如重复创建） |
| 422 | Unprocessable Entity - 验证失败 |
| 500 | Internal Server Error - 服务器错误 |

---

## 3. 认证 API

### 3.1 用户注册

**端点**: `POST /auth/register`

**请求**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**响应** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2025-02-28T10:00:00Z"
}
```

### 3.2 用户登录

**端点**: `POST /auth/login`

**请求**:
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3.3 刷新 Token

**端点**: `POST /auth/refresh`

**请求**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3.4 登出

**端点**: `POST /auth/logout`

**请求头**: `Authorization: Bearer {access_token}`

**请求**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应** (204)

### 3.5 获取当前用户信息

**端点**: `GET /auth/me`

**请求头**: `Authorization: Bearer {access_token}`

**响应** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "roles": [
    {"id": "...", "name": "developer"}
  ],
  "created_at": "2025-02-28T10:00:00Z"
}
```

---

## 4. 用户管理 API

### 4.1 列出用户

**端点**: `GET /users`

**请求头**: `Authorization: Bearer {access_token}`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| size | int | 否 | 每页数量，默认 20 |
| search | str | 否 | 搜索关键词 |

**响应** (200):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "email": "john@example.com",
      "roles": [{"name": "developer"}],
      "is_active": true,
      "created_at": "2025-02-28T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

### 4.2 创建用户

**端点**: `POST /users`

**权限**: 仅管理员

**请求**:
```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "SecurePassword123!",
  "role_ids": ["role-id-1"]
}
```

**响应** (201):
```json
{
  "id": "...",
  "username": "jane_doe",
  "email": "jane@example.com",
  "created_at": "2025-02-28T11:00:00Z"
}
```

### 4.3 获取用户详情

**端点**: `GET /users/{id}`

**响应** (200):
```json
{
  "id": "...",
  "username": "john_doe",
  "email": "john@example.com",
  "roles": [
    {"id": "...", "name": "developer", "description": "..."}
  ],
  "is_active": true,
  "created_at": "2025-02-28T10:00:00Z"
}
```

### 4.4 更新用户

**端点**: `PUT /users/{id}`

**请求**:
```json
{
  "email": "newemail@example.com",
  "role_ids": ["role-id-1", "role-id-2"]
}
```

**响应** (200): 返回更新后的用户信息

### 4.5 删除用户

**端点**: `DELETE /users/{id}`

**权限**: 仅超级管理员

**响应** (204)

---

## 5. 角色管理 API

### 5.1 列出角色

**端点**: `GET /roles`

**响应** (200):
```json
{
  "items": [
    {
      "id": "...",
      "name": "developer",
      "description": "Can build and publish skills",
      "permissions": [
        {"resource": "skills", "action": "read"},
        {"resource": "skills", "action": "write"}
      ]
    }
  ]
}
```

### 5.2 创建角色

**端点**: `POST /roles`

**权限**: 仅管理员

**请求**:
```json
{
  "name": "data_analyst",
  "description": "Data analysis role",
  "permission_ids": ["perm-1", "perm-2"]
}
```

**响应** (201)

### 5.3 更新角色

**端点**: `PUT /roles/{id}`

**请求**:
```json
{
  "description": "Updated description",
  "permission_ids": ["perm-1", "perm-2", "perm-3"]
}
```

**响应** (200)

### 5.4 删除角色

**端点**: `DELETE /roles/{id}`

**权限**: 仅管理员

**响应** (204)

---

## 6. 技能管理 API

### 6.1 列出技能

**端点**: `GET /skills`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| size | int | 否 | 每页数量 |
| type | str | 否 | 技能类型过滤 |
| search | str | 否 | 搜索关键词 |

**响应** (200):
```json
{
  "items": [
    {
      "id": "...",
      "name": "weather-forecast",
      "description": "Get weather forecast",
      "skill_type": "business_logic",
      "runtime": "python",
      "created_by": "john_doe",
      "latest_version": "1.0.0",
      "created_at": "2025-02-28T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

### 6.2 创建技能

**端点**: `POST /skills`

**请求**:
```json
{
  "name": "weather-forecast",
  "description": "Get weather forecast for a city",
  "skill_type": "business_logic"
}
```

**响应** (201):
```json
{
  "id": "...",
  "name": "weather-forecast",
  "description": "Get weather forecast for a city",
  "skill_type": "business_logic",
  "runtime": "python",
  "created_by": "...",
  "created_at": "2025-02-28T10:00:00Z"
}
```

### 6.3 获取技能详情

**端点**: `GET /skills/{id}`

**响应** (200):
```json
{
  "id": "...",
  "name": "weather-forecast",
  "description": "Get weather forecast for a city",
  "skill_type": "business_logic",
  "runtime": "python",
  "created_by": "john_doe",
  "versions": [
    {
      "id": "...",
      "version": "1.0.0",
      "status": "published",
      "published_at": "2025-02-28T11:00:00Z"
    }
  ],
  "created_at": "2025-02-28T10:00:00Z"
}
```

### 6.4 构建技能

**端点**: `POST /skills/{id}/build`

**请求**: `multipart/form-data`
```
code_file: <Python file>
requirements_file: <requirements.txt>
version: "1.0.0"
```

**响应** (200):
```json
{
  "version_id": "...",
  "skill_id": "...",
  "version": "1.0.0",
  "status": "draft",
  "artifact_path": "/artifacts/weather-forecast-1.0.0.zip",
  "build_log": "Build successful",
  "created_at": "2025-02-28T10:30:00Z"
}
```

### 6.5 发布技能

**端点**: `POST /skills/{id}/publish`

**请求**:
```json
{
  "version": "1.0.0"
}
```

**响应** (200):
```json
{
  "id": "...",
  "skill_id": "...",
  "version": "1.0.0",
  "status": "published",
  "published_at": "2025-02-28T11:00:00Z"
}
```

### 6.6 列出版本

**端点**: `GET /skills/{id}/versions`

**响应** (200):
```json
{
  "items": [
    {
      "id": "...",
      "version": "1.0.0",
      "status": "published",
      "published_at": "2025-02-28T11:00:00Z",
      "created_at": "2025-02-28T10:30:00Z"
    },
    {
      "id": "...",
      "version": "0.9.0",
      "status": "draft",
      "created_at": "2025-02-27T15:00:00Z"
    }
  ]
}
```

### 6.7 调用技能 (直接)

**端点**: `POST /skills/{id}/invoke`

**请求**:
```json
{
  "version": "1.0.0",
  "params": {
    "city": "Beijing",
    "days": 3
  }
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "city": "Beijing",
    "forecast": [...]
  },
  "metadata": {
    "execution_time": 150,
    "version": "1.0.0"
  }
}
```

---

## 7. 技能市场 API

### 7.1 创建技能

**端点**: `POST /skills`

**请求**:
```json
{
  "name": "string (1-255, required)",
  "description": "string (optional, max 10000)",
  "content": "string (optional, max 100000)",
  "created_by": "string (1-255, required)",
  "category": "string (optional, max 100)",
  "tags": "string (optional, comma-separated, max 500)",
  "version": "string (optional, default '1.0.0')"
}
```

**响应** (201): 返回创建的技能对象

### 7.2 列出技能

**端点**: `GET /skills`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| size | int | 否 | 每页数量，默认 20，最大 100 |
| category | str | 否 | 按类别过滤 |
| tags | str | 否 | 按标签过滤（逗号分隔） |
| author | str | 否 | 按创建者用户 ID 过滤 |

**响应** (200): 返回分页的技能列表

### 7.3 获取技能详情

**端点**: `GET /skills/{id}`

**响应** (200): 返回技能对象

**响应** (404): 技能不存在

### 7.4 更新技能

**端点**: `PUT /skills/{id}`

**请求**: 所有字段可选
```json
{
  "name": "string (1-255, optional)",
  "description": "string (optional, max 10000)",
  "content": "string (optional, max 100000)",
  "category": "string (optional, max 100)",
  "tags": "string (optional, comma-separated, max 500)"
}
```

**响应** (200): 返回更新后的技能对象

**响应** (404): 技能不存在

### 7.5 删除技能

**端点**: `DELETE /skills/{id}`

**响应** (204): 删除成功

**响应** (404): 技能不存在

---

## 8. ACL 管理 API

### 8.1 列出 ACL 规则

**端点**: `GET /acl/rules`

**响应** (200):
```json
{
  "items": [
    {
      "id": "...",
      "resource_id": "weather-forecast",
      "resource_name": "Weather Forecast API",
      "access_mode": "any",
      "conditions": {
        "rateLimit": "100/minute"
      },
      "created_at": "2025-02-28T10:00:00Z"
    }
  ]
}
```

### 8.2 创建 ACL 规则

**端点**: `POST /acl/rules`

**请求** (Any 模式):
```json
{
  "resource_id": "weather-forecast",
  "resource_name": "Weather Forecast API",
  "access_mode": "any",
  "conditions": {
    "rateLimit": "100/minute",
    "ipWhitelist": ["10.0.0.0/8"]
  }
}
```

**请求** (RBAC 模式):
```json
{
  "resource_id": "payment-api",
  "resource_name": "Payment API",
  "access_mode": "rbac",
  "roles": [
    {
      "role_id": "admin",
      "permissions": ["read", "write", "delete"]
    },
    {
      "role_id": "operator",
      "permissions": ["read", "write"]
    }
  ],
  "conditions": {
    "rateLimit": "50/minute"
  }
}
```

**响应** (201)

### 8.3 获取 ACL 规则详情

**端点**: `GET /acl/rules/{id}`

**响应** (200):
```json
{
  "id": "...",
  "resource_id": "payment-api",
  "resource_name": "Payment API",
  "access_mode": "rbac",
  "roles": [...],
  "conditions": {...},
  "created_at": "2025-02-28T10:00:00Z"
}
```

### 8.4 更新 ACL 规则

**端点**: `PUT /acl/rules/{id}`

**请求**: 同创建规则

**响应** (200)

### 8.5 删除 ACL 规则

**端点**: `DELETE /acl/rules/{id}`

**响应** (204)

### 8.6 查询审计日志

**端点**: `GET /acl/audit-logs`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | str | 否 | 用户 ID 过滤 |
| resource_id | str | 否 | 资源 ID 过滤 |
| result | str | 否 | 结果过滤 (allow/deny) |
| start_time | str | 否 | 开始时间 |
| end_time | str | 否 | 结束时间 |
| page | int | 否 | 页码 |
| size | int | 否 | 每页数量 |

**响应** (200):
```json
{
  "items": [
    {
      "id": "...",
      "timestamp": "2025-02-28T12:00:00Z",
      "user_id": "...",
      "username": "john_doe",
      "resource_id": "weather-forecast",
      "access_mode": "any",
      "result": "allow",
      "ip_address": "10.0.0.1",
      "request_id": "req-12345"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

---

## 9. 网关 API

### 9.1 统一调用入口

**端点**: `POST /gateway/call`

**请求头**: `Authorization: Bearer {access_token}`

**请求**:
```json
{
  "skillId": "weather-forecast",
  "version": "1.0.0",
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

**响应** (成功 - 200):
```json
{
  "success": true,
  "data": {
    "city": "Beijing",
    "forecast": [
      {"date": "2025-03-01", "temp": 15, "condition": "sunny"},
      {"date": "2025-03-02", "temp": 18, "condition": "cloudy"}
    ]
  },
  "metadata": {
    "executionTime": 150,
    "version": "1.0.0",
    "cached": false
  },
  "requestId": "req-12345"
}
```

**响应** (权限拒绝 - 403):
```json
{
  "success": false,
  "error": {
    "code": "ACCESS_DENIED",
    "message": "You do not have permission to access this resource"
  },
  "requestId": "req-12345"
}
```

**响应** (技能不存在 - 404):
```json
{
  "success": false,
  "error": {
    "code": "SKILL_NOT_FOUND",
    "message": "Skill 'weather-forecast' not found"
  },
  "requestId": "req-12345"
}
```

**响应** (执行错误 - 500):
```json
{
  "success": false,
  "error": {
    "code": "SKILL_EXECUTION_ERROR",
    "message": "Skill execution failed",
    "details": {
      "error": "TypeError: unsupported operand type(s)"
    }
  },
  "requestId": "req-12345"
}
```

---

## 10. 错误码参考

| 错误码 | HTTP 状态 | 说明 |
|--------|----------|------|
| `AUTH_FAILED` | 401 | 认证失败 |
| `INVALID_TOKEN` | 401 | Token 无效或过期 |
| `TOKEN_EXPIRED` | 401 | Token 已过期 |
| `ACCESS_DENIED` | 403 | 访问被拒绝 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `SKILL_NOT_FOUND` | 404 | 技能不存在 |
| `DUPLICATE_USERNAME` | 409 | 用户名已存在 |
| `DUPLICATE_EMAIL` | 409 | 邮箱已存在 |
| `DUPLICATE_SKILL_NAME` | 409 | 技能名称已存在 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `BUILD_FAILED` | 422 | 技能构建失败 |
| `SKILL_EXECUTION_ERROR` | 500 | 技能执行错误 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |

---

## 11. 分页规范

所有列表 API 支持统一分页参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码（从 1 开始） |
| size | int | 20 | 每页数量（最大 100） |

**分页响应格式**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

## 12. 认证说明

### 12.1 Token 使用

在请求头中添加 JWT Token：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 12.2 Token 刷新

当 Access Token 过期时，使用 Refresh Token 获取新的 Access Token：

```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
```

### 12.3 需要 Token 的端点

除 `/auth/register` 和 `/auth/login` 外，所有端点都需要有效的 JWT Token。

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
