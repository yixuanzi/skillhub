# SkillHub 技术栈选型 (MVP)

## 1. 概述

本文档描述 SkillHub MVP 的技术栈选型。MVP 采用简化的技术栈，专注于快速开发和核心功能验证。

### MVP 设计原则

- **简单优先**：选择成熟、易用的技术
- **快速迭代**：减少配置和部署复杂度
- **易于理解**：降低学习成本
- **可演进**：为未来扩展预留空间

---

## 2. 技术栈总览

```mermaid
graph TB
    subgraph "前端层"
        WebUI[Web 应用<br/>React + TypeScript<br/>Port: 5173]
    end

    subgraph "后端服务层"
        Backend[FastAPI 单体服务<br/>Python 3.11+<br/>Port: 8000]
    end

    subgraph "数据存储层"
        SQLite[(SQLite 数据库<br/>本地文件)]
        Files[本地文件系统<br/>artifacts/]
    end

    WebUI --> Backend
    Backend --> SQLite
    Backend --> Files
```

---

## 3. 后端技术栈

### 3.1 核心框架

| 技术 | 版本 | 选择理由 |
|------|------|----------|
| **Python** | 3.11+ | 简单易用，生态丰富 |
| **FastAPI** | 0.110+ | 现代、快速，自动生成 API 文档 |
| **Uvicorn** | 0.27+ | ASGI 服务器，支持异步 |
| **Pydantic** | 2.0+ | 数据验证，与 FastAPI 深度集成 |

### 3.2 数据库相关

| 技术 | 版本 | 用途 |
|------|------|------|
| **SQLite** | 3.40+ | 主数据库（单文件存储） |
| **SQLAlchemy** | 2.0+ | ORM |
| **Alembic** | 1.12+ | 数据库迁移 |

### 3.3 认证和安全

| 技术 | 版本 | 用途 |
|------|------|------|
| **python-jose** | 3.3+ | JWT 处理 |
| **passlib** | 1.7+ | 密码哈希（bcrypt） |
| **python-multipart** | 0.0+ | 文件上传支持 |

### 3.4 其他依赖

| 技术 | 版本 | 用途 |
|------|------|------|
| **pytest** | 8.0+ | 测试框架 |
| **httpx** | 0.25+ | 异步 HTTP 客户端 |
| **pydantic-settings** | 2.0+ | 配置管理 |

### 3.5 后端依赖文件

```txt
# backend/requirements.txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.0
pydantic==2.6.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# 测试依赖
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.0.0
httpx==0.26.0
```

---

## 4. 前端技术栈

### 4.1 核心框架

| 技术 | 版本 | 选择理由 |
|------|------|----------|
| **React** | 18.x | 成熟的 UI 框架 |
| **TypeScript** | 5.x | 类型安全 |
| **Vite** | 5.x | 快速构建工具，HMR |

### 4.2 UI 和样式

| 技术 | 版本 | 用途 |
|------|------|------|
| **Tailwind CSS** | 3.x | 原子化 CSS 框架 |
| **PostCSS** | 8.x | CSS 处理 |
| **Autoprefixer** | 10.x | CSS 兼容性 |

### 4.3 路由和状态

| 技术 | 版本 | 用途 |
|------|------|------|
| **React Router** | 6.x | 客户端路由 |
| **Zustand** | 4.x | 轻量级状态管理 |
| **React Query** | 5.x | 服务端状态管理 |
| **Axios** | 1.x | HTTP 客户端 |

### 4.4 表单和验证

| 技术 | 版本 | 用途 |
|------|------|------|
| **React Hook Form** | 7.x | 表单管理 |
| **Zod** | 3.x | 数据验证 |

### 4.5 前端依赖文件

