# SkillHub 核心模块设计 (MVP)

## 1. 概述

本文档描述 SkillHub MVP 的核心功能模块。所有模块都在单个 FastAPI 服务中实现，使用 SQLite 数据库存储。

### MVP 核心模块

1. **认证模块 (Auth Module)** - 用户认证和 JWT Token 管理
2. **权限模块 (RBAC Module)** - 用户-角色-权限管理
3. **技能模块 (Skill Module)** - 技能构建、发布、执行
4. **访问控制模块 (ACL Module)** - 访问控制和审计日志
5. **网关模块 (Gateway Module)** - 统一调用入口

---

## 2. 认证模块 (Auth Module)

### 2.1 职责

- 用户注册和登录
- JWT Token 生成和验证
- 密码哈希和验证
- 刷新令牌管理

### 2.2 代码结构

```
backend/
├── api/auth.py              # 认证 API 端点
├── services/auth_service.py # 认证业务逻辑
└── models/user.py           # User, RefreshToken 模型
```

### 2.3 数据模型

```python
# models/user.py
class User(Base):
    __tablename__ = "users"

    id: str = Column(String, primary_key=True)  # UUID
    username: str = Column(String, unique=True, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    password_hash: str = Column(String, nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: str = Column(String, primary_key=True)
    user_id: str = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: str = Column(String, nullable=False)
    expires_at: datetime = Column(DateTime, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
```

### 2.4 API 端点

```
POST   /api/v1/auth/register    # 注册新用户
POST   /api/v1/auth/login       # 用户登录
POST   /api/v1/auth/refresh     # 刷新 access token
POST   /api/v1/auth/logout      # 登出（撤销 refresh token）
GET    /api/v1/auth/me          # 获取当前用户信息
```

### 2.5 JWT Token 设计

```python
# Token payload
{
    "sub": "user-id",           # 用户 ID
    "username": "john.doe",
    "roles": ["developer"],
    "exp": 1709050500,          # 过期时间 (15 分钟)
    "iat": 1709049600,          # 签发时间
    "jti": "token-unique-id"    # Token ID
}

# 配置
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
```

### 2.6 核心服务方法

```python
# services/auth_service.py
class AuthService:
    def register(self, username: str, email: str, password: str) -> User
    def login(self, username: str, password: str) -> TokenResponse
    def verify_token(self, token: str) -> TokenPayload
    def refresh_token(self, refresh_token: str) -> TokenResponse
    def logout(self, refresh_token: str) -> None
    def hash_password(self, password: str) -> str
    def verify_password(self, password: str, hash: str) -> bool
```

---

## 3. 权限模块 (RBAC Module)

### 3.1 职责

- 角色和权限管理
- 用户角色分配
- 权限检查

### 3.2 代码结构

```
backend/
├── api/users.py              # 用户管理 API
├── api/roles.py              # 角色管理 API
├── services/rbac_service.py  # RBAC 业务逻辑
└── models/user.py            # Role, Permission 模型
```

### 3.3 数据模型

```python
# models/user.py
class Role(Base):
    __tablename__ = "roles"

    id: str = Column(String, primary_key=True)
    name: str = Column(String, unique=True, nullable=False)
    description: str = Column(String)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

class Permission(Base):
    __tablename__ = "permissions"

    id: str = Column(String, primary_key=True)
    resource: str = Column(String, nullable=False)  # e.g., "skills", "users"
    action: str = Column(String, nullable=False)    # e.g., "read", "write", "delete"
    description: str = Column(String)

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: str = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: str = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: str = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: str = Column(String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
```

### 3.4 预定义角色

| 角色名称 | 描述 | 权限范围 |
|----------|------|----------|
| `super_admin` | 超级管理员 | 所有资源的完全控制 |
| `admin` | 系统管理员 | 用户管理、技能管理、配置管理 |
| `developer` | 开发者 | 技能构建、发布、测试 |
| `operator` | 运营人员 | 技能调用、日志查看 |
| `viewer` | 只读用户 | 仅查看权限 |

