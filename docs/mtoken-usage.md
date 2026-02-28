# MToken Token托管模块 - 使用文档

## 概述

MToken 模块允许用户在平台上安全地存储和管理第三方 API token 令牌，支持完整的增删改查操作。

## 数据库表结构

### 表名: `mtoken`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | String(36) | PRIMARY KEY, UUID | 唯一标识符 |
| app_name | String(255) | NOT NULL, INDEX | 应用名称（如 GitHub, OpenAI） |
| key_name | String(255) | NOT NULL, INDEX | 密钥名称（如 API Key, Token） |
| value | Text | NOT NULL | 密钥值（敏感信息） |
| desc | Text | NULLABLE | 描述信息 |
| created_by | String(36) | FOREIGN KEY, INDEX, NOT NULL | 创建用户ID |
| created_at | DateTime | DEFAULT NOW() | 创建时间 |
| updated_at | DateTime | DEFAULT NOW(), ON UPDATE | 最后更新时间 |

## API 端点

### 基础路径
`/api/v1/mtokens`

所有端点都需要 **JWT Token 或 TmpKey** 认证。

---

### 1. 创建 Token

**POST** `/api/v1/mtokens/`

创建一个新的托管 token。

**请求体:**
```json
{
  "app_name": "GitHub",
  "key_name": "Personal Access Token",
  "value": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "desc": "我的 GitHub API 访问令牌"
}
```

**响应:** `201 Created`
```json
{
  "id": "uuid-string",
  "app_name": "GitHub",
  "key_name": "Personal Access Token",
  "value": "ghp_xxxxxxxxxxxxxxxxxxxx",
  "desc": "我的 GitHub API 访问令牌",
  "created_by": "user-uuid",
  "created_at": "2025-02-28T10:00:00Z",
  "updated_at": "2025-02-28T10:00:00Z"
}
```

**字段验证:**
- `app_name`: 1-255 字符，必填
- `key_name`: 1-255 字符，必填
- `value`: 1-10000 字符，必填
- `desc`: 最多 10000 字符，可选

---

### 2. 列出所有 Token

**GET** `/api/v1/mtokens/`

获取当前用户的所有托管 token，支持分页和按应用名称过滤。

**查询参数:**
- `page` (可选): 页码，默认 1，最小值 1
- `size` (可选): 每页数量，默认 20，最大 100
- `app_name` (可选): 按应用名称过滤

**示例请求:**
```bash
# 获取第一页，每页20条
GET /api/v1/mtokens/

# 获取第二页，每页10条
GET /api/v1/mtokens/?page=2&size=10

# 只获取 GitHub 相关的 token
GET /api/v1/mtokens/?app_name=GitHub
```