```json
{
  "name": "skillhub-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.5.0",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

---

## 5. 开发工具

### 5.1 代码质量

| 工具 | 用途 |
|------|------|
| **ESLint** | JavaScript/TypeScript 代码检查 |
| **Prettier** | 代码格式化 |
| **Black** | Python 代码格式化 |
| **Ruff** | Python 代码检查 |

### 5.2 版本控制

```bash
# .gitignore (简化版)
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
env/
node_modules/
dist/
build/
*.db
*.db-journal
data/*.db
.env
.env.local
```

---

## 6. 技术选型决策 (ADR)

### ADR-001: 选择 FastAPI 作为后端框架

**背景**: 需要一个现代、高效的 Python Web 框架。

**决策**: 使用 FastAPI。

**原因**:
1. 自动生成 OpenAPI 文档（Swagger UI）
2. 基于 Pydantic 的类型安全
3. 原生异步支持
4. 简单易学，快速开发
5. 活跃的社区支持

### ADR-002: 选择 SQLite 作为 MVP 数据库

**背景**: MVP 需要轻量级、易部署的数据库。

**决策**: 使用 SQLite。

**原因**:
1. 零配置，开箱即用
2. 单文件存储，便于备份
3. 无需独立数据库服务
4. 支持 SQL 标准的大部分功能
5. 可以平滑迁移到 PostgreSQL

### ADR-003: 选择 React + Vite 作为前端框架

**背景**: 需要现代的前端开发体验。

**决策**: 使用 React + Vite。

**原因**:
1. React 生态成熟
2. Vite 提供极快的 HMR
3. TypeScript 支持良好
4. 与后端技术栈无关

### ADR-004: 选择本地文件系统存储构建产物

**背景**: 需要存储技能构建产物。

**决策**: 使用本地文件系统。

**原因**:
1. MVP 阶段数据量小
2. 简单直接，无需额外服务
3. 后续可迁移到对象存储（MinIO/S3）

---

## 7. 与完整版技术栈对比

| 层级 | MVP 技术栈 | 完整版技术栈 |
|------|-----------|-------------|
| **后端框架** | FastAPI (Python) | Go (Gin) + Node.js (Express) |
| **数据库** | SQLite | PostgreSQL + Redis |
| **存储** | 本地文件系统 | MinIO/S3 |
| **API 网关** | FastAPI 内置 | Kong Gateway |
| **前端** | React + Vite | React + Vite |
| **部署** | 单进程 | Kubernetes |
| **监控** | 日志文件 | Prometheus + Grafana + ELK |
| **平台集成** | 无 | Dify |

---

## 8. 未来演进路径

### Phase 2: 数据库升级

```python
# 从 SQLite 迁移到 PostgreSQL
# 1. 导出数据
# 2. 调整 SQLAlchemy 连接字符串
DATABASE_URL = "postgresql://user:pass@localhost/skillhub"

# 3. 使用 Alembic 迁移
alembic upgrade head
```

### Phase 3: 添加缓存

```python
# 集成 Redis
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 缓存技能元数据
def get_skill_cached(skill_id: str):
    cached = redis_client.get(f"skill:{skill_id}")
    if cached:
        return json.loads(cached)
    # 从数据库查询...
```

### Phase 4: 添加对象存储

```python
# 集成 MinIO
from minio import Minio

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# 上传构建产物
client.fput_object(
    "skillhub-artifacts",
    "weather-forecast-1.0.0.zip",
    "/tmp/weather-forecast-1.0.0.zip"
)
```

---

## 9. 版本升级策略

| 组件 | MVP 版本 | 升级策略 |
|------|----------|----------|
| Python | 3.11+ | 跟踪最新稳定版 |
| FastAPI | 0.110+ | 每月检查更新 |
| SQLite | 3.40+ | 跟随 Python 版本 |
| React | 18.x | 跟踪最新版 |
| Node.js | 20 LTS | 跟踪 LTS 版本 |

---

## 10. 性能考虑

### MVP 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| API 响应时间 | < 500ms (P99) | MVP 可接受的延迟 |
| 并发请求 | ~100 QPS | SQLite 的合理并发能力 |
| 技能执行时间 | < 30s | 默认超时时间 |

### 优化建议

1. **数据库查询优化**
   - 合理使用索引
   - 避免 N+1 查询
   - 使用 SQLAlchemy 的 `eager loading`

2. **缓存策略**
   - Python 内存缓存（`functools.lru_cache`）
   - 后续添加 Redis

3. **异步处理**
   - FastAPI 的异步端点
   - 长时间任务使用后台任务

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
