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
| RBAC | ✅ | 用户-角色-权限 |
| ACL | ✅ | Any + RBAC 模式 |
| 审计日志 | ✅ | 记录访问决策 |
| HTTPS | ⚠️ | 开发环境 HTTP，生产环境需配置 |
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

        # 5. 分配默认角色（viewer）
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

### 3.1 RBAC 模型

```
用户 (User)
  └─ 拥有 ──> 角色 (Role)
      └─ 包含 ──> 权限 (Permission)
          └─ 作用于 ──> 资源 (Resource)
```

### 3.2 权限检查

```python
# backend/services/rbac_service.py
class RBACService:
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        # 1. 获取用户的角色
        roles = db.query(Role).join(UserRole).filter(
            UserRole.user_id == user_id
        ).all()

        # 2. 获取角色的权限
        permissions = db.query(Permission).join(RolePermission).filter(
            RolePermission.role_id.in_([r.id for r in roles])
        ).all()

        # 3. 检查是否有匹配的权限
        for perm in permissions:
            if perm.resource == resource and perm.action == action:
                return True

        return False
```

### 3.3 预定义角色和权限

```python
# 初始化脚本
PREDEFINED_ROLES = {
    "super_admin": {
        "permissions": ["*:*"]  # 所有权限
    },
    "admin": {
        "permissions": [
            "users:*",
            "skills:*",
            "acl:*"
        ]
    },
    "developer": {
        "permissions": [
            "skills:create",
            "skills:read",
            "skills:write",
            "skills:execute"
        ]
    },
    "operator": {
        "permissions": [
            "skills:read",
            "skills:execute"
        ]
    },
    "viewer": {
        "permissions": [
            "skills:read"
        ]
    }
}
```

---

## 4. ACL 规则

### 4.1 Any 模式

```python
# backend/services/acl_service.py
class ACLService:
    def check_any_mode(self, rule: ACLRule, context: dict) -> bool:
        # 1. 检查限流
        if "rateLimit" in rule.conditions:
            if not self._check_rate_limit(rule.resource_id, rule.conditions["rateLimit"]):
                return False

        # 2. 检查 IP 白名单
        if "ipWhitelist" in rule.conditions:
            client_ip = context.get("ip_address")
            if not self._check_ip_whitelist(client_ip, rule.conditions["ipWhitelist"]):
                return False

        return True
```

### 4.2 RBAC 模式

```python
def check_rbac_mode(self, rule: ACLRule, user_id: str, action: str) -> bool:
    # 1. 获取用户角色
    user_roles = db.query(Role).join(UserRole).filter(
        UserRole.user_id == user_id
    ).all()

    # 2. 检查规则中的角色配置
    for rule_role in rule.acl_rule_roles:
        if rule_role.role in [r.id for r in user_roles]:
            # 3. 检查权限
            permissions = json.loads(rule_role.permissions)
            if action in permissions:
                return True

    return False
```

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
# .env (不提交到 Git)
DATABASE_URL=sqlite:///data/skillhub.db
JWT_SECRET_KEY=change-this-in-production-use-openssl-rand-base64-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# 生产环境
# JWT_SECRET_KEY 应该使用强随机字符串
# 生成方式: openssl rand -base64 32
```

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
| JWT_SECRET_KEY | 简单字符串 | 强随机字符串 |
| 数据库密码 | 无 | 强密码 |
| HTTPS | HTTP | HTTPS |
| CORS | 允许所有源 | 限制源 |

### 10.2 部署前检查清单

- [ ] 修改 JWT_SECRET_KEY
- [ ] 启用 HTTPS
- [ ] 配置 CORS 白名单
- [ ] 配置 TrustedHost
- [ ] 启用日志记录
- [ ] 设置文件权限（database file）
- [ ] 定期备份数据库

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
