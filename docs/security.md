# SkillHub 安全设计文档 (MVP)

## 1. 安全概述

本文档描述 SkillHub MVP 的安全设计。MVP 阶段采用简化的安全策略，专注于核心安全功能的实现。

### 1.1 MVP 安全目标

- **认证**: 用户名/密码 + JWT Token 认证
- **授权**: 基于 RBAC 的权限控制
- **审计**: 记录所有关键操作
- **数据保护**: 密码哈希、敏感信息保护

### 1.2 MVP 安全范围

| 安全功能 | MVP 状态 | 说明 |
|----------|----------|------|
| 密码哈希 | ✅ | bcrypt |
| JWT Token | ✅ | Access Token + Refresh Token |
| 角色 | ✅ | 三个内置角色 + 自定义角色，无权限矩阵 |
| ACL | ✅ | Any + RBAC 模式，决定资源能否被调用 |
| 审计日志 | ✅ | 记录访问决策 |
| HTTPS | ⚠️ | 开发环境 HTTP，生产环境需配置 |
| 登录限流 | ✅ | 按用户名和 IP 统计失败次数 |
| 出站地址限制 | ✅ | 资源不能指向本地或内网地址（SSRF 防护） |
| 审计日志脱敏 | ✅ | 密码、令牌、凭证不落库 |
| 多因素认证 | ❌ | 未实现 |
| API 限流 | ✅ | 基础限流（内存） |
| IP 白名单 | ✅ | ACL 条件支持 |

---

## 2. 认证机制

### 2.1 用户注册

```python
# backend/services/auth_service.py
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def register(self, username: str, email: str, password: str) -> User:
        # 1. 验证用户名和邮箱唯一性
        # 2. 验证密码强度
        # 3. 哈希密码
        password_hash = pwd_context.hash(password)

        # 4. 创建用户
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash
        )

        # 5. 分配默认角色（user）
        # ...
        return user
```

### 2.2 用户登录

```python
class AuthService:
    def login(self, username: str, password: str) -> TokenResponse:
        # 1. 查询用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise AuthException("Invalid credentials")

        # 2. 验证密码
        if not pwd_context.verify(password, user.password_hash):
            raise AuthException("Invalid credentials")

        # 3. 生成 JWT Token
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900  # 15 分钟
        )
```

**登录限流**（`backend/core/login_throttle.py`）：登录失败按 15 分钟滑动窗口计数，达到上限后返回 429 和 `Retry-After`，窗口滑过后自动恢复。

| 维度 | 默认上限 | 配置项 | 作用 |
|------|----------|--------|------|
| 同一用户名（不区分大小写，不论来源 IP） | 5 次 | `LOGIN_MAX_FAILURES` | 防止针对单个账号猜密码 |
| 同一客户端 IP | 50 次 | `LOGIN_MAX_FAILURES_PER_IP` | 防止同一来源遍历多个账号 |

- 被限流期间即使密码正确也会被拒绝，否则限流只能减慢错误的猜测。
- 登录成功会清零该用户名的计数；不存在的用户名同样计数。
- 窗口长度由 `LOGIN_FAILURE_WINDOW_SECONDS` 控制，上限设为 0 表示关闭对应维度。
- 计数保存在进程内存中：重启后清零；多 worker 部署时每个进程各自计数，实际上限会乘以进程数。
- 有意接受的代价：知道用户名的人可以用错误密码让该账号暂时无法用密码登录（SSO 登录不受影响）。

### 2.3 JWT Token 生成