### 3.5 API 端点

```
# 用户管理
GET    /api/v1/users           # 列出用户 (admin only)
POST   /api/v1/users           # 创建用户 (admin only)
GET    /api/v1/users/{id}      # 获取用户详情
PUT    /api/v1/users/{id}      # 更新用户
DELETE /api/v1/users/{id}      # 删除用户 (admin only)

# 角色管理
GET    /api/v1/roles           # 列出角色
POST   /api/v1/roles           # 创建角色 (admin only)
GET    /api/v1/roles/{id}      # 获取角色详情
PUT    /api/v1/roles/{id}      # 更新角色
DELETE /api/v1/roles/{id}      # 删除角色 (admin only)
POST   /api/v1/roles/{id}/permissions  # 分配权限
```

### 3.6 核心服务方法

```python
# services/rbac_service.py
class RBACService:
    def create_role(self, name: str, description: str) -> Role
    def assign_role_to_user(self, user_id: str, role_id: str) -> None
    def remove_role_from_user(self, user_id: str, role_id: str) -> None
    def get_user_roles(self, user_id: str) -> List[Role]
    def get_user_permissions(self, user_id: str) -> List[Permission]
    def check_permission(self, user_id: str, resource: str, action: str) -> bool
    def assign_permission_to_role(self, role_id: str, permission_id: str) -> None
```

---

## 4. 技能模块 (Skill Module)

### 4.1 职责

- 技能元数据管理
- 代码上传和构建
- 技能发布
- 技能执行

### 4.2 代码结构

```
backend/
├── api/skills.py              # 技能 API 端点
├── services/skill_service.py  # 技能业务逻辑
├── models/skill.py            # Skill, SkillVersion 模型
├── skills/                    # 内置技能示例
└── artifacts/                 # 构建产物存储
```

### 4.3 数据模型

```python
# models/skill.py
class Skill(Base):
    __tablename__ = "skills"

    id: str = Column(String, primary_key=True)  # UUID
    name: str = Column(String, unique=True, nullable=False)
    description: str = Column(String)
    skill_type: str = Column(String, nullable=False)  # business_logic, api_proxy, ai_llm, data_processing
    runtime: str = Column(String, nullable=False)      # python
    created_by: str = Column(String, ForeignKey("users.id"))
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id: str = Column(String, primary_key=True)
    skill_id: str = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))
    version: str = Column(String, nullable=False)  # Semantic version "1.0.0"
    status: str = Column(String, nullable=False)   # draft, published, deprecated
    artifact_path: str = Column(String)            # Local file path
    metadata: dict = Column(JSON)                   # Input/output schema, config
    published_at: datetime = Column(DateTime)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('skill_id', 'version', name='uq_skill_version'),
    )
```

### 4.4 构建流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     技能构建流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 用户上传 Python 代码文件 + requirements.txt                │
│     └─> API: POST /api/v1/skills/{id}/build                    │
│                                                                  │
│  2. 代码验证                                                     │
│     └─> Python 语法检查 (ast.parse)                             │
│     └─> 文件结构验证                                            │
│                                                                  │
│  3. 创建临时构建目录                                            │
│     └─> /tmp/builds/{skill_id}-{timestamp}/                    │
│                                                                  │
│  4. 安装依赖                                                     │
│     └─> pip install -r requirements.txt -t ./dependencies       │
│                                                                  │
│  5. 运行测试（如果存在）                                         │
│     └─> pytest discovery: test_*.py                             │
│     └─> 执行测试并捕获结果                                      │
│                                                                  │
│  6. 打包产物                                                     │
│     └─> 创建 ZIP: code + requirements + metadata                │
│     └─> 存储到: backend/artifacts/{skill_name}-{version}.zip    │
│                                                                  │
│  7. 创建 SkillVersion 记录 (status=draft)                       │
│                                                                  │
│  8. 返回构建结果                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     技能执行流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 接收执行请求                                                 │
│     └─> API: POST /api/v1/skills/{id}/invoke                   │
│     └─> 或: POST /api/v1/gateway/call                           │
│                                                                  │
│  2. 加载技能产物                                                 │
│     └─> 从 artifacts/ 目录解压 ZIP                              │
│     └─> 定位入口函数 (默认: main.py::handler)                   │
│                                                                  │
│  3. 准备执行环境                                                 │
│     └─> 设置环境变量                                            │
│     └─> 创建临时工作目录                                        │
│                                                                  │
│  4. 子进程执行                                                   │
│     └─> python -c "import handler; handler.handler(params)"    │
│     └─> 超时控制: 30 秒默认                                     │
│     └─> 捕获 stdout 和 stderr                                   │
│                                                                  │
│  5. 解析返回结果                                                 │
│     └─> 验证输出符合 output_schema                              │
│                                                                  │
│  6. 清理临时文件                                                │
│                                                                  │
│  7. 返回执行结果                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.6 API 端点

