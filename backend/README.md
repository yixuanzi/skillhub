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
- **Redis** 7.x (缓存和会话)

### 安全认证
- **JWT** (JSON Web Tokens) - 用户认证
- **TmpKey** - 临时密钥认证
- **BCrypt** - 密码加密
- **Passlib** - 密码哈希

### 测试工具
- **Pytest** - 测试框架
- **httpx** - 异步 HTTP 客户端
- **TestClient** - FastAPI 测试客户端

---

## 📁 项目结构

```
backend/
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── auth.py                 # 认证相关端点（注册、登录、刷新 token）
│   ├── mtoken.py              # Token 托管端点
│   ├── resource.py             # 资源管理端点
│   ├── acl_resource.py         # ACL 资源端点
│   ├── gateway.py              # 网关管理端点
│   └── skill_list.py           # 技能市场端点
│
├── models/                     # 数据模型层
│   ├── __init__.py
│   ├── user.py                 # 用户、角色、权限模型
│   ├── skill.py                # 技能模型
│   ├── acl.py                  # 访问控制模型
│   ├── resource.py             # 资源模型
│   ├── skill_list.py           # 技能市场模型
│   └── mtoken.py              # Token 托管模型
│
├── schemas/                    # Pydantic 数据验证层
│   ├── __init__.py
│   ├── auth.py                 # 认证相关 schemas
│   ├── mtoken.py              # Token 托管 schemas
│   ├── resource.py             # 资源 schemas
│   ├── acl_resource.py         # ACL 资源 schemas
│   ├── gateway.py              # 网关 schemas
│   └── common.py               # 通用 schemas
│
├── services/                   # 业务逻辑层
│   ├── __init__.py
│   ├── auth_service.py         # 认证服务
│   ├── mtoken_service.py      # Token 托管服务
│   ├── resource_service.py     # 资源服务
│   ├── acl_resource_service.py # ACL 资源服务
│   └── gateway_service.py      # 网关服务
│
├── core/                       # 核心功能模块
│   ├── __init__.py
│   ├── deps.py                 # FastAPI 依赖（认证）
│   ├── security.py             # 安全模块（JWT、密码哈希）
│   ├── tmpkey_manager.py       # TmpKey 管理器
│   └── exceptions.py           # 自定义异常
│
├── tests/                      # 测试文件
│   ├── conftest.py             # pytest 配置和 fixtures
│   ├── test_auth_service.py    # 认证服务测试
│   ├── test_mtoken_service.py  # Token 托管服务测试
│   ├── test_mtoken_api.py      # Token 托管 API 测试
│   └── ...
│
├── scripts/                    # 脚本工具
│   ├── init_db.py             # 数据库初始化
│   ├── seed_db.py             # 数据库种子数据
│   ├── create_skill_list_table.py     # 创建 skill_list 表
│   └── create_mtoken_table.py        # 创建 mtoken 表
│
├── main.py                     # 应用入口
├── config.py                   # 配置管理
├── database.py                 # 数据库连接
└── run_tests.py               # 测试运行器
```

---

## 🎯 功能模块

### 1. 认证模块 (`/api/v1/auth/`)
- 用户注册
- 用户登录（JWT + TmpKey 双认证）
- Token 刷新
- 用户登出
- 获取当前用户信息

### 2. Token 托管模块 (`/api/v1/mtokens/`)
- 创建第三方 API token
- 查询 token（支持分页和按应用过滤）
- 更新 token
- 删除 token
- **用户隔离**：每个用户只能管理自己创建的 token

### 3. 技能市场模块 (`/api/v1/skills/`)
- 创建技能
- 查询技能（支持分页、分类、标签、作者过滤）
- 更新技能
- 删除技能

### 4. 资源管理模块 (`/api/v1/resources/`)
- 创建资源（build、gateway、third）
- 查询资源（支持分页和类型过滤）
- 更新资源
- 删除资源

### 5. ACL 资源管理模块 (`/api/v1/acl-resources/`)
- 管理 ACL 资源
- 资源权限配置