```python
from datetime import datetime, timedelta
from jose import jwt

JWT_SECRET_KEY = "your-secret-key-change-in-production"  # 从环境变量读取
JWT_ALGORITHM = "HS256"

def _create_access_token(self, user: User) -> str:
    expires_delta = timedelta(minutes=15)
    now = datetime.utcnow()

    payload = {
        "sub": user.id,
        "username": user.username,
        "roles": [role.name for role in user.roles],
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid.uuid4())
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

### 2.4 Token 验证

```python
def verify_token(self, token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise AuthException("Token has expired")
    except jwt.JWTError as e:
        raise AuthException(f"Invalid token: {str(e)}")
```

### 2.5 刷新令牌

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String, nullable=False)  # 哈希存储
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_refresh_token(self, user: User) -> str:
    token_id = str(uuid.uuid4())
    refresh_token = jwt.encode(
        {
            "sub": user.id,
            "jti": token_id,
            "exp": datetime.utcnow() + timedelta(days=7)
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    # 存储 Token 哈希
    token_hash = pwd_context.hash(refresh_token)
    db_token = RefreshToken(
        id=token_id,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_token)
    db.commit()

    return refresh_token
```

---

## 3. 授权机制

### 3.1 授权模型

SkillHub 不使用权限矩阵，也没有“权限点”。一次操作是否被允许，只取决于三个问题：

1. **是不是你的**：技能、资源、ACL 规则、API Key、托管令牌，由创建者自己管理。
2. **是不是管理员**：`admin` 和 `super_admin` 可以额外查看并管理他人的技能、资源和 ACL 规则，查看全部审计日志，管理用户和角色。
3. **能不能调用**：只看资源的 ACL 规则（见第 4 节）。归属、管理员角色、资源是否 public 都不构成调用权限。

### 3.2 内置角色

| 角色 | 描述 | 说明 |
|------|------|------|
| `super_admin` | 超级管理员 | 拥有 `admin` 的全部能力，并且可以管理 `super_admin` 账号 |
| `admin` | 管理员 | 有限的管理权限：不能授予 `super_admin`，也不能编辑、删除 `super_admin` 账号或调整其角色 |
| `user` | 普通用户 | 每个账号的默认角色，只管理自己的东西 |

- 角色只是“一组用户”的名字，不带任何权限点。角色定义和判断集中在 `backend/core/roles.py`。
- 三个内置角色不能改名、删除，名称也不能被新建角色占用。
- 注册、SSO 首次登录、管理员创建账号时，自动赋予 `user` 角色。
- 管理员可以创建自定义角色。自定义角色不带来任何管理能力，唯一用途是在 ACL 规则里被授权调用某个资源。

```python
# backend/core/roles.py
ADMIN_ROLES = frozenset({"admin", "super_admin"})

def is_admin_user(user) -> bool:
    return bool(role_names(user) & ADMIN_ROLES)

def is_super_admin(user) -> bool:
    return "super_admin" in role_names(user)
```

### 3.3 谁能做什么

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

### 3.4 对 admin 的限制

`admin` 只有有限的管理权限，以下操作仅 `super_admin` 可以执行，由 `backend/api/user_management.py` 强制：

- 授予或收回 `super_admin` 角色（包括在创建账号时指定）
- 编辑、停用、删除持有 `super_admin` 的账号，或调整其角色

任何人都不能删除自己的账号。

---

## 4. ACL 规则

调用资源时的授权由 `ACLResourceService.enforce_permission` 统一判断，gateway、third、mcp、composio 四类资源走同一条路径，SkillHub 自身的 MCP 服务（`/api/v1/mcp`）也一样。

### 4.1 Any 模式

任何已登录用户都可以调用。

### 4.2 RBAC 模式

命中以下任意一项即允许，否则拒绝：

- `conditions.users`：用户名白名单
- `conditions.roles`：角色白名单，写角色名或角色 ID 均可
- 角色绑定（`acl_rule_roles`）：绑定到这条规则的角色

```python
# backend/services/acl_resource_service.py（节选）
if acl_rule.access_mode == AccessMode.ANY:
    return allowed("Public access (any mode)")

if current_user.username in conditions.get("users", []):
    return allowed("User in whitelist")
if _matched_role_whitelist(current_user, conditions.get("roles")):
    return allowed("User's role in whitelist")
if _matched_role_bindings(current_user, acl_rule):
    return allowed("User's role is bound to this resource")
return denied()
```

资源没有 ACL 规则时一律拒绝。新建资源会自动生成一条 RBAC 规则，并把创建者加入用户白名单。

> **尚未生效的字段**：`conditions` 中的 `ip_whitelist`、`rate_limit`、`time_windows`，角色绑定上的 `permissions`，以及权限检查接口的 `required_permission` 参数，目前可以保存但不参与判断。API Key 没有 scopes：一把 Key 就代表它所属的用户，能做的事与该用户完全相同。下面 4.3 的限流实现是设计稿，尚未接入。

### 4.3 限流实现

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        now = time.time()
        window_start = now - window

        # 清理过期记录
        self.requests[key] = [
            ts for ts in self.requests[key] if ts > window_start
        ]

        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            return False

        # 记录当前请求
        self.requests[key].append(now)
        return True

# 解析限流配置
def parse_rate_limit(rate_limit: str) -> tuple:
    """解析 '100/minute' 格式的配置"""
    count, unit = rate_limit.split("/")
    count = int(count)

    if unit == "second":
        window = 1
    elif unit == "minute":
        window = 60
    elif unit == "hour":
        window = 3600
    else:
        raise ValueError(f"Invalid rate limit unit: {unit}")

    return count, window
```

---

## 5. 审计日志

> **敏感信息脱敏**：审计中间件会记录请求体和查询参数，写入前统一经过 `backend/core/redaction.py` 处理，密码、令牌、密钥、上游凭证等一律替换为 `***`，无法逐字段检查的原始文本不落库。规则详见 [audit-logs.md](audit-logs.md) 的 “Sensitive Data Handling”。脱敏上线之前写入的记录用 `python scripts/redact_audit_logs.py --apply` 清理；清理不等于没泄露过，被记录过的密码和令牌应当更换。

### 5.1 日志记录

```python
# backend/services/audit_service.py
class AuditService:
    def log_access(
        self,
        user_id: str,
        resource_id: str,
        access_mode: str,
        result: str,
        context: dict
    ):
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            resource_id=resource_id,
            access_mode=access_mode,
            result=result,
            reason=context.get("reason"),
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            request_id=context.get("request_id")
        )
        db.add(log)
        db.commit()
