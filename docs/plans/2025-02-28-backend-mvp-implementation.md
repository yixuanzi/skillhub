# SkillHub Backend MVP Implementation Design

**Date**: 2025-02-28
**Author**: AI Assistant (Claude)
**Status**: Approved

---

## Overview

This document describes the implementation design for the SkillHub MVP backend service - a FastAPI-based REST API providing authentication, skill management, access control, and gateway routing capabilities.

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.104+ |
| Python | 3.11+ |
| Database | SQLite with SQLAlchemy 2.0 |
| Auth | JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |
| Server | uvicorn (dev) |

---

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI Routes)      │  ← Request handling, validation
├─────────────────────────────────────────┤
│      Service Layer (Business Logic)     │  ← Core operations, orchestration
├─────────────────────────────────────────┤
│         Data Layer (SQLAlchemy)         │  ← Database operations
└─────────────────────────────────────────┘
```

### Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── config.py               # Pydantic settings
├── database.py             # SQLAlchemy setup
├── requirements.txt
│
├── models/                 # SQLAlchemy ORM models
│   ├── user.py            # User, Role, Permission, RefreshToken
│   ├── skill.py           # Skill, SkillVersion
│   └── acl.py             # ACLRule, AuditLog
│
├── schemas/                # Pydantic schemas
│   ├── auth.py            # Auth request/response
│   ├── skill.py           # Skill request/response
│   ├── acl.py             # ACL request/response
│   └── common.py          # Shared schemas
│
├── api/                    # API route handlers
│   ├── auth.py            # /auth/* endpoints
│   ├── users.py           # /users/* endpoints
│   ├── roles.py           # /roles/* endpoints
│   ├── skills.py          # /skills/* endpoints
│   ├── acl.py             # /acl/* endpoints
│   └── gateway.py         # /gateway/* endpoints
│
├── services/               # Business logic
│   ├── auth_service.py    # JWT, password operations
│   ├── skill_service.py   # Build, publish, execute
│   ├── acl_service.py     # Access control checks
│   └── gateway_service.py # Request routing
│
├── core/                   # Core utilities
│   ├── security.py        # JWT, password helpers
│   ├── deps.py            # FastAPI dependencies
│   └── exceptions.py      # Custom exceptions
│
├── tests/                  # Pytest tests
│   ├── conftest.py        # Test fixtures
│   ├── test_auth.py
│   ├── test_skills.py
│   ├── test_acl.py
│   └── test_gateway.py
│
├── scripts/                # Utility scripts
│   ├── init_db.py         # Database initialization
│   └── seed_db.py         # Seed initial data
│
├── artifacts/              # Skill artifacts (ZIP files)
└── data/                   # SQLite database
```

---

## Database Schema

### User & Authentication Tables

**users**
- `id` (UUID, PK)
- `username` (String, unique)
- `email` (String, unique)
- `hashed_password` (String)
- `is_active` (Boolean, default True)
- `created_at` (DateTime)

**roles**
- `id` (UUID, PK)
- `name` (String, unique)
- `description` (String)
- `created_at` (DateTime)

**permissions**
- `id` (UUID, PK)
- `resource` (String)  # e.g., "skills", "users"
- `action` (String)     # e.g., "read", "write", "delete"

**user_roles** (Junction)
- `user_id` (UUID, FK)
- `role_id` (UUID, FK)

**role_permissions** (Junction)
- `role_id` (UUID, FK)
- `permission_id` (UUID, FK)

**refresh_tokens**
- `id` (UUID, PK)
- `token_hash` (String)  # Hashed token
- `user_id` (UUID, FK)
- `expires_at` (DateTime)
- `created_at` (DateTime)

### Skill Tables

**skills**
- `id` (UUID, PK)
- `name` (String, unique)
- `description` (String)
- `skill_type` (String)  # business_logic, api_proxy, ai_llm, data_processing
- `runtime` (String)     # python, nodejs, go
- `created_by` (UUID, FK → users)
- `created_at` (DateTime)

**skill_versions**
- `id` (UUID, PK)
- `skill_id` (UUID, FK)
- `version` (String)     # Semantic versioning
- `status` (String)      # draft, published
- `artifact_path` (String)  # Path to ZIP file
- `build_log` (String)   # Build output
- `published_at` (DateTime, nullable)
- `created_at` (DateTime)

### Access Control Tables

**acl_rules**
- `id` (UUID, PK)
- `resource_id` (String, unique)
- `resource_name` (String)
- `access_mode` (String)  # any, rbac
- `conditions` (JSON)     # {rateLimit, ipWhitelist}
- `created_at` (DateTime)

**acl_rule_roles** (Junction)
- `acl_rule_id` (UUID, FK)
- `role_id` (UUID, FK)
- `permissions` (JSON array)  # ["read", "write"]