### 6. 网关管理模块 (`/api/v1/gateways/`)
- 网关配置管理
- 路由规则配置

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

创建 `.env` 文件（可选）：

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/skillhub.db

# JWT 密钥（生产环境请修改）
SECRET_KEY=your-secret-key-change-in-production

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Refresh Token 过期时间（天）
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
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

服务将在 `http://localhost:8000` 启动

### 7. 访问 API 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ⚙️ 配置说明

### 配置文件 (`config.py`)

```python
class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/skillhub.db"

    # 安全
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/skillhub.db` |
| `SECRET_KEY` | JWT 加密密钥 | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期（天） | 7 |
| `CORS_ORIGINS` | 允许的 CORS 源 | `["http://localhost:5173"]` |

---

## 📚 API 文档

### API 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token 或 TmpKey
- **响应格式**: JSON

### 主要 API 端点

#### 认证相关
- `POST /auth/register/` - 用户注册
- `POST /auth/login/` - 用户登录（返回 JWT + TmpKey）
- `POST /auth/refresh/` - 刷新 Access Token
- `POST /auth/logout/` - 用户登出
- `GET /auth/me/` - 获取当前用户信息

#### Token 托管
- `POST /mtokens/` - 创建 token
- `GET /mtokens/` - 列出 token（支持分页和过滤）
- `GET /mtokens/{id}` - 获取单个 token
- `PUT /mtokens/{id}` - 更新 token
- `DELETE /mtokens/{id}` - 删除 token

#### 技能市场
- `POST /skills/` - 创建技能
- `GET /skills/` - 列出技能（支持分页和过滤）
- `GET /skills/{id}` - 获取技能详情
- `PUT /skills/{id}` - 更新技能
- `DELETE /skills/{id}` - 删除技能

#### 资源管理
- `POST /resources/` - 创建资源
- `GET /resources/` - 列出资源
- `GET /resources/{id}` - 获取资源详情
- `PUT /resources/{id}` - 更新资源
- `DELETE /resources/{id}` - 删除资源

更多 API 详情请访问：`http://localhost:8000/docs`

---

## 🗄️ 数据库

### 数据库模型

#### 用户相关
- **User** - 用户表
- **Role** - 角色表
- **Permission** - 权限表
- **RefreshToken** - 刷新令牌表

#### 技能相关
- **Skill** - 技能表
- **SkillVersion** - 技能版本表
- **SkillType** - 技能类型枚举
- **SkillRuntime** - 技能运行时
- **SkillStatus** - 技能状态枚举

#### 技能市场
- **SkillList** - 技能市场表

#### 资源相关
- **Resource** - 资源表
- **ResourceType** - 资源类型枚举

#### ACL 相关
- **ACLRule** - 访问控制规则表
- **ACLRuleRole** - ACL 角色关联表
- **AuditLog** - 审计日志表
- **AccessMode** - 访问模式枚举
- **AuditResult** - 审计结果枚举

#### Token 托管
- **MToken** - 第三方 token 托管表

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

### 运行特定模块测试

```bash
# 认证模块测试
pytest tests/test_auth*.py -v

# Token 托管测试
pytest tests/test_mtoken*.py -v

# 技能市场测试
pytest tests/test_skill_list*.py -v

# 资源管理测试
pytest tests/test_resources*.py -v
```

### 测试文件说明

- `test_auth_service.py` - 认证服务单元测试
- `test_auth_api.py` - 认证 API 集成测试
- `test_mtoken_service.py` - Token 托管服务测试
- `test_mtoken_api.py` - Token 托管 API 测试
- `test_skill_list_service.py` - 技能市场服务测试
- `test_skill_list_api.py` - 技能市场 API 测试
- `test_resources.py` - 资源管理测试

---

## 💻 开发指南

### 添加新的 API 端点

#### 1. 创建数据模型 (`models/`)

```python
# models/my_model.py
from sqlalchemy import Column, String, Text, DateTime
from database import Base
import uuid
from datetime import timezone, datetime

class MyModel(Base):
    __tablename__ = "my_model"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
```

