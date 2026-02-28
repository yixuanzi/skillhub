# SkillHub 开发指南 (MVP)

## 1. 开发环境搭建

### 1.1 系统要求

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.11+ | 后端开发 |
| Node.js | 20 LTS | 前端开发 |
| SQLite | 3.40+ | 数据库（随 Python） |
| Git | 2.x+ | 版本控制 |
| VS Code | 推荐 | 代码编辑器 |

### 1.2 安装 Python 和依赖

#### macOS

```bash
# 安装 Python 3.11
brew install python@3.11

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装后端依赖
cd backend
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)

```bash
# 安装 Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装后端依赖
cd backend
pip install -r requirements.txt
```

#### Windows

```powershell
# 使用 Python Launcher
py -3.11 -m venv venv
.\venv\Scripts\activate

# 安装后端依赖
cd backend
pip install -r requirements.txt
```

### 1.3 安装前端依赖

```bash
# 安装 Node.js 20 LTS
# macOS
brew install node@20

# Linux
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装前端依赖
cd frontend
npm install
```

### 1.4 配置开发环境

创建 `.env` 文件：

```bash
# backend/.env
DATABASE_URL=sqlite:///data/skillhub.db
JWT_SECRET_KEY=dev-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ARTIFACTS_DIR=backend/artifacts
```

---

## 2. 项目结构

```
skillhub/
├── backend/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   │
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── skill.py
│   │   └── acl.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── skill.py
│   │   └── acl.py
│   │
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── roles.py
│   │   ├── skills.py
│   │   ├── acl.py
│   │   └── gateway.py
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── rbac_service.py
│   │   ├── skill_service.py
│   │   ├── acl_service.py
│   │   └── gateway_service.py
│   │
│   ├── skills/                 # 内置技能示例
│   ├── artifacts/              # 构建产物存储
│   ├── tests/                  # 测试文件
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Skills.tsx
│   │   │   ├── Users.tsx
│   │   │   ├── Roles.tsx
│   │   │   └── ACL.tsx
│   │   │
│   │   ├── components/         # 可复用组件
│   │   ├── api/                # API 客户端
│   │   │   └── client.ts
│   │   ├── types/              # TypeScript 类型
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── data/                       # 数据目录（运行时创建）
│   └── skillhub.db
│
├── docs/                       # 文档
├── run.py                      # 单命令启动
└── README.md
```

---

## 3. 启动开发服务器

### 3.1 方式一：单命令启动（推荐）

```bash
# 在项目根目录
python run.py
```

### 3.2 方式二：分别启动

```bash
# 终端 1：启动后端
cd backend
python -m uvicorn main:app --reload --port 8000

# 终端 2：启动前端
cd frontend
npm run dev
```

### 3.3 访问应用

- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **前端应用**: http://localhost:5173

---

## 4. 开发工作流

### 4.1 创建新功能

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发功能
# 后端：在 backend/ 目录下添加代码
# 前端：在 frontend/src/ 目录下添加代码

# 3. 测试
cd backend && pytest
cd frontend && npm test

# 4. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 4.2 代码规范

#### Python 后端

```python
# 使用类型注解
def get_skill(skill_id: str) -> Optional[Skill]:
    """获取技能详情"""
    return db.query(Skill).filter(Skill.id == skill_id).first()

# 使用 Pydantic 验证
class SkillCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=1000)
```

#### TypeScript 前端

```typescript
// 使用类型定义
interface Skill {
  id: string;
  name: string;
  description: string;
  skill_type: string;
}

// 使用 API 客户端
import { apiClient } from '@/api/client';

export const useSkills = () => {
  return useQuery({
    queryKey: ['skills'],
    queryFn: () => apiClient.get('/skills').then(res => res.data),
  });
};
```

---

## 5. 测试

### 5.1 后端测试

```bash
# 运行所有测试
cd backend
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 带覆盖率报告
pytest --cov=backend --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 5.2 前端测试

```bash
# 运行测试
cd frontend
npm test

# 运行 E2E 测试
npm run test:e2e
```

---

## 6. 数据库操作

### 6.1 初始化数据库

```bash
cd backend
python init_db.py
```

### 6.2 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "Add new field"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 6.3 查看数据库

```bash
# 使用 sqlite3 命令行
sqlite3 data/skillhub.db

# 常用命令
.tables          # 列出所有表
.schema users    # 查看 users 表结构
SELECT * FROM users LIMIT 10;  # 查询数据
```

---

## 7. 调试

### 7.1 后端调试

```python
# 使用 VS Code 调试
# .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "DATABASE_URL": "sqlite:///data/skillhub.db"
      }
    }
  ]
}
```

### 7.2 前端调试

```javascript
// 在 VS Code 中使用 Chrome 调试
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome against localhost",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend/src"
    }
  ]
}
```

### 7.3 日志

```python
# backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}
```

---

## 8. 常见问题

### 8.1 后端问题

**问题**: `ImportError: No module named 'fastapi'`
```bash
# 解决方案：确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows
pip install -r backend/requirements.txt
```

**问题**: `sqlite3.OperationalError: no such table`
```bash
# 解决方案：初始化数据库
cd backend
python init_db.py
```

### 8.2 前端问题

**问题**: `Cannot find module 'react'`
```bash
# 解决方案：安装依赖
cd frontend
npm install
```

**问题**: `Module not found: Error: Can't resolve '@/api/client'`
```bash
# 解决方案：检查 vite.config.ts 中的 alias 配置
```

---

## 9. 代码提交规范

### 9.1 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 9.2 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 代码重构 |
| `test` | 添加测试 |
| `chore` | 构建/工具更新 |

### 9.3 示例

```bash
feat(auth): add JWT token refresh endpoint

Implement refresh token endpoint that allows users to
get a new access token using their refresh token.

Closes #123
```

---

## 10. 性能优化建议

### 10.1 后端优化

1. **使用连接池**
```python
# backend/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

2. **添加索引**
```python
# models/skill.py
class Skill(Base):
    __tablename__ = "skills"
    # ...
    __table_args__ = (
        Index('idx_skills_name', 'name'),
        Index('idx_skills_type', 'skill_type'),
    )
```

### 10.2 前端优化

1. **代码分割**
```typescript
// src/App.tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

2. **请求缓存**
```typescript
// 使用 React Query 缓存
const { data } = useQuery({
  queryKey: ['skills'],
  queryFn: fetchSkills,
  staleTime: 5 * 60 * 1000,  // 5 分钟
});
```

---

## 11. 发布前检查清单

- [ ] 所有测试通过
- [ ] 代码格式化（`black` 和 `prettier`）
- [ ] 代码 lint 检查通过
- [ ] 更新文档
- [ ] 更新版本号
- [ ] 检查环境变量配置
- [ ] 备份数据库（如有）
- [ ] 创建 git tag

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