**响应:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid-1",
      "app_name": "GitHub",
      "key_name": "Personal Access Token",
      "value": "ghp_xxx",
      "desc": "GitHub token",
      "created_by": "user-uuid",
      "created_at": "2025-02-28T10:00:00Z",
      "updated_at": "2025-02-28T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "app_name": "OpenAI",
      "key_name": "API Key",
      "value": "sk-xxx",
      "desc": "OpenAI token",
      "created_by": "user-uuid",
      "created_at": "2025-02-28T09:00:00Z",
      "updated_at": "2025-02-28T09:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 20
}
```

**重要:** 用户只能看到自己创建的 token（用户隔离）。

---

### 3. 获取单个 Token

**GET** `/api/v1/mtokens/{token_id}`

获取指定 ID 的 token。

**路径参数:**
- `token_id`: Token UUID

**响应:** `200 OK` (token 对象) 或 `404 Not Found`

**示例:**
```bash
GET /api/v1/mtokens/550e8400-e29b-41d4-a716-446655440000
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "app_name": "GitHub",
  "key_name": "Personal Access Token",
  "value": "ghp_xxx",
  "desc": "我的 GitHub token",
  "created_by": "user-uuid",
  "created_at": "2025-02-28T10:00:00Z",
  "updated_at": "2025-02-28T10:00:00Z"
}
```

**安全:** 只能获取自己创建的 token。

---

### 4. 更新 Token

**PUT** `/api/v1/mtokens/{token_id}`

更新指定的 token。所有字段都是可选的。

**路径参数:**
- `token_id`: Token UUID

**请求体:** 所有字段可选
```json
{
  "app_name": "GitHub",
  "key_name": "Updated Token Name",
  "value": "ghp_new_value",
  "desc": "更新的描述"
}
```

**响应:** `200 OK` (更新后的 token) 或 `404 Not Found`

**示例:**
```bash
PUT /api/v1/mtokens/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "value": "ghp_updated_xxxxxxxxxxxx"
}
```

**安全:** 只能更新自己创建的 token。

---

### 5. 删除 Token

**DELETE** `/api/v1/mtokens/{token_id}`

删除指定的 token。

**路径参数:**
- `token_id`: Token UUID

**响应:** `204 No Content` 或 `404 Not Found`

**示例:**
```bash
DELETE /api/v1/mtokens/550e8400-e29b-41d4-a716-446655440000
```

**安全:** 只能删除自己创建的 token。

---

## 使用示例

### cURL 示例

#### 1. 创建 Token
```bash
curl -X POST http://localhost:8000/api/v1/mtokens/ \
  -H "Authorization: Bearer <your_token_or_tmpkey>" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "OpenAI",
    "key_name": "API Key",
    "value": "sk-proj-xxxxxxxxxxxxxxxxxxx",
    "desc": "OpenAI GPT-4 API Key"
  }'
```

#### 2. 列出所有 Token
```bash
curl http://localhost:8000/api/v1/mtokens/ \
  -H "Authorization: Bearer <your_token_or_tmpkey>"
```

#### 3. 过滤特定应用的 Token
```bash
curl "http://localhost:8000/api/v1/mtokens/?app_name=GitHub" \
  -H "Authorization: Bearer <your_token_or_tmpkey>"
```

#### 4. 获取单个 Token
```bash
curl http://localhost:8000/api/v1/mtokens/<token_id> \
  -H "Authorization: Bearer <your_token_or_tmpkey>"
```

#### 5. 更新 Token
```bash
curl -X PUT http://localhost:8000/api/v1/mtokens/<token_id> \
  -H "Authorization: Bearer <your_token_or_tmpkey>" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "ghp_updated_xxxxxxxxxxxx",
    "desc": "更新后的描述"
  }'
```

#### 6. 删除 Token
```bash
curl -X DELETE http://localhost:8000/api/v1/mtokens/<token_id> \
  -H "Authorization: Bearer <your_token_or_tmpkey>"
```

---

### Python 示例

```python
import requests

API_BASE = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token_or_tmpkey"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. 创建 Token
token_data = {
    "app_name": "GitHub",
    "key_name": "Personal Access Token",
    "value": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "desc": "我的 GitHub token"
}
response = requests.post(f"{API_BASE}/mtokens/", json=token_data, headers=HEADERS)
token = response.json()
print(f"创建的 Token ID: {token['id']}")

# 2. 列出所有 Token
response = requests.get(f"{API_BASE}/mtokens/", headers=HEADERS)
tokens = response.json()
print(f"共有 {tokens['total']} 个 token:")
for t in tokens['items']:
    print(f"  - {t['app_name']}: {t['key_name']}")

# 3. 过滤特定应用的 Token
response = requests.get(f"{API_BASE}/mtokens/?app_name=GitHub", headers=HEADERS)
github_tokens = response.json()
print(f"GitHub token 数量: {github_tokens['total']}")

# 4. 获取单个 Token
token_id = token['id']
response = requests.get(f"{API_BASE}/mtokens/{token_id}", headers=HEADERS)
single_token = response.json()
print(f"Token 详情: {single_token}")