#### 2. 创建 Pydantic Schemas (`schemas/`)

```python
# schemas/my_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MyModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class MyModelCreate(MyModelBase):
    pass

class MyModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

class MyModelResponse(MyModelBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### 3. 创建服务层 (`services/`)

```python
# services/my_model_service.py
from sqlalchemy.orm import Session
from models.my_model import MyModel
from schemas.my_schema import MyModelCreate, MyModelUpdate, MyModelResponse
from core.exceptions import NotFoundException

class MyModelService:
    @staticmethod
    def create(db: Session, data: MyModelCreate, user_id: str) -> MyModelResponse:
        new_model = MyModel(**data.dict(), created_by=user_id)
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return MyModelResponse.model_validate(new_model)

    @staticmethod
    def get_by_id(db: Session, model_id: str, user_id: str):
        return db.query(MyModel).filter(
            MyModel.id == model_id,
            MyModel.created_by == user_id
        ).first()

    # ... 其他方法
```

#### 4. 创建 API 路由 (`api/`)

```python
# api/my_model.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.my_schema import MyModelCreate, MyModelUpdate, MyModelResponse
from services.my_model_service import MyModelService
from core.deps import get_current_active_user
from models.user import User

router = APIRouter(prefix="/mymodels", tags=["MyModel"])

@router.post("/", response_model=MyModelResponse)
async def create_mymodel(
    data: MyModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return MyModelService.create(db, data, str(current_user.id))
```

#### 5. 注册路由 (`main.py`)

```python
from api.my_model import router as my_model_router

app.include_router(my_model_router, prefix="/api/v1")
```

---

## 🔐 认证机制

### JWT + TmpKey 双认证

SkillHub Backend 支持两种认证方式：

#### 1. JWT Token（短期）
- 有效期：15 分钟
- 用途：高频操作、API 调用
- 获取方式：登录时返回 `access_token`

#### 2. TmpKey（长期）
- 有效期：7 天
- 用途：长期会话、减少重复登录
- 获取方式：登录时返回 `tmpkey`

### 使用认证

#### JWT Token 方式
```bash
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/api/v1/mtokens/
```

#### TmpKey 方式
```bash
curl -H "Authorization: Bearer <tmpkey>" \
  http://localhost:8000/api/v1/mtokens/
```

### 两种方式完全等价！
所有需要认证的 API 端点都支持这两种方式。

---

## 📝 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用 Type Hints
- 编写 Docstrings（Google 风格）
- 最大行长度：120 字符

### 命名约定
- **类名**: PascalCase (如 `MTokenService`)
- **函数/方法**: snake_case (如 `get_by_id`)
- **常量**: UPPER_CASE (如 `DEFAULT_EXPIRE_SECONDS`)
- **私有方法**: 前缀下划线 (如 `_internal_method()`)

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

- [API 设计文档](../docs/api-design.md)
- [技术架构文档](../docs/architecture.md)
- [开发指南](../docs/development.md)
- [数据模型文档](../docs/data-model.md)
- [安全设计文档](../docs/security.md)
- [MToken 使用文档](../docs/mtoken-usage.md)

---

## 🐛 故障排查

### 常见问题

#### 1. 导入错误
```
ModuleNotFoundError: No module named 'xxx'
```
**解决**: 确保在虚拟环境中，运行 `pip install -r requirements.txt`

#### 2. 数据库连接错误
```
sqlalchemy.exc.OperationalError: unable to open database file
```
**解决**: 确保 `data/` 目录存在，或检查 `DATABASE_URL` 配置

#### 3. CORS 错误
```
Access blocked by CORS policy
```
**解决**: 在 `config.py` 中添加前端地址到 `CORS_ORIGINS`

#### 4. 认证失败
```
401 Unauthorized
```
**解决**: 确保提供了有效的 JWT Token 或 TmpKey

---

## 📞 联系方式

- **项目地址**: [GitHub Repository]
- **问题反馈**: [Issues]

---

## 📄 许可证

[MIT License](../LICENSE)

---

**最后更新**: 2025-02-28
