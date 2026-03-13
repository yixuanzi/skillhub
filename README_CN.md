# SkillHub

> 企业级内部技能生态系统平台

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SkillHub 是一个企业级内部技能生态系统平台，旨在为企业提供统一的技能构建、发布和调用管理能力。

## 目录

- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [开发指南](#开发指南)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [部署](#部署)
- [相关文档](#相关文档)

---

## 核心功能

### 1. 技能构建与发布 (Build & Publish)

- 支持多种运行时：Node.js、Python、Go
- 完整的技能生命周期管理
- 代码验证、依赖解析、测试验证
- 版本控制与灰度发布

### 2. 统一网关调用 (Gateway)

- 所有技能调用的统一入口
- JWT 认证 + RBAC 权限控制
- 支持内部托管 API、内部独立 API、第三方 API

### 3. 访问控制列表 (ACL)

- `any` 模式：公开访问（支持速率限制、IP 白名单等条件）
- `rbac` 模式：基于角色的访问控制（支持用户/角色白名单）

### 4. 托管应用令牌 (MToken)

- 自动管理第三方 API Token
- Token 加密存储和自动刷新

### 5. 技能市场 (Skill Market)

- 技能发布与发现
- 支持分类和标签管理

---

## 技术架构

### 前端

```
React 18 + TypeScript
├── Vite 5 - 构建工具
├── React Router 6 - 路由
├── React Query - 数据获取
├── Zustand - 状态管理
└── Tailwind CSS - 样式
```

### 后端

```
Python 3.11+ + FastAPI
├── SQLAlchemy 2.0 - ORM
├── Pydantic 2.0 - 数据验证
├── JWT - 用户认证
└── SQLite/PostgreSQL - 数据存储
```

### 资源类型

| 类型 | 说明 | 示例 |
|-----|------|-----|
| `gateway` | 网关资源，支持路径代理 | 内部 API 代理 |
| `third` | 第三方 API 资源 | OpenAI、Salesforce |
| `mcp` | MCP 服务器资源 | Dify、n8n |

---

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/yixuanzi/skillhub.git
cd skillhub

# 启动服务（包含前端和后端）
docker-compose -f docker-compose-dev.yml up -d

# 访问应用
# 前端: http://localhost
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 手动安装

#### 1. 后端服务

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py
python scripts/seed_db.py

# 启动服务
python main.py
```

#### 2. 前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 3. 使用启动脚本

```bash
# 从项目根目录运行
./start.sh
```

---

## 开发指南

### 环境变量配置

创建 `backend/.env` 文件：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/skillhub.db

# JWT 密钥（生产环境请修改）
SECRET_KEY=your-secret-key-change-in-production

# Token 过期时间
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:80

# 服务器配置
SKILL_HOST=0.0.0.0
SKILL_PORT=8000
SKILLHUB_URL=http://localhost:8000
```

### 默认账户

初始化后可使用以下默认账户登录：

```
用户名: admin
密码: admin123
```

### CLI 工具使用

```bash
# 下载 CLI 工具
curl http://localhost:8000/api/v1/script/bash -o skillhub.sh
chmod +x skillhub.sh

# 调用第三方 API
./skillhub.sh third weather-api -method GET -inputs '{"city":"Beijing"}'

# 调用网关资源
./skillhub.sh gateway backend-api -method GET -path users/123

# 调用 MCP 服务器
./skillhub.sh mcp my-mcp-server -mcptool tool_name
```

---

## 项目结构

```
skillhub/
├── backend/                    # 后端服务
│   ├── api/                    # API 路由层
│   ├── services/               # 业务逻辑层
│   ├── models/                 # 数据模型 (SQLAlchemy)
│   ├── schemas/                # 数据验证 (Pydantic)
│   ├── core/                   # 核心功能
│   ├── middleware/             # 中间件
│   ├── scripts/                # 工具脚本
│   ├── tests/                  # 测试文件
│   ├── main.py                 # 应用入口
│   └── config.py               # 配置管理
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/         # React 组件
│   │   ├── pages/              # 页面组件
│   │   ├── services/           # API 服务
│   │   ├── store/              # 状态管理
│   │   └── utils/              # 工具函数
│   ├── public/                 # 静态资源
│   └── package.json
│
├── docs/                       # 项目文档
│   ├── architecture.md         # 系统架构
│   ├── api-design.md           # API 设计
│   ├── data-model.md           # 数据模型
│   ├── security.md             # 安全设计
│   └── PRD.md                  # 产品需求文档
│
├── docker/                     # Docker 配置
├── docker-compose-dev.yml      # 开发环境
├── docker-compose-prod.yml     # 生产环境
├── Dockerfile                  # 镜像构建
├── start.sh                    # 启动脚本
├── CLAUDE.md                   # Claude Code 指南
└── README.md                   # 本文件
```

---

## API 文档

### 认证方式

支持两种认证方式：

1. **JWT Token** (推荐用于用户)
   ```bash
   curl -H "Authorization: Bearer <jwt_token>" http://localhost:8000/api/v1/resources/
   ```

2. **API Key** (推荐用于应用集成)
   ```bash
   curl -H "X-API-Key: <api_key>" http://localhost:8000/api/v1/resources/
   ```

### 主要 API 端点

| 端点 | 方法 | 说明 |
|-----|------|-----|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/resources/` | GET/POST | 资源列表/创建 |
| `/api/v1/acl/resources/` | GET/POST | ACL 规则管理 |
| `/api/v1/gateway/{name}` | POST | 调用资源 |
| `/api/v1/skills/` | GET/POST | 技能市场 |
| `/api/v1/skill-creator/` | POST | 生成技能内容 |
| `/api/v1/script/bash` | GET | 获取 CLI 工具 |

完整 API 文档：`http://localhost:8000/docs`

---

## 部署

### 生产环境部署

#### 使用 Docker

```bash
# 使用生产配置
docker-compose -f docker-compose-prod.yml up -d
```

#### 手动部署

后端使用 Gunicorn + Uvicorn Workers：

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

前端构建：

```bash
cd frontend
npm run build
# 输出在 frontend/dist/
```

### 环境要求

| 组件 | 版本要求 |
|-----|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ (生产环境推荐) |

---

## 相关文档

- [CLAUDE.md](./CLAUDE.md) - Claude Code 开发指南
- [backend/README.md](./backend/README.md) - 后端服务详细文档
- [frontend/README.md](./frontend/README.md) - 前端应用详细文档
- [docs/PRD.md](./docs/PRD.md) - 产品需求文档
- [docs/architecture.md](./docs/architecture.md) - 系统架构设计
- [docs/api-design.md](./docs/api-design.md) - API 接口设计
- [docs/security.md](./docs/security.md) - 安全设计

---

## 技术栈

### 后端
- FastAPI - 现代高性能 Web 框架
- SQLAlchemy - ORM 工具
- Pydantic - 数据验证
- JWT - 用户认证
- SQLite/PostgreSQL - 数据存储

### 前端
- React 18 - UI 框架
- TypeScript - 类型安全
- Vite - 构建工具
- React Query - 数据获取
- Zustand - 状态管理
- Tailwind CSS - 样式框架

---

## 许可证

[MIT License](LICENSE)

---

**最后更新**: 2026-03-13