# 5. 更新 Token
update_data = {
    "value": "ghp_updated_xxxxxxxxxxxx",
    "desc": "更新后的描述"
}
response = requests.put(f"{API_BASE}/mtokens/{token_id}", json=update_data, headers=HEADERS)
updated_token = response.json()
print(f"更新后的 Token: {updated_token}")

# 6. 删除 Token
response = requests.delete(f"{API_BASE}/mtokens/{token_id}", headers=HEADERS)
print(f"删除状态: {response.status_code}")  # 应该是 204
```

---

### JavaScript/TypeScript 示例

```typescript
const API_BASE = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token_or_tmpkey';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// 1. 创建 Token
async function createToken() {
  const tokenData = {
    app_name: 'OpenAI',
    key_name: 'API Key',
    value: 'sk-proj-xxxxxxxxxxxxxxxxxxx',
    desc: 'OpenAI GPT-4 API Key'
  };

  const response = await fetch(`${API_BASE}/mtokens/`, {
    method: 'POST',
    headers,
    body: JSON.stringify(tokenData)
  });

  const token = await response.json();
  console.log('创建的 Token ID:', token.id);
  return token;
}

// 2. 列出所有 Token
async function listTokens() {
  const response = await fetch(`${API_BASE}/mtokens/`, {
    method: 'GET',
    headers
  });

  const result = await response.json();
  console.log(`共有 ${result.total} 个 token:`);
  result.items.forEach((t: any) => {
    console.log(`  - ${t.app_name}: ${t.key_name}`);
  });

  return result;
}

// 3. 过滤特定应用的 Token
async function filterByApp(appName: string) {
  const response = await fetch(`${API_BASE}/mtokens/?app_name=${appName}`, {
    method: 'GET',
    headers
  });

  const result = await response.json();
  console.log(`${appName} token 数量: ${result.total}`);
  return result;
}

// 4. 获取单个 Token
async function getToken(tokenId: string) {
  const response = await fetch(`${API_BASE}/mtokens/${tokenId}`, {
    method: 'GET',
    headers
  });

  const token = await response.json();
  console.log('Token 详情:', token);
  return token;
}