```
GET    /api/v1/skills                 # 列出技能
POST   /api/v1/skills                 # 创建技能
GET    /api/v1/skills/{id}            # 获取技能详情
PUT    /api/v1/skills/{id}            # 更新技能元数据
DELETE /api/v1/skills/{id}            # 删除技能

POST   /api/v1/skills/{id}/build      # 上传代码并构建
GET    /api/v1/skills/{id}/versions   # 列出版本
POST   /api/v1/skills/{id}/publish    # 发布版本
DELETE /api/v1/skills/{id}/versions/{version}  # 删除版本

POST   /api/v1/skills/{id}/invoke     # 直接调用技能
```

### 4.7 核心服务方法

```python
# services/skill_service.py
class SkillService:
    def create_skill(self, name: str, description: str, skill_type: str, created_by: str) -> Skill
    def build_skill(self, skill_id: str, code_file: UploadFile, requirements: UploadFile, version: str) -> SkillVersion
    def publish_skill(self, skill_id: str, version: str) -> SkillVersion
    def execute_skill(self, skill_id: str, version: str, params: dict) -> dict
    def get_skill_versions(self, skill_id: str) -> List[SkillVersion]
    def delete_skill(self, skill_id: str) -> None

    # 内部方法
    def _validate_code(self, code: str) -> bool
    def _install_dependencies(self, requirements: str, target_dir: str) -> None
    def _run_tests(self, skill_dir: str) -> TestResult
    def _create_artifact(self, skill_dir: str, artifact_path: str) -> None
    def _execute_in_subprocess(self, artifact_path: str, params: dict, timeout: int) -> ExecutionResult
```

### 4.8 技能代码结构

```
skill_artifact/
├── main.py              # 入口文件，必须包含 handler 函数
├── requirements.txt     # Python 依赖
├── config.yaml          # 技能配置（可选）
└── tests/               # 测试文件（可选）
    └── test_skill.py
```

**main.py 示例**:
```python
def handler(params: dict) -> dict:
    """
    技能入口函数

    Args:
        params: 调用参数

    Returns:
        dict: 执行结果
    """
    city = params.get("city", "Beijing")
    days = params.get("days", 3)

    # 业务逻辑
    result = {
        "city": city,
        "forecast": [...]  # 天气预报数据
    }

    return result
```

---

## 5. 访问控制模块 (ACL Module)

### 5.1 职责

- ACL 规则管理
- 访问权限检查
- 条件约束执行
- 审计日志记录

### 5.2 代码结构

```
backend/
├── api/acl.py               # ACL API 端点
├── services/acl_service.py  # ACL 业务逻辑
└── models/acl.py            # ACLRule, AuditLog 模型
```

### 5.3 数据模型

