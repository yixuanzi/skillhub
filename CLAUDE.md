# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillHub is an enterprise-level internal skill ecosystem platform for managing, publishing, and calling AI agent skills. It provides a complete skill lifecycle management system including build, publish, call control, and permission management.

## Architecture

This is a **microservices architecture** with multiple languages:

- **Frontend**: React 18 + TypeScript (monorepo with Turborepo/pnpm)
  - `frontend/apps/web` - User-facing web application
  - `frontend/apps/admin` - Admin dashboard
  - `frontend/packages/` - Shared packages (ui, api-client, types)

- **Backend Services**:
  - `services/auth-service/` - Node.js + Express + Passport.js (authentication)
  - `services/skill-service/` - Go + Gin + GORM (skill management)
  - `services/acl-service/` - Go + Gin + Casbin (access control)
  - `services/gateway/` - Go (API gateway)

- **Data Layer**:
  - PostgreSQL 15+ (primary database with JSONB, full-text search)
  - Redis 7.x (cache, sessions, ACL cache)
  - MinIO/S3 (object storage for build artifacts)

- **Infrastructure**:
  - Kong Gateway (API gateway)
  - Dify (self-hosted for API orchestration and LLM integration)
  - Kubernetes (container orchestration)

## Core Concepts

### Skill Types
- `business_logic` - Custom business logic
- `api_proxy` - API proxy endpoints
- `ai_llm` - AI/LLM integrations
- `data_processing` - Data transformation skills

### Skill Runtimes
- Node.js (18/20 LTS)
- Python (3.11/3.12)
- Go (1.22+)

### Access Control Modes
- `any` - Public access (no authentication required)
- `rbac` - Role-based access control (requires authentication + permissions)

## Development Commands

### Frontend (React + TypeScript)
```bash
cd frontend
pnpm install          # Install dependencies
pnpm dev              # Start development server
pnpm build            # Build for production
pnpm test             # Run tests
pnpm test:e2e         # Run E2E tests
pnpm lint             # Lint code
pnpm format           # Format code
```

### Node.js Services (Auth Service)
```bash
cd services/auth-service
npm run dev           # Start development server with hot reload
npm run build         # Build TypeScript
npm start             # Start production server
npm test              # Run tests
npm run lint          # Lint code
npm run format        # Format code
```

### Go Services (Skill, ACL, Gateway)
```bash
cd services/skill-service  # or acl-service, gateway
go run cmd/server/main.go  # Run development server
go build -o bin/server cmd/server/main.go  # Build
go test ./... -v           # Run tests
go test ./... -coverprofile=coverage.out  # Test coverage
go tool cover -html=coverage.out          # View coverage
golangci-lint run         # Lint code
go fmt ./...              # Format code
```

### Database Migrations
```bash
# Using golang-migrate
migrate -database $DATABASE_URL -path migrations up    # Apply migrations
migrate -database $DATABASE_URL -path migrations down  # Rollback one
migrate -database $DATABASE_URL -path migrations version  # Check version

# Or via Makefile (if exists)
make migrate-up
make migrate-down
```

### Development Environment
```bash
docker-compose up -d     # Start PostgreSQL, Redis, MinIO
```

## Code Organization

### Frontend Structure (React)
- Components use PascalCase naming: `UserCard.tsx`
- Co-located files: `UserCard/index.tsx`, `UserCard/UserCard.test.tsx`
- React Query for data fetching with hooks: `useSkills()`, `useUsers()`
- Zustand for state management
- Zod for validation

### Node.js Service Structure
- `src/app.ts` - Application entry point
- `src/controllers/` - HTTP request handlers
- `src/services/` - Business logic
- `src/models/` - Data models (Prisma)
- `src/middleware/` - Express middleware
- `src/routes/` - Route definitions

### Go Service Structure
- `cmd/server/main.go` - Application entry point
- `internal/handlers/` - HTTP handlers (Gin)
- `internal/services/` - Business logic
- `internal/models/` - Data models (GORM)
- `internal/repository/` - Data access layer
- `internal/middleware/` - Gin middleware
- `pkg/` - Reusable packages

## API Design

- RESTful design with `/api/v1/` prefix
- Standardized response format:
  - Success: `{"success": true, "data": {...}}`
  - Error: `{"success": false, "error": {"code": "...", "message": "...", "details": [...]}}`
- JWT authentication via `Authorization: Bearer <token>` header
- Input validation with Zod (Node.js) or validator (Go)

## Git Workflow

- Main branch: `main`
- Development branch: `develop`
- Feature branches: `feature/TICKET-123-description`
- Bugfix branches: `bugfix/TICKET-456-description`
- Hotfix branches: `hotfix/TICKET-789-description`

Conventional Commits format:
```
feat(scope): description
fix(scope): description
docs: description
test: description
```

## Key Design Patterns

### RBAC Permission Model
- Users have Roles
- Roles have Permissions
- Permissions apply to Resources
- ACL rules support `any` or `rbac` modes with conditional constraints (rate limits, IP whitelist, time windows)

### Skill Lifecycle
1. **Build**: Code upload → validation → dependency install → test → store artifact
2. **Publish**: Version generation → metadata registration → gateway routing config
3. **Call**: Gateway → Auth verify → ACL check → Registry lookup → Dify → execution

### Multi-tenancy
- PostgreSQL row-level security for data isolation
- Namespace/resource-based scoping

## Testing

- Target test coverage: > 80%
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical user flows

## Documentation

- `docs/architecture.md` - System architecture with detailed component descriptions
- `docs/development.md` - Detailed development guide with examples
- `docs/tech-stack.md` - Technology choices and rationale
- `docs/api-design.md` - API specifications
- `docs/data-model.md` - Database schema
- `docs/security.md` - Security design

## Important Notes

- **Currently in early design/planning phase** - source code structure may not yet exist
- All backend services are stateless for horizontal scaling
- JWT tokens have 15-minute validity (refreshable)
- Dify integration is self-hosted for internal API orchestration
- Skills are stored as build artifacts (Docker images or ZIP packages)
