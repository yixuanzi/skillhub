# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillHub is an enterprise-level internal skill ecosystem platform for managing, publishing, and calling AI agent skills. It provides a complete skill lifecycle management system including resource management, access control, and skill generation tools.

## Architecture

This is a **monolithic FastAPI application** with SQLAlchemy ORM:

- **Backend**: Python 3.11+ + FastAPI + SQLAlchemy + SQLite
  - `api/` - FastAPI route handlers
  - `services/` - Business logic layer
  - `models/` - SQLAlchemy ORM models
  - `schemas/` - Pydantic request/response schemas
  - `core/` - Core utilities (deps, exceptions, middleware)
  - `scripts/` - Utility scripts (skillhub.sh CLI tool)

- **Data Layer**:
  - SQLite (development, easily upgradable to PostgreSQL)
  - JSON fields for flexible configuration (ext, conditions)
  - Row-level ownership tracking (owner_id)

## Core Concepts

### Resource Types
- `gateway` - Gateway resources with path support for API proxying
- `third` - Third-party API resources with method-based access
- `mcp` - MCP (Model Context Protocol) servers with tool discovery

### View Scope
- `public` - Accessible to all authenticated users
- `private` - Accessible only to owner, admin/super_admin, or ACL-granted users

### Access Control Modes (ACL)
- `any` - Public access within the ACL context
- `rbac` - Role-based access with user/role whitelists

### User Roles
- `admin` - Full administrative access
- `super_admin` - Full administrative access
- Custom roles - Defined via role management

## Development Commands

### Start Development Server
```bash
cd backend
python main.py
# Server runs on http://0.0.0.0:8000 (configurable via SKILL_HOST/SKILL_PORT)
```

### Environment Variables
```bash
SKILLHUB_URL=http://localhost:8000  # Base URL for API and scripts
DATABASE_URL=sqlite:///./data/skillhub.db
SECRET_KEY=your-secret-key
SKILL_HOST=0.0.0.0
SKILL_PORT=8000
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Code Organization

### Project Structure
```
backend/
├── api/              # FastAPI route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── resource.py   # Resource CRUD
│   ├── acl_resource.py # ACL rule management
│   ├── gateway.py    # Resource invocation gateway
│   ├── skill_list.py # Skill marketplace
│   ├── skill_creator.py # Skill content generation
│   ├── script.py     # Script serving (no auth required)
│   ├── api_key.py    # API key management
│   ├── mtoken.py     # Managed tokens
│   ├── audit_log.py  # System audit logs
│   └── user_management.py # User/role/permission management
├── services/         # Business logic layer
│   ├── resource_service.py
│   ├── acl_resource_service.py
│   ├── skill_list_service.py
│   ├── skill_creator_service.py
│   ├── gateway_service.py
│   └── mcp_service.py
├── models/           # SQLAlchemy ORM models
│   ├── user.py       # User, Role, Permission, RefreshToken
│   ├── resource.py   # Resource (gateway, third, mcp)
│   ├── acl.py        # ACLRule, ACLRuleRole
│   ├── skill_list.py # Skill marketplace
│   ├── api_key.py    # API keys
│   └── mtoken.py     # Managed tokens
├── schemas/          # Pydantic schemas
├── core/             # Core utilities
│   ├── deps.py       # Dependencies (get_current_active_user)
│   └── exceptions.py # Custom exceptions
├── scripts/          # Utility scripts
│   └── skillhub.sh   # CLI tool for resource invocation
└── main.py           # Application entry point
```

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: `_leading_underscore`

### Service Layer Pattern
```python
class SomeService:
    @staticmethod
    def create(db, data, user=None) -> Response:
        # Business logic
        pass

    @staticmethod
    def get_accessible(db, id, user) -> Model:
        # Access control check
        pass
```

## API Design

### Base URL
All endpoints are prefixed with `/api/v1/`

### Authentication
- JWT tokens via `Authorization: Bearer <token>` header
- API keys via `X-API-Key` header
- Refresh token rotation for enhanced security

### Response Format
Success responses return the model directly:
```json
{
  "id": "uuid",
  "name": "example",
  ...
}
```

Error responses (HTTPException):
```json
{
  "detail": "Error message"
}
```

### Pagination
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20
}
```

## Key Design Patterns

### Access Control Implementation
1. **Resource Access** (`resource_service.py`):
   - `get_accessible()` - Public resources accessible to all
   - Private resources: owner OR admin OR ACL-granted
   - SQLite JSON functions for ACL filtering

2. **ACL Management** (`acl_resource_service.py`):
   - Write operations: owner OR admin/super_admin only
   - Read operations: user has been granted access OR admin
   - SQLite JSON search for RBAC conditions