```

### 5.2 审计日志查询

```python
def get_audit_logs(
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    result: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    size: int = 20
) -> List[AuditLog]:
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    if result:
        query = query.filter(AuditLog.result == result)
    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)

    return query.order_by(AuditLog.timestamp.desc()).offset((page-1)*size).limit(size).all()
```

---

## 6. API 安全

### 6.1 认证中间件

```python
# backend/middleware/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenPayload:
    token = credentials.credentials
    try:
        payload = auth_service.verify_token(token)
        return payload
    except AuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# 使用示例
@app.get("/api/v1/users/me")
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    return current_user
```

### 6.2 权限装饰器

```python
from functools import wraps
from fastapi import HTTPException

def require_permission(resource: str, action: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: TokenPayload, **kwargs):
            has_permission = rbac_service.check_permission(
                current_user.sub, resource, action
            )
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {resource}:{action}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.post("/api/v1/skills")
@require_permission("skills", "create")
async def create_skill(
    skill_data: SkillCreate,
    current_user: TokenPayload = Depends(get_current_user)
):
    # ...
```

### 6.3 输入验证

```python
from pydantic import BaseModel, Field, validator

class SkillCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=1000)
    skill_type: str = Field(..., pattern="^(business_logic|api_proxy|ai_llm|data_processing)$")

    @validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z0-9-_]+$", v):
            raise ValueError("Name can only contain letters, numbers, hyphens, and underscores")
        return v
```

---

## 7. 密码安全

### 7.1 密码策略

```python
import re