```python
# models/acl.py
class ACLRule(Base):
    __tablename__ = "acl_rules"

    id: str = Column(String, primary_key=True)
    resource_id: str = Column(String, nullable=False)      # Skill ID or resource identifier
    resource_name: str = Column(String, nullable=False)
    access_mode: str = Column(String, nullable=False)      # 'any' or 'rbac'
    conditions: dict = Column(JSON)                        # rateLimit, ipWhitelist, etc.
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ACLRuleRole(Base):
    __tablename__ = "acl_rule_roles"

    acl_rule_id: str = Column(String, ForeignKey("acl_rules.id", ondelete="CASCADE"), primary_key=True)
    role_id: str = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permissions: list = Column(JSON, nullable=False)       # ["read", "execute"]

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: str = Column(String, primary_key=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)
    user_id: str = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    resource_id: str = Column(String, nullable=False)
    access_mode: str = Column(String, nullable=False)
    result: str = Column(String, nullable=False)           # 'allow' or 'deny'
    reason: str = Column(String)
    ip_address: str = Column(String)
    user_agent: str = Column(String)
    request_id: str = Column(String)
```

### 5.4 访问模式

#### Any 模式
```python
# 配置示例
{
    "resource_id": "weather-forecast",
    "access_mode": "any",
    "conditions": {
        "rateLimit": "100/minute",
        "ipWhitelist": ["10.0.0.0/8", "192.168.0.0/16"]
    }
}
```

#### RBAC 模式
```python
# 配置示例
{
    "resource_id": "payment-api",
    "access_mode": "rbac",
    "roles": [
        {"role_id": "admin", "permissions": ["read", "write", "delete"]},
        {"role_id": "operator", "permissions": ["read", "write"]}
    ],
    "conditions": {
        "rateLimit": "50/minute"
    }
}
```

### 5.5 权限检查流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACL 权限检查流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 接收检查请求                                                 │
│     └─> user_id, resource_id, action, request_context          │
│                                                                  │
│  2. 查询 ACL 规则                                               │
│     └─> SELECT * FROM acl_rules WHERE resource_id = ?           │
│                                                                  │
│  3. 规则存在检查                                                 │
│     └─> 如果没有规则 → DENY (默认拒绝)                          │
│                                                                  │
│  4. 访问模式判断                                                 │
│     └─> IF mode == 'any':                                       │
│         └─> 检查条件 (rate limit, IP whitelist)                  │
│         └─> 条件满足 → ALLOW, 否则 → DENY                       │
│                                                                  │
│     └─> IF mode == 'rbac':                                      │
│         └─> 获取用户角色                                        │
│         └─> 检查角色是否有所需权限                              │
│         └─> 检查条件                                            │
│         └─> 满足 → ALLOW, 否则 → DENY                           │
│                                                                  │
│  5. 记录审计日志                                                │
│     └─> 插入 audit_logs 表                                      │
│                                                                  │
│  6. 返回检查结果                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.6 API 端点

```
GET    /api/v1/acl/rules          # 列出 ACL 规则
POST   /api/v1/acl/rules          # 创建 ACL 规则
GET    /api/v1/acl/rules/{id}     # 获取规则详情
PUT    /api/v1/acl/rules/{id}     # 更新规则
DELETE /api/v1/acl/rules/{id}     # 删除规则

GET    /api/v1/acl/audit-logs     # 查询审计日志
```

### 5.7 核心服务方法

```python
# services/acl_service.py
class ACLService:
    def create_rule(self, rule: ACLRuleCreate) -> ACLRule
    def check_access(self, user_id: str, resource_id: str, action: str, context: dict) -> bool
    def check_any_mode(self, rule: ACLRule, context: dict) -> bool
    def check_rbac_mode(self, rule: ACLRule, user_id: str, action: str, context: dict) -> bool
    def check_conditions(self, conditions: dict, context: dict) -> bool
    def log_access(self, log: AuditLogCreate) -> None
    def get_audit_logs(self, filters: dict) -> List[AuditLog]

    # 条件检查
    def _check_rate_limit(self, resource_id: str, rate_limit: str) -> bool
    def _check_ip_whitelist(self, ip: str, whitelist: List[str]) -> bool
```

---

## 6. 网关模块 (Gateway Module)

