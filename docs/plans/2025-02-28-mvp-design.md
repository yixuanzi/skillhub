# SkillHub MVP Design Document

**Date**: 2025-02-28
**Author**: AI Assistant (Claude)
**Status**: Approved

---

## Overview

This document describes the simplified MVP architecture for SkillHub - an enterprise-level internal skill ecosystem platform. The MVP focuses on core functionality with minimal infrastructure complexity.

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ + FastAPI |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Database | SQLite (local file) |
| Storage | Local filesystem (`backend/artifacts/`) |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Single-process dev server |

---

## Phase 1 MVP Features

Based on the PRD Phase 1, the MVP includes:

1. **User Authentication & JWT Token Management**
   - User registration and login
   - JWT access tokens (15 min) + refresh tokens (7 days)
   - Password hashing with bcrypt

2. **Basic RBAC Permission System**
   - Users, Roles, Permissions model
   - Predefined roles: super_admin, admin, developer, operator, viewer
   - Role-based access to resources

3. **Skill Build & Publish**
   - Python code upload
   - Dependency management (requirements.txt)
   - Artifact packaging (ZIP storage)
   - Version control (semantic versioning)
   - Draft and publish workflow

4. **Simple Gateway Call Routing**
   - Unified `/gateway/call` endpoint
   - Skill execution via subprocess
   - Request/response standardization

5. **ACL Rules Management**
   - Access modes: `any` (public) and `rbac` (role-based)
   - Conditions: rate limiting, IP whitelist
   - Audit logging for all access attempts

6. **Basic Web Management UI**
   - Login/logout
   - Skill management dashboard
   - User/role management
   - ACL rule configuration

**Excluded from MVP:**
- Dify platform integration
- Third-party API URL resources
- Advanced ACL features (time windows, custom rules)
- Gray release / blue-green deployment

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────┐
│         React Frontend (port 5173)      │
│         Vite dev server with HMR        │
└─────────────────┬───────────────────────┘
                  │ HTTP (proxy)
┌─────────────────▼───────────────────────┐
│      FastAPI Backend (port 8000)        │
│  ┌────────────────────────────────────┐ │
│  │  Auth Module (JWT)                 │ │
│  │  - User login/logout               │ │
│  │  - Token generation/validation     │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  RBAC Module                       │ │
│  │  - User/Role/Permission management │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Skill Module                      │ │
│  │  - Build (code → artifact)         │ │
│  │  - Publish (version registry)      │ │
│  │  - Execute (subprocess call)       │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  ACL Module                        │ │
│  │  - Access control (Any/RBAC)       │ │
│  │  - Rate limiting                   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Gateway Module                    │ │
│  │  - Request routing                 │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         SQLite Database                 │
│  (users, roles, skills, artifacts, acl) │
└─────────────────────────────────────────┘
```

### Project Structure

```
skillhub/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings configuration
│   ├── database.py             # SQLAlchemy setup
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py             # User, Role, Permission
│   │   ├── skill.py            # Skill, SkillVersion, Artifact
│   │   └── acl.py              # ACLRule, AuditLog
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py             # LoginRequest, TokenResponse
│   │   ├── skill.py            # SkillCreate, SkillInvoke
│   │   └── acl.py              # ACLRuleCreate
│   ├── api/                    # API route handlers
│   │   ├── auth.py             # /auth/* endpoints
│   │   ├── skills.py           # /skills/* endpoints
│   │   ├── acl.py              # /acl/* endpoints
│   │   └── gateway.py          # /gateway/* endpoints
│   ├── services/               # Business logic
│   │   ├── auth_service.py     # JWT, password hashing
│   │   ├── skill_service.py    # Build, publish, execute
│   │   ├── acl_service.py      # Access control checks
│   │   └── gateway_service.py  # Request routing
│   ├── skills/                 # Built-in skills
│   ├── artifacts/              # Stored skill artifacts
│   ├── requirements.txt
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── pages/              # Route pages
│   │   ├── components/         # Reusable components
│   │   ├── api/                # API client
│   │   ├── types/              # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── data/                       # SQLite database
│   └── skillhub.db
│
├── docs/                       # Documentation
├── run.py                      # Single command start
└── README.md
```

---

## Database Schema

### Core Tables

**Users & Authentication:**
- `users` - User accounts
- `roles` - Role definitions
- `permissions` - Permission definitions
- `user_roles` - User-role associations
- `role_permissions` - Role-permission associations
- `refresh_tokens` - Token storage for revocation

**Skills:**
- `skills` - Skill metadata
- `skill_versions` - Version history

**Access Control:**
- `acl_rules` - ACL rule definitions
- `acl_rule_roles` - RBAC role mappings
- `audit_logs` - Access attempt logging

### Key Schema Features

- UUIDs for all primary keys
- JSON columns for flexible metadata (`metadata`, `conditions`, `permissions`)
- Cascade deletes for cleanup
- Indexes on frequently queried columns

---

## API Design

**Base URL:** `http://localhost:8000/api/v1`