3. **Skill Ownership** (`skill_list_service.py`):
   - Write operations: creator OR admin/super_admin only
   - Created_by tracks ownership (username)

### Helper Functions
```python
def _is_admin_user(user: Optional[User]) -> bool:
    """Check if user has admin or super_admin role."""
    if not user or not user.roles:
        return False
    user_role_names = {role.name for role in user.roles}
    return bool(user_role_names & {"admin", "super_admin"})
```

### MCP Integration
- Uses `langchain-mcp-adapters` for MCP server communication
- Supports SSE and HTTPSTREAM transports
- Caches MCP clients and tools
- Tools accessible via `/api/v1/gateway/{name}/mcp/tools`

## Security Policy Summary

### Read Operations
- **Public resources**: All authenticated users
- **Private resources**: Owner, admin/super_admin, or ACL-granted users

### Write Operations
- **Resources**: Only owner can modify (update/delete)
- **ACL Rules**: Resource owner or admin/super_admin
- **Skills**: Only creator can modify (update/delete)

### Admin Privileges
Users with `admin` or `super_admin` roles have:
- Access to all resources (regardless of view_scope)
- Ability to modify ACL rules (for any resource)
- Access to all audit logs
- Full user/role/permission management

## API Endpoints Summary

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (invalidate refresh token)

### Resources
- `GET /api/v1/resources/` - List accessible resources
- `POST /api/v1/resources/` - Create resource (owner_id set to current user)
- `GET /api/v1/resources/{id}/` - Get resource (access controlled)
- `PUT /api/v1/resources/{id}/` - Update resource (owner only)
- `DELETE /api/v1/resources/{id}/` - Delete resource (owner only)

### ACL Rules
- `GET /api/v1/acl/resources/` - List accessible ACL rules
- `POST /api/v1/acl/resources/` - Create ACL rule (owner/admin)
- `GET /api/v1/acl/resources/{id}/` - Get ACL rule
- `PUT /api/v1/acl/resources/{id}/` - Update ACL rule (owner/admin)
- `DELETE /api/v1/acl/resources/{id}/` - Delete ACL rule (owner/admin)

### Gateway (Resource Invocation)
- `POST /api/v1/gateway/{name}` - Invoke resource with full control
- `GET /api/v1/gateway/{name}/get` - GET shortcut
- `POST /api/v1/gateway/{name}/post` - POST shortcut
- `GET /api/v1/gateway/{name}/{path:path}` - GET with path
- `POST /api/v1/gateway/{name}/{path:path}` - POST with path
- `PUT /api/v1/gateway/{name}/{path:path}` - PUT with path
- `DELETE /api/v1/gateway/{name}/{path:path}` - DELETE with path
- `POST /api/v1/gateway/{name}/mcp` - Call MCP server
- `GET /api/v1/gateway/{name}/mcp/tools` - List MCP tools

### Skills
- `GET /api/v1/skills/` - List skills (with filters)
- `POST /api/v1/skills/` - Create skill
- `GET /api/v1/skills/{id}/` - Get skill
- `PUT /api/v1/skills/{id}/` - Update skill (creator/admin only)
- `DELETE /api/v1/skills/{id}/` - Delete skill (creator/admin only)

### Skill Creator
- `POST /api/v1/skill-creator/` - Generate skill content from resources/skills

### Script
- `GET /api/v1/script/bash` - Download skillhub.sh CLI tool (no auth required)

### User Management
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{id}/` - Get user
- `PUT /api/v1/users/{id}/` - Update user
- `DELETE /api/v1/users/{id}/` - Delete user
- `GET /api/v1/roles/` - List roles
- `POST /api/v1/roles/` - Create role
- `GET /api/v1/permissions/` - List permissions

### API Keys
- `GET /api/v1/api-keys/` - List user's API keys
- `POST /api/v1/api-keys/` - Create API key
- `DELETE /api/v1/api-keys/{id}/` - Delete API key

### Audit Logs
- `GET /api/v1/audit-logs/` - List audit logs (own logs or admin)

## Important Notes

- **owner_id Tracking**: All resources have owner_id set to creating user (both public and private)
- **JWT Token Validity**: 60 minutes (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)
- **Refresh Token Validity**: 7 days (configurable via REFRESH_TOKEN_EXPIRE_DAYS)
- **SQLite to PostgreSQL**: Current implementation uses SQLite with JSON functions; migration to PostgreSQL requires updating JSON query syntax
- **MCP Client Caching**: MCP clients and tools are cached for performance
- **CLI Tool**: skillhub.sh supports third, gateway, and mcp resource types