### 6.1 职责

- 统一的技能调用入口
- 请求路由和分发
- 响应格式标准化

### 6.2 代码结构

```
backend/
├── api/gateway.py            # 网关 API 端点
└── services/gateway_service.py  # 网关业务逻辑
```

### 6.3 统一调用接口

**端点**: `POST /api/v1/gateway/call`

**请求格式**:
```json
{
  "skillId": "weather-forecast",
  "version": "1.0.0",
  "params": {
    "city": "Beijing",
    "days": 3
  },
  "context": {
    "requestId": "req-12345"
  }
}
```

**响应格式 (成功)**:
```json
{
  "success": true,
  "data": {
    "city": "Beijing",
    "forecast": [...]
  },
  "metadata": {
    "executionTime": 150,
    "version": "1.0.0",
    "cached": false
  },
  "requestId": "req-12345"
}
```

**响应格式 (失败)**:
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

### 6.4 网关调用流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    网关调用流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 接收请求 + JWT Token                                        │
│                                                                  │
│  2. 验证 JWT Token                                               │
│     └─> 解析 Token，提取 user_id, roles                         │
│     └─> Token 无效 → 返回 401 Unauthorized                      │
│                                                                  │
│  3. 查询技能信息                                                 │
│     └─> 获取技能元数据和版本信息                                │
│     └─> 技能不存在 → 返回 404 Not Found                         │
│                                                                  │
│  4. ACL 权限检查                                                 │
│     └─> 调用 ACL Service 检查权限                               │
│     └─> 权限拒绝 → 返回 403 Forbidden                           │
│                                                                  │
│  5. 执行技能                                                     │
│     └─> 调用 Skill Service 执行                                │
│     └─> 捕获执行结果                                            │
│                                                                  │
│  6. 返回标准化响应                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 核心服务方法

```python
# services/gateway_service.py
class GatewayService:
    def call_skill(self, request: GatewayCallRequest, auth_context: AuthContext) -> GatewayResponse
    def _validate_token(self, token: str) -> TokenPayload
    def _get_skill_info(self, skill_id: str, version: str) -> SkillInfo
    def _check_permission(self, user_id: str, skill_id: str, action: str) -> bool
    def _execute_skill(self, skill_id: str, version: str, params: dict) -> dict
    def _format_response(self, success: bool, data: dict, error: dict, request_id: str) -> dict
```

---

## 7. 模块间依赖关系

```
                    ┌─────────────────────┐
                    │   Auth Module       │
                    │   (认证)             │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   RBAC Module       │
                    │   (权限)             │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐    ┌────────▼────────┐    ┌───────▼────────┐
│  Gateway Module│    │   ACL Module    │    │  Skill Module  │
│   (网关)        │◄───┤   (访问控制)     │◄───┤   (技能)       │
└────────────────┘    └─────────────────┘    └────────────────┘
        │                      │
        └──────────┬───────────┘
                   ▼
            ┌─────────────────┐
            │   SQLite DB     │
            └─────────────────┘
```

**依赖说明**:
- Gateway 依赖 Auth (Token 验证)
- Gateway 依赖 Skill (技能执行)
- Gateway 依赖 ACL (权限检查)
- ACL 依赖 RBAC (角色权限数据)
- Skill 依赖 ACL (执行前权限检查)

---

## 8. 配置管理

### 8.1 配置文件 (config.py)

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "SkillHub"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///data/skillhub.db"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 文件存储配置
    ARTIFACTS_DIR: str = "backend/artifacts"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 技能执行配置
    SKILL_EXECUTION_TIMEOUT: int = 30  # 秒
    MAX_BUILD_TIME: int = 600  # 10 分钟

    # 限流配置
    DEFAULT_RATE_LIMIT: str = "100/minute"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 8.2 环境变量 (.env)

```bash
# .env
DATABASE_URL=sqlite:///data/skillhub.db
JWT_SECRET_KEY=change-this-in-production
DEBUG=true
```

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
