# SkillHub 数据模型设计 (MVP)

## 1. 概述

本文档定义 SkillHub MVP 的数据模型，使用 SQLite 作为数据库。数据模型经过简化，专注于 MVP 核心功能。

### MVP 数据库技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| SQLite | 3.40+ | 轻量级关系数据库，单文件存储 |
| SQLAlchemy | 2.0+ | Python ORM |
| Alembic | 1.12+ | 数据库迁移工具 |

---

## 2. 实体关系图

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    USER_ROLES }o--|| ROLES : references

    USERS ||--o{ SKILLS : creates
    SKILLS ||--o{ SKILL_VERSIONS : has

    SKILLS ||--o{ ACL_RULES : protected_by
    ROLES ||--o{ ACL_RULE_ROLES : defines

    USERS ||--o{ AUDIT_LOGS : generates

    USERS {
        TEXT id PK
        TEXT username UK
        TEXT email UK
        TEXT password_hash
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    ROLES {
        TEXT id PK
        TEXT name UK
        TEXT description
        TIMESTAMP created_at
    }

    USER_ROLES {
        TEXT user_id FK
        TEXT role_id FK
    }

    SKILLS {
        TEXT id PK
        TEXT name UK
        TEXT description
        TEXT skill_type
        TEXT runtime
        TEXT created_by FK
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    SKILL_VERSIONS {
        TEXT id PK
        TEXT skill_id FK
        TEXT version
        TEXT status
        TEXT artifact_path
        JSON metadata
        TIMESTAMP published_at
        TIMESTAMP created_at
    }

    ACL_RULES {
        TEXT id PK
        TEXT resource_id
        TEXT resource_name
        TEXT access_mode
        JSON conditions
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    ACL_RULE_ROLES {
        TEXT acl_rule_id FK
        TEXT role_id FK
        JSON permissions
    }

    AUDIT_LOGS {
        TEXT id PK
        TIMESTAMP timestamp
        TEXT user_id FK
        TEXT resource_id
        TEXT access_mode
        TEXT result
        TEXT reason
        TEXT ip_address
        TEXT user_agent
        TEXT request_id
    }

    REFRESH_TOKENS {
        TEXT id PK
        TEXT user_id FK
        TEXT token_hash
        TIMESTAMP expires_at
        TIMESTAMP created_at
    }
```

---

## 3. 核心表结构

### 3.1 用户和认证表

#### users（用户表）

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,                       -- UUID
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,              -- bcrypt hash
    is_active BOOLEAN DEFAULT 1,              -- 1=active, 0=inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
```

#### refresh_tokens（刷新令牌表）

```sql
CREATE TABLE refresh_tokens (
    id TEXT PRIMARY KEY,                       -- UUID
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,                  -- Hashed token
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

### 3.2 角色表

角色只是“一组用户”的名字，不带任何权限点，因此没有权限表。授权模型见 [security.md](security.md) 第 3 节。

#### roles（角色表）

```sql
CREATE TABLE roles (
    id TEXT PRIMARY KEY,                       -- UUID
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

内置角色（由 `backend/scripts/seed_db.py` 创建，缺失时在首次需要时自动补建）：

| name | 说明 |
|------|------|
| `super_admin` | 超级管理员 |
| `admin` | 管理员 |
| `user` | 普通用户，每个账号的默认角色 |

除此之外的角色都是管理员创建的自定义角色，只用于在 ACL 规则中成组授权。

#### user_roles（用户角色关联表）

```sql
CREATE TABLE user_roles (
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

> 早期版本还有 `permissions` 和 `role_permissions` 两张表，以及 `developer`、`operator`、`viewer` 三个预置角色，它们从未参与过权限判断，现已移除。存量数据库用 `python scripts/migrate_roles.py` 迁移（默认只预演，加 `--apply` 才写入）：`viewer` 改名为 `user`，`developer`、`operator` 被删除、其成员改为 `user`，两张旧表被删除。

### 3.3 技能相关表

#### skills（技能表）

```sql
CREATE TABLE skills (
    id TEXT PRIMARY KEY,                       -- UUID
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    skill_type TEXT NOT NULL,                  -- 'business_logic', 'api_proxy', 'ai_llm', 'data_processing'
    runtime TEXT NOT NULL DEFAULT 'python',    -- MVP: 仅支持 'python'
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_type ON skills(skill_type);
CREATE INDEX idx_skills_created_by ON skills(created_by);
```

#### skill_versions（技能版本表）

```sql
CREATE TABLE skill_versions (
    id TEXT PRIMARY KEY,                       -- UUID
    skill_id TEXT NOT NULL,
    version TEXT NOT NULL,                     -- Semantic version '1.0.0'
    status TEXT NOT NULL DEFAULT 'draft',     -- 'draft', 'published', 'deprecated'
    artifact_path TEXT,                       -- 本地文件路径
    metadata TEXT,                            -- JSON: input_schema, output_schema, config
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(skill_id, version),
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

CREATE INDEX idx_skill_versions_skill_id ON skill_versions(skill_id);
CREATE INDEX idx_skill_versions_status ON skill_versions(status);
CREATE INDEX idx_skill_versions_version ON skill_versions(skill_id, version DESC);
```

### 3.4 ACL 相关表

#### acl_rules（ACL 规则表）

```sql
CREATE TABLE acl_rules (
    id TEXT PRIMARY KEY,                       -- UUID
    resource_id TEXT NOT NULL,                -- 技能 ID 或资源标识符
    resource_name TEXT NOT NULL,
    access_mode TEXT NOT NULL,                -- 'any' or 'rbac'
    conditions TEXT,                          -- JSON: rateLimit, ipWhitelist, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_acl_rules_resource_id ON acl_rules(resource_id);
CREATE INDEX idx_acl_rules_access_mode ON acl_rules(access_mode);
```

#### acl_rule_roles（ACL 规则角色关联表）

```sql
CREATE TABLE acl_rule_roles (
    acl_rule_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    permissions TEXT,                         -- JSON array，可保存，尚未参与判断
    PRIMARY KEY (acl_rule_id, role_id),
    FOREIGN KEY (acl_rule_id) REFERENCES acl_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE INDEX idx_acl_rule_roles_acl_rule_id ON acl_rule_roles(acl_rule_id);
CREATE INDEX idx_acl_rule_roles_role_id ON acl_rule_roles(role_id);
```

### 3.5 审计日志表

#### audit_logs（审计日志表）

```sql
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,                       -- UUID
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,                             -- 可为 NULL（未认证请求）
    resource_id TEXT NOT NULL,
    access_mode TEXT NOT NULL,                -- 'any' or 'rbac'
    result TEXT NOT NULL,                     -- 'allow' or 'deny'
    reason TEXT,
    ip_address TEXT,
    user_agent TEXT,
    request_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_result ON audit_logs(result);
```

---

## 4. 数据库初始化

### 4.1 SQLAlchemy 模型定义

```python
# backend/models/__init__.py
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    skill_type = Column(String, nullable=False)
    runtime = Column(String, nullable=False, default="python")
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id = Column(String, primary_key=True)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"))
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")
    artifact_path = Column(String)
    metadata = Column(JSON)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class ACLRule(Base):
    __tablename__ = "acl_rules"

    id = Column(String, primary_key=True)
    resource_id = Column(String, nullable=False)
    resource_name = Column(String, nullable=False)
    access_mode = Column(String, nullable=False)  # 'any' or 'rbac'
    conditions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"))
    resource_id = Column(String, nullable=False)
    access_mode = Column(String, nullable=False)
    result = Column(String, nullable=False)  # 'allow' or 'deny'
    reason = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    request_id = Column(String)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 初始化脚本

```bash
cd backend
python scripts/init_db.py     # 建表
python scripts/seed_db.py     # 创建内置角色和默认管理员账号
```

`seed_db.py` 创建三个内置角色，以及一个持有 `super_admin` 的默认账号 `admin`：

```python
# backend/scripts/seed_db.py（节选）
from core.roles import BUILTIN_ROLES   # super_admin / admin / user

def seed_roles(db):
    for name, description in BUILTIN_ROLES.items():
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name, description=description))
```

---

## 5. 数据迁移

### 5.1 Alembic 配置

```ini
# alembic.ini
[alembic]
script_location = backend/migrations
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = sqlite:///data/skillhub.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 5.2 创建迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 6. 数据字典

### 6.1 枚举值定义

#### 技能类型 (skill_type)

| 值 | 描述 |
|----|------|
| business_logic | 业务逻辑函数 |
| api_proxy | API 代理 |
| ai_llm | AI/LLM 能力 |
| data_processing | 数据处理 |

#### 版本状态 (version_status)

| 值 | 描述 |
|----|------|
| draft | 草稿 |
| published | 已发布 |
| deprecated | 已废弃 |

#### 访问模式 (access_mode)

| 值 | 描述 |
|----|------|
| any | 公开访问（带条件约束） |
| rbac | 基于角色的访问控制 |

#### 审计结果 (audit_result)

| 值 | 描述 |
|----|------|
| allow | 允许访问 |
| deny | 拒绝访问 |

### 6.2 JSON 字段格式

#### skill_versions.metadata

```json
{
  "input_schema": {
    "type": "object",
    "properties": {
      "city": {"type": "string"},
      "days": {"type": "integer", "minimum": 1, "maximum": 7}
    },
    "required": ["city"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "forecast": {"type": "array"}
    }
  },
  "config": {
    "timeout": 30,
    "memory": 256
  }
}
```

#### acl_rules.conditions

```json
{
  "rateLimit": "100/minute",
  "ipWhitelist": ["10.0.0.0/8", "192.168.0.0/16"]
}
```

#### acl_rule_roles.permissions

```json
["read", "execute", "write", "delete"]
```

该字段可以保存，但目前不参与判断：角色一旦绑定到规则，其成员即可调用该资源。

---

## 7. 数据备份和恢复

### 7.1 备份

```bash
# 备份 SQLite 数据库
cp data/skillhub.db data/backups/skillhub_$(date +%Y%m%d_%H%M%S).db
```

### 7.2 恢复

```bash
# 恢复 SQLite 数据库
cp data/backups/skillhub_20250228_100000.db data/skillhub.db
```

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
