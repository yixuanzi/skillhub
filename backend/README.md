# SkillHub Backend API

SkillHub 后端服务，基于 FastAPI 构建的企业级内部技能生态系统平台 API 服务。

## 📋 目录

- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [功能模块](#功能模块)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [数据库](#数据库)
- [测试](#测试)
- [开发指南](#开发指南)
- [部署](#部署)

---

## 🛠️ 技术栈

### 核心框架
- **Python** 3.11+
- **FastAPI** 0.104+ - 现代高性能 Web 框架
- **SQLAlchemy** 2.0+ - ORM 工具
- **Pydantic** 2.0+ - 数据验证
- **Uvicorn** - ASGI 服务器

### 数据库
- **SQLite** (开发环境)
- **PostgreSQL** 15+ (生产环境推荐)

### 安全认证
- **JWT** (JSON Web Tokens) - 用户认证
- **BCrypt** - 密码加密
- **Passlib** - 密码哈希

### MCP 支持
- **langchain-mcp-adapters** - MCP 服务器集成
- 支持 SSE 和 HTTPSTREAM 传输

### 测试工具
- **Pytest** - 测试框架
- **httpx** - 异步 HTTP 客户端

---

## 📁 项目结构

```
backend/
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── auth.py                 # 认证相关端点
│   ├── resource.py             # 资源管理端点
│   ├── acl_resource.py         # ACL 资源端点
│   ├── gateway.py              # 网关调用端点
│   ├── skill_list.py           # 技能市场端点
│   ├── skill_creator.py        # 技能内容生成端点
│   ├── script.py               # 脚本服务端点
│   ├── api_key.py              # API 密钥管理端点
│   ├── mtoken.py               # Token 托管端点
│   ├── audit_log.py            # 审计日志端点
│   └── user_management.py      # 用户/角色/权限管理端点
│
├── services/                   # 业务逻辑层
│   ├── resource_service.py     # 资源服务
│   ├── acl_resource_service.py # ACL 资源服务
│   ├── gateway_service.py      # 网关服务
│   ├── mcp_service.py          # MCP 服务器服务
│   ├── skill_list_service.py   # 技能市场服务
│   └── skill_creator_service.py # 技能生成服务
│
├── models/                     # 数据模型层
│   ├── user.py                 # 用户、角色、权限模型
│   ├── resource.py             # 资源模型
│   ├── acl.py                  # 访问控制模型
│   ├── skill_list.py           # 技能市场模型
│   ├── api_key.py              # API 密钥模型
│   ├── mtoken.py               # Token 托管模型
│   └── system_audit_log.py     # 系统审计日志模型
│
├── schemas/                    # Pydantic 数据验证层
│   ├── auth.py                 # 认证相关 schemas
│   ├── resource.py             # 资源 schemas
│   ├── acl_resource.py         # ACL 资源 schemas
│   ├── gateway.py              # 网关 schemas
│   ├── skill_list.py           # 技能市场 schemas
│   ├── skill_creator.py        # 技能生成 schemas
│   └── common.py               # 通用 schemas
│
├── core/                       # 核心功能模块
│   ├── deps.py                 # FastAPI 依赖（认证）
│   ├── security.py             # 安全模块（JWT、密码哈希）
│   └── exceptions.py           # 自定义异常
│
├── middleware/                 # 中间件
│   └── audit_middleware.py     # 审计日志中间件
│
├── scripts/                    # 脚本工具
│   └── skillhub.sh             # CLI 工具
│
├── main.py                     # 应用入口
├── config.py                   # 配置管理
└── database.py                 # 数据库连接
```

---

## 🎯 功能模块

### 1. 认证模块 (`/api/v1/auth/`)
- 用户注册
- 用户登录（JWT 认证）
- Token 刷新
- 用户登出
- 获取当前用户信息

### 2. 资源管理模块 (`/api/v1/resources/`)
- 创建资源（gateway、third、mcp）
- 查询资源（支持分页和类型过滤）
- 更新资源（仅所有者）
- 删除资源（仅所有者）
- **访问控制**: public 资源所有用户可访问，private 资源仅所有者/admin/ACL 授权用户可访问

### 3. ACL 资源管理模块 (`/api/v1/acl/resources/`)
- 创建 ACL 规则（仅资源所有者/admin）
- 查询 ACL 规则（基于授权过滤）
- 更新 ACL 规则（仅资源所有者/admin）
- 删除 ACL 规则（仅资源所有者/admin）
- **访问模式**: ANY（公开）、RBAC（基于用户/角色白名单）

### 4. 网关调用模块 (`/api/v1/gateway/`)
- 调用资源（自动权限检查）
- 支持 GET/POST/PUT/DELETE 方法
- 支持路径参数（gateway 类型）
- MCP 工具调用
- MCP 工具列表

### 5. 技能市场模块 (`/api/v1/skills/`)
- 创建技能
- 查询技能（支持多条件联合过滤：category、tags、author）
- 更新技能（仅创建者/admin）
- 删除技能（仅创建者/admin）

### 6. 技能生成模块 (`/api/v1/skill-creator/`)
- 从资源生成技能内容（base 模式）
- 从现有技能生成 SOP（sop 模式）
- MCP 资源自动获取工具列表

### 7. 脚本服务模块 (`/api/v1/script/`)
- 获取 CLI 工具脚本（无需认证）
- 自动替换 SKILLHUB_URL 配置

### 8. API 密钥管理 (`/api/v1/api-keys/`)
- 创建 API 密钥
- 查询 API 密钥
- 删除 API 密钥

### 9. Token 托管模块 (`/api/v1/mtokens/`)
- 创建第三方 API token
- 查询 token（支持分页和按应用过滤）
- 更新 token
- 删除 token

### 10. 审计日志模块 (`/api/v1/audit-logs/`)
- 查询审计日志（普通用户查看自己的，admin 查看所有）
- 支持多维度过滤（action、resource_type、user_id、status、date range）

### 11. 用户管理模块 (`/api/v1/`)
- 用户管理（CRUD）
- 角色管理（CRUD）
- 权限管理

---

## 📦 环境要求

### Python 版本
- Python 3.11 或更高

### 依赖包
主要依赖（见 `requirements.txt`）：
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
httpx==0.25.2
langchain-mcp-adapters>=0.1.0
```

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd skillhub/backend
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/skillhub.db

# JWT 密钥（生产环境请修改）
SECRET_KEY=your-secret-key-change-in-production

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Refresh Token 过期时间（天）
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# SkillHub URL
SKILLHUB_URL=http://localhost:8000

# Server Config
SKILL_HOST=0.0.0.0
SKILL_PORT=8000
```

### 5. 初始化数据库

```bash
python scripts/init_db.py
python scripts/seed_db.py
```

### 6. 启动服务

```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动

### 7. 访问 API 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/skillhub.db` |
| `SECRET_KEY` | JWT 加密密钥 | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | 60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期（天） | 7 |
| `CORS_ORIGINS` | 允许的 CORS 源 | `["http://localhost:5173"]` |
| `SKILLHUB_URL` | SkillHub API 地址 | `http://localhost:8000` |
| `SKILL_HOST` | 服务器监听地址 | `0.0.0.0` |
| `SKILL_PORT` | 服务器端口 | 8000 |

---

## 📚 API 文档

### API 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token 或 API Key
- **响应格式**: JSON

### 主要 API 端点

#### 认证相关
- `POST /auth/register/` - 用户注册
- `POST /auth/login/` - 用户登录
- `POST /auth/refresh/` - 刷新 Access Token
- `POST /auth/logout/` - 用户登出
- `GET /auth/me/` - 获取当前用户信息

#### 资源管理
- `POST /resources/` - 创建资源
- `GET /resources/` - 列出资源
- `GET /resources/{id}/` - 获取资源详情
- `PUT /resources/{id}/` - 更新资源
- `DELETE /resources/{id}/` - 删除资源

#### ACL 管理
- `POST /acl/resources/` - 创建 ACL 规则
- `GET /acl/resources/` - 列出 ACL 规则
- `GET /acl/resources/{id}/` - 获取 ACL 规则
- `PUT /acl/resources/{id}/` - 更新 ACL 规则
- `DELETE /acl/resources/{id}/` - 删除 ACL 规则

#### 网关调用
- `POST /gateway/{name}` - 调用资源
- `GET /gateway/{name}/get` - GET 快捷方式
- `POST /gateway/{name}/post` - POST 快捷方式
- `GET /gateway/{name}/{path:path}` - 带路径的 GET
- `POST /gateway/{name}/mcp` - 调用 MCP 工具
- `GET /gateway/{name}/mcp/tools` - 获取 MCP 工具列表

#### 技能市场
- `POST /skills/` - 创建技能
- `GET /skills/` - 列出技能（支持过滤）
- `GET /skills/{id}/` - 获取技能详情
- `PUT /skills/{id}/` - 更新技能
- `DELETE /skills/{id}/` - 删除技能

#### 技能生成
- `POST /skill-creator/` - 生成技能内容

#### 脚本服务
- `GET /script/bash` - 获取 CLI 工具（无需认证）

更多 API 详情请访问：`http://localhost:8000/docs`

---

## 🗄️ 数据库

### 数据库模型

#### 用户相关
- **User** - 用户表
- **Role** - 角色表
- **Permission** - 权限表
- **RefreshToken** - 刷新令牌表

#### 资源相关
- **Resource** - 资源表（gateway、third、mcp）
- **ResourceType** - 资源类型枚举

#### ACL 相关
- **ACLRule** - 访问控制规则表
- **ACLRuleRole** - ACL 角色关联表
- **AccessMode** - 访问模式枚举（any、rbac）

#### 技能相关
- **SkillList** - 技能市场表

#### 其他
- **APIKey** - API 密钥表
- **MToken** - Token 托管表
- **SystemAuditLog** - 系统审计日志表

### 数据库初始化

```bash
# 创建所有表
python scripts/init_db.py

# 插入测试数据
python scripts/seed_db.py
```

---

## 🧪 测试

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并查看覆盖率
pytest tests/ --cov=tests --cov-report=html
```

---

## 💻 开发指南

### CLI 工具使用

下载 CLI 工具：
```bash
curl http://localhost:8000/api/v1/script/bash -o skillhub.sh
chmod +x skillhub.sh
```

使用示例：
```bash
# Third-party API 调用
./skillhub.sh third weather-api -method GET -inputs '{"city":"Beijing"}'

# Gateway 资源调用
./skillhub.sh gateway backend-api -method GET -path users/123

# MCP 服务器调用
./skillhub.sh mcp my-mcp-server -mcptool tool_name
```

### 安全模型

**资源访问控制**
- **Public 资源**: 所有认证用户可访问
- **Private 资源**: 仅所有者、admin 或 ACL 授权用户可访问

**写操作权限**
- **资源**: 仅所有者可修改
- **ACL 规则**: 资源所有者或 admin 可修改
- **技能**: 仅创建者可修改

**管理员权限**
拥有 `admin` 或 `super_admin` 角色的用户具有：
- 访问所有资源（无视 view_scope）
- 修改任何资源的 ACL 规则
- 查看所有审计日志
- 完整的用户/角色/权限管理

---

## 🔐 认证机制

### JWT Token

- 有效期：60 分钟（可配置）
- 用途：API 调用认证
- 获取方式：登录时返回 `access_token`

### 使用认证

```bash
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/api/v1/resources/
```

---

## 📝 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用 Type Hints
- 编写 Docstrings
- 最大行长度：120 字符

### 命名约定
- **类名**: PascalCase (如 `ResourceService`)
- **函数/方法**: snake_case (如 `get_by_id`)
- **常量**: UPPER_CASE (如 `ADMIN_ROLES`)
- **私有方法**: 前缀下划线 (如 `_is_admin_user()`)

### 提交规范
使用 Conventional Commits：
```
feat(module): 添加新功能
fix(module): 修复 bug
docs: 更新文档
test(module): 添加测试
refactor(module): 重构代码
```

---

## 🚢 部署

### 生产环境配置

#### 1. 使用 PostgreSQL

```bash
# 设置环境变量
export DATABASE_URL="postgresql://user:password@localhost/skillhub"
export SECRET_KEY="<strong-random-key>"
```

#### 2. 使用 Gunicorn

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 3. 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## 📖 相关文档

- [CLAUDE.md](./CLAUDE.md) - Claude Code 开发指南
- [API 设计文档](../docs/api-design.md)
- [技术架构文档](../docs/architecture.md)

---

## 📄 许可证

[MIT License](../LICENSE)

---

**最后更新**: 2026-03-10