### Endpoint Summary

| Category | Endpoints |
|----------|-----------|
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me` |
| Users | `/users`, `/users/{id}` |
| Roles | `/roles`, `/roles/{id}`, `/roles/{id}/permissions` |
| Skills | `/skills`, `/skills/{id}`, `/skills/{id}/build`, `/skills/{id}/publish`, `/skills/{id}/invoke` |
| ACL | `/acl/rules`, `/acl/rules/{id}`, `/acl/audit-logs` |
| Gateway | `/gateway/call` |

### Key Request/Response Format

**Gateway Call (Unified API):**
```json
// Request
POST /api/v1/gateway/call
{
  "skillId": "weather-forecast",
  "version": "1.0.0",
  "params": { "city": "Beijing", "days": 3 },
  "context": { "requestId": "req-12345" }
}

// Response (Success)
{
  "success": true,
  "data": { "forecast": [...] },
  "metadata": {
    "executionTime": 150,
    "version": "1.0.0",
    "cached": false
  },
  "requestId": "req-12345"
}

// Response (ACL Denied)
{
  "success": false,
  "error": {
    "code": "ACCESS_DENIED",
    "message": "You do not have permission to access this resource"
  },
  "requestId": "req-12345"
}
```

---

## Key Flows

### Skill Build Flow

```
1. User uploads Python code + requirements.txt
   └─> Validate syntax, dependencies

2. Create temporary build directory
   └─> Extract code, install requirements

3. Run tests (if present)
   └─> pytest discovery, execution

4. Package artifact (ZIP)
   └─> Store in backend/artifacts/

5. Create SkillVersion record (status=draft)
```

### Gateway Call with ACL

```
1. Verify JWT Token
   └─> Extract user_id, roles, permissions

2. Load ACL Rule for resource
   └─> Query acl_rules by resource_id

3. Check Access Mode
   └─> any: Check conditions (rate limit, IP)
   └─> rbac: Check user roles, permissions, conditions

4. Execute Skill
   └─> Load artifact, execute in subprocess

5. Log Audit, Return Response
```

---

## Development Workflow

```bash
# Development mode (with hot reload)
python run.py

# Or separately:
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Run tests
cd backend && pytest

# Build for production
cd frontend && npm run build
```

---

## Dependencies

### Backend (Python)
```
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
pytest
```

### Frontend (Node.js)
```
react
typescript
vite
tailwindcss
react-router-dom
axios
react-query
zustand
```

---

## Security Considerations

1. **Password Storage**: bcrypt hashing with salt
2. **JWT Tokens**: 15-minute access token, 7-day refresh token
3. **Token Storage**: Refresh tokens hashed in database
4. **Rate Limiting**: Per-resource configurable limits
5. **Audit Logging**: All access attempts logged
6. **CORS**: Configurable for production

---

## Future Enhancements (Post-MVP)

- PostgreSQL + Redis for production scale
- Multi-runtime support (Node.js, Go)
- Third-party API URL resources
- Dify platform integration
- Advanced ACL conditions
- Kubernetes deployment
- Monitoring and observability

---

## Appendix: Predefined Roles

| Role | Permissions |
|------|-------------|
| `super_admin` | Full access to all resources |
| `admin` | User management, skill management, configuration |
| `developer` | Skill build, publish, test |
| `operator` | Skill invocation, log viewing |
| `viewer` | Read-only access |

---

**Document Version**: 1.0
**Last Updated**: 2025-02-28