**audit_logs**
- `id` (UUID, PK)
- `timestamp` (DateTime)
- `user_id` (UUID, nullable)
- `username` (String, nullable)
- `resource_id` (String)
- `access_mode` (String)
- `result` (String)  # allow, deny
- `ip_address` (String)
- `request_id` (String)

### Key Schema Features

- UUID primary keys for all tables
- JSON columns for flexible metadata
- Cascade deletes for relationships
- Indexes on frequently queried columns
- Foreign key constraints

---

## API Endpoints

### Base URL
`http://localhost:8000/api/v1`

### Authentication (`/auth/`)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/register` | No | User registration |
| POST | `/login` | No | User login (returns JWT) |
| POST | `/refresh` | No | Refresh access token |
| POST | `/logout` | Yes | Invalidate refresh token |
| GET | `/me` | Yes | Get current user info |

### Users (`/users/`)

| Method | Endpoint | Permissions | Description |
|--------|----------|-------------|-------------|
| GET | `/` | Admin | List users (paginated) |
| POST | `/` | Admin | Create user |
| GET | `/{id}` | - | Get user details |
| PUT | `/{id}` | Admin | Update user |
| DELETE | `/{id}` | Super Admin | Delete user |

### Roles (`/roles/`)

| Method | Endpoint | Permissions | Description |
|--------|----------|-------------|-------------|
| GET | `/` | - | List all roles |
| POST | `/` | Admin | Create role |
| GET | `/{id}` | - | Get role details |
| PUT | `/{id}` | Admin | Update role |
| DELETE | `/{id}` | Admin | Delete role |

### Skills (`/skills/`)

| Method | Endpoint | Permissions | Description |
|--------|----------|-------------|-------------|
| GET | `/` | - | List skills (paginated) |
| POST | `/` | Developer | Create skill metadata |
| GET | `/{id}` | - | Get skill details |
| POST | `/{id}/build` | Developer | Build skill from code |
| POST | `/{id}/publish` | Developer | Publish skill version |
| GET | `/{id}/versions` | - | List skill versions |
| POST | `/{id}/invoke` | Operator | Direct skill invocation |

### ACL (`/acl/`)

| Method | Endpoint | Permissions | Description |
|--------|----------|-------------|-------------|
| GET | `/rules` | - | List ACL rules |
| POST | `/rules` | Admin | Create ACL rule |
| GET | `/rules/{id}` | - | Get rule details |
| PUT | `/rules/{id}` | Admin | Update rule |
| DELETE | `/rules/{id}` | Admin | Delete rule |
| GET | `/audit-logs` | Admin | Query audit logs |

### Gateway (`/gateway/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/call` | Unified skill invocation with ACL check |

---

## Security Design

### JWT Token Handling

**Important:** JWT tokens are stored and transmitted using only the last 32 characters.

**Access Token:**
- Algorithm: HS256
- Expiration: 15 minutes
- Payload: user_id, username, roles, exp, iat
- Storage: Client-side (sent in Authorization header)

**Token Processing:**
- On generation: Create full JWT, extract last 32 chars for response
- On validation: Receive 32 chars, reconstruct full token for validation
- This provides an additional layer of token obfuscation

### Authentication Flow

```
1. User Registration
   POST /auth/register
   → Create user with bcrypt password
   → Return user info

2. Login
   POST /auth/login
   → Validate credentials
   → Generate access_token + refresh_token
   → Return last 32 chars of each token

3. Authenticated Request
   Authorization: Bearer <last_32_chars>
   → Reconstruct full token
   → Validate signature + expiration
   → Extract user info

4. Refresh
   POST /auth/refresh
   → Validate refresh_token (last 32 chars)
   → Generate new access_token
   → Rotate refresh_token

5. Logout
   POST /auth/logout
   → Delete refresh_token from DB
```

### Access Control Flow

```
Request → JWT Validation → Load User + Roles
                ↓
        Get ACL Rule for Resource
                ↓
        ┌───────┴────────┐
        ↓                ↓
   Mode: ANY        Mode: RBAC
        ↓                ↓
  Check Conditions  Check User Roles
  (rate limit, IP)  → Permissions
        │                │
        └────────┬───────┘
                 ↓
         Audit Log (allow/deny)
                 ↓
         Return Response or 403
```

### Security Measures

1. **Passwords:** bcrypt with salt (12 rounds)
2. **Tokens:** Hashed in database for refresh tokens
3. **Rate Limiting:** Per-resource configurable limits
4. **IP Whitelisting:** Optional ACL condition
5. **CORS:** Configurable origins
6. **Input Validation:** Pydantic schemas
7. **Audit Logging:** All access attempts logged
8. **SQL Injection Prevention:** SQLAlchemy parameterized queries

---

## Error Handling

### Exception Hierarchy