// 5. 更新 Token
async function updateToken(tokenId: string) {
  const updateData = {
    value: 'ghp_updated_xxxxxxxxxxxx',
    desc: '更新后的描述'
  };

  const response = await fetch(`${API_BASE}/mtokens/${tokenId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(updateData)
  });

  const updatedToken = await response.json();
  console.log('更新后的 Token:', updatedToken);
  return updatedToken;
}

// 6. 删除 Token
async function deleteToken(tokenId: string) {
  const response = await fetch(`${API_BASE}/mtokens/${tokenId}`, {
    method: 'DELETE',
    headers
  });

  console.log('删除状态:', response.status); // 应该是 204
  return response.status;
}
```

---

## 安全特性

### 1. **用户隔离**
- 用户只能看到、更新、删除自己创建的 token
- 通过 `created_by` 字段实现用户数据隔离
- 所有查询都自动过滤当前用户的 token

### 2. **认证要求**
- 所有 API 端点都需要认证
- 支持 JWT Token 和 TmpKey 两种认证方式
- 未认证的请求返回 `401 Unauthorized` 或 `403 Forbidden`

### 3. **权限控制**
- GET/PUT/DELETE 操作会验证 token 是否属于当前用户
- 尝试访问其他用户的 token 返回 `404 Not Found`
- 防止横向越权攻击

### 4. **输入验证**
- 所有字段都有长度限制
- `app_name` 和 `key_name` 必填
- `value` 必填（存储敏感信息）

---

## 常见使用场景

### 场景 1: 存储 GitHub Personal Access Token
```json
{
  "app_name": "GitHub",
  "key_name": "Personal Access Token",
  "value": "ghp_kxxxxxxxxxxxxxxxxxxxxxxxx",
  "desc": "用于 GitHub API 访问的 token"
}
```

### 场景 2: 存储 OpenAI API Key
```json
{
  "app_name": "OpenAI",
  "key_name": "API Key",
  "value": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "desc": "GPT-4 API Key，用于 AI 对话功能"
}
```

### 场景 3: 存储 Slack Bot Token
```json
{
  "app_name": "Slack",
  "key_name": "Bot Token",
  "value": "xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "desc": "Slack Bot Token，用于消息推送"
}
```

### 场景 4: 存储多个同一服务的不同 Token
```json
// Token 1 - 开发环境
{
  "app_name": "OpenAI",
  "key_name": "Dev API Key",
  "value": "sk-proj-dev-xxx",
  "desc": "开发环境 API Key"
}

// Token 2 - 生产环境
{
  "app_name": "OpenAI",
  "key_name": "Prod API Key",
  "value": "sk-proj-prod-xxx",
  "desc": "生产环境 API Key"
}
```

---

## 数据库初始化

运行表创建脚本：

```bash
cd backend
python scripts/create_mtoken_table.py
```

**输出:**
```
Creating mtoken table...
mtoken table created successfully!
```

---

## 错误处理

### 常见错误响应

#### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```
**原因:** 未提供认证 token 或 token 无效

#### 403 Forbidden
```json
{
  "detail": "Inactive user"
}
```
**原因:** 用户账户已被禁用

#### 404 Not Found
```json
{
  "detail": "Token with id 'xxx' not found"
}
```
**原因:**
- Token ID 不存在
- Token 属于其他用户（用户隔离）

#### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```
**原因:** 请求数据验证失败（字段长度、格式等）

---

## 索引优化

表中有以下索引用于查询优化：

1. `ix_mtoken_app_key` - 复合索引 `(app_name, key_name)`
   - 优化按应用和密钥名称的查询

2. `ix_mtoken_created_by` - 单列索引 `created_by`
   - 优化用户数据隔离查询
   - 加速用户专属 token 列表

---

## 测试

运行单元测试：
```bash
cd backend
pytest tests/test_mtoken_service.py -v
```

运行集成测试：
```bash
cd backend
pytest tests/test_mtoken_api.py -v
```

运行所有 mtoken 测试：
```bash
cd backend
pytest tests/test_mtoken*.py -v
```

---

## 注意事项

1. **敏感信息存储**:
   - `value` 字段目前以明文存储
   - 建议生产环境使用加密存储（可后续优化）

2. **Token 过期**:
   - Token 没有自动过期机制
   - 需要手动删除过期的 token

3. **Token 轮换**:
   - 更新 token 值后，旧值立即失效
   - 建议定期轮换敏感 token

4. **审计日志**:
   - 当前版本没有操作审计日志
   - 可通过数据库 `updated_at` 字段追踪修改时间

---

## 文件清单

### 新增文件
- `backend/models/mtoken.py` - 数据模型
- `backend/schemas/mtoken.py` - Pydantic schemas
- `backend/services/mtoken_service.py` - 业务逻辑层
- `backend/api/mtoken.py` - API 路由
- `backend/scripts/create_mtoken_table.py` - 数据库表创建脚本
- `backend/tests/test_mtoken_service.py` - 单元测试
- `backend/tests/test_mtoken_api.py` - 集成测试

### 修改文件
- `backend/models/__init__.py` - 添加 MToken 导入
- `backend/main.py` - 注册 mtoken 路由

---

## 总结

MToken 模块提供了完整的 token 托管功能：

✅ **安全性**: 用户隔离 + 认证要求
✅ **完整性**: CRUD 操作全覆盖
✅ **易用性**: RESTful API 设计
✅ **可扩展性**: 支持按应用过滤、分页
✅ **可靠性**: 全面的单元和集成测试

可以安全地用于存储各类第三方 API token！