def validate_password(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        raise ValueError("Password must contain at least one special character")

    return True
```

### 7.2 密码哈希

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 哈希密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

---

## 8. 安全配置

### 8.1 环境变量

```bash
# backend/.env (不提交到 Git)
DATABASE_URL=sqlite:///./data/skillhub.db
SECRET_KEY=<随机字符串，至少 32 个字符>
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
GATEWAY_ALLOWED_HOSTS=[]
```

**签名密钥检查**：`SECRET_KEY` 用于签发所有访问令牌和刷新令牌，知道它的人可以伪造任意用户（包括 `super_admin`）的登录态。服务启动时会检查（`core/security.ensure_secret_key_is_safe`），遇到以下情况直接拒绝启动：

- 仍是仓库里的占位值（如 `your-secret-key-change-in-production`）
- 长度不足 32 个字符

生成方式：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

更换密钥会使已签发的令牌全部失效，用户需要重新登录。

### 8.1.1 出站地址限制（SSRF 防护）

任何登录用户都能创建资源并让网关代为请求其地址，所以资源的目标地址必须受限（`backend/core/url_guard.py`）：

- 只允许 `http` / `https`。
- 默认只允许公网可路由的地址。回环、私网（10/8、172.16/12、192.168/16）、链路本地（含云厂商元数据地址 169.254.169.254）、IPv6 本地地址、运营商级 NAT 等一律拒绝。
- 需要访问内网服务时，由管理员在 `GATEWAY_ALLOWED_HOSTS` 中显式放行，JSON 数组，条目可以是：
  - CIDR 或单个 IP：`"10.20.0.0/16"`
  - 主机名：`"billing.internal"`（该名称无论解析到哪里都放行）
  - 通配后缀：`"*.corp.example.com"`
  - `"*"`：完全关闭检查，仅用于开发环境

检查发生在两个时机：

| 时机 | 做什么 |
|------|--------|
| 保存资源（创建、修改） | 不做 DNS 解析，直接拒绝协议不对、字面量为本地或私网 IP、`localhost` 的地址 |
| 每次调用前（gateway、third、mcp） | 解析域名，解析结果中只要有一个地址不被允许就拒绝，请求不会发出 |

对调用方的报错不包含解析出的 IP，避免被用来探测内网 DNS；具体地址记录在服务端日志里。

已知局限：HTTP 客户端建立连接时会再解析一次域名，检查与连接之间如果 DNS 记录被切换（DNS rebinding），这里拦不住。网关不跟随重定向，所以公网地址无法把请求跳转到内网。

### 8.2 CORS 配置

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.3 安全头

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 生产环境添加
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.skillhub.example.com"]
)
```

---

## 9. 数据安全

### 9.1 敏感字段处理

```python
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        # 排除敏感字段
        fields = {"password_hash": {"exclude": True}}
```

### 9.2 数据库安全

```python
# 使用 SQLAlchemy 参数化查询（自动防护 SQL 注入）
user = db.query(User).filter(User.username == username).first()

# 不要直接拼接 SQL
# 危险示例（不要这样做）:
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

---

## 10. 生产环境安全建议

### 10.1 必须修改的配置

| 配置 | 开发环境 | 生产环境 |
|------|----------|----------|
| SECRET_KEY | 随机字符串（占位值无法启动） | 独立生成的强随机字符串 |
| GATEWAY_ALLOWED_HOSTS | 按需放行本机或内网 | 只放行确实需要的内网目标 |
| 数据库密码 | 无 | 强密码 |
| HTTPS | HTTP | HTTPS |
| CORS | 允许所有源 | 限制源 |

### 10.2 部署前检查清单

- [ ] 设置独立生成的 SECRET_KEY
- [ ] 核对 GATEWAY_ALLOWED_HOSTS 只包含必要的内网目标
- [ ] 修改默认管理员密码（`admin / admin123`）
- [ ] 启用 HTTPS
- [ ] 配置 CORS 白名单
- [ ] 配置 TrustedHost
- [ ] 启用日志记录
- [ ] 设置文件权限（database file）
- [ ] 定期备份数据库

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