```python
class SkillHubException(Exception):
    """Base exception for all custom errors"""

class AuthException(SkillHubException):
    """Authentication/authorization errors"""

class NotFoundException(SkillHubException):
    """Resource not found"""

class ValidationException(SkillHubException):
    """Input validation errors"""

class BusinessException(SkillHubException):
    """Business logic errors (build failed, execution error)"""
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### Common Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| AUTH_FAILED | 401 | Authentication failed |
| INVALID_TOKEN | 401 | Token invalid |
| TOKEN_EXPIRED | 401 | Token expired |
| ACCESS_DENIED | 403 | Permission denied |
| RESOURCE_NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 422 | Input validation failed |
| BUILD_FAILED | 422 | Skill build failed |
| SKILL_EXECUTION_ERROR | 500 | Skill execution error |
| INTERNAL_ERROR | 500 | Server error |

---

## Testing Strategy

### Test Coverage Areas

**Unit Tests (services/):**
- Password hashing (bcrypt)
- JWT token generation/validation (with last-32-chars logic)
- Permission checking logic
- ACL rule evaluation
- Skill build validation

**Integration Tests (api/):**
- Complete auth flow (register → login → refresh → logout)
- User/role management with RBAC
- Skill lifecycle (create → build → publish → invoke)
- ACL enforcement (allow/deny scenarios)
- Gateway invocation with various ACL modes

### Test Fixtures (conftest.py)

- Test database (SQLite in-memory)
- Sample users: super_admin, admin, developer, operator, viewer
- Sample roles with permissions
- Sample skills with versions
- Sample ACL rules (any and rbac modes)

---

## Skill Build & Execution

### Build Process

```
1. Upload Code (multipart/form-data)
   ├── code_file: Python script
   ├── requirements_file: requirements.txt
   └── version: "1.0.0"

2. Validation
   ├── Validate Python syntax
   ├── Parse requirements.txt
   └── Check version format

3. Build
   ├── Create temp directory
   ├── Extract code + requirements
   ├── Install dependencies (pip install -r requirements.txt)
   ├── Run tests (if present)
   └── Package as ZIP artifact

4. Store
   ├── Save ZIP to backend/artifacts/
   └── Create SkillVersion record (status=draft)

5. Response
   └── Return version info + build log
```

### Execution Process

```
1. Load SkillVersion
   └── Get artifact_path

2. Extract Artifact
   └── Unzip to temp directory

3. Execute
   ├── subprocess.run([python, skill.py, --params, json_params])
   └── Capture stdout/stderr

4. Response
   └── Return result + execution_time
```

---

## Database Seeding

### Seed Data Contents

**Default Roles:**
1. `super_admin` - Full access to all resources
2. `admin` - User management, skill management, configuration
3. `developer` - Skill build, publish, test
4. `operator` - Skill invocation, log viewing
5. `viewer` - Read-only access

**Default Admin User:**
- Username: `admin`
- Password: `admin123` (change on first login)
- Role: `super_admin`

**Sample Skills:**
- `hello-world` - Simple greeting skill
- `calculator` - Basic math operations

**Sample ACL Rules:**
- Public access to hello-world (mode: any)
- RBAC for calculator (mode: rbac)

---

## Implementation Order

1. **Phase 1: Infrastructure**
   - Database setup (models, migrations)
   - Configuration management
   - Core utilities (security, exceptions)

2. **Phase 2: Authentication**
   - User model + CRUD
   - JWT token handling (with last-32-chars logic)
   - Auth endpoints (register, login, refresh, logout, me)

3. **Phase 3: RBAC**
   - Role/Permission models
   - User-role assignment
   - Role management endpoints
   - Permission checking service

4. **Phase 4: Skills**
   - Skill/SkillVersion models
   - Skill build service
   - Skill management endpoints

5. **Phase 5: ACL**
   - ACLRule/AuditLog models
   - ACL checking service
   - ACL management endpoints

6. **Phase 6: Gateway**
   - Gateway service (orchestration)
   - Gateway endpoint (unified invocation)

7. **Phase 7: Testing**
   - Unit tests for each service
   - Integration tests for each module
   - End-to-end tests

8. **Phase 8: Scripts**
   - Database initialization script
   - Database seeding script

---

## Dependencies

### Backend (Python)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

---

## Development Commands

```bash
# Development server
uvicorn main:app --reload --port 8000

# Run tests
pytest -v

# Test coverage
pytest --cov=. --cov-report=html

# Initialize database
python scripts/init_db.py

# Seed database
python scripts/seed_db.py
```

---

## Environment Variables

```bash
DATABASE_URL=sqlite:///./data/skillhub.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:5173"]
```

---

## Future Enhancements

Post-MVP improvements:
- PostgreSQL + Redis for production
- Async database operations
- Background task queue for builds
- Skill execution timeout and resource limits
- Metrics and monitoring
- WebSocket support for real-time updates

---

**Document Version**: 1.0
**Last Updated**: 2025-02-28
