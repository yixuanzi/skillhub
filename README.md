# SkillHub

> Enterprise-Grade Internal Skill Ecosystem Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

SkillHub is an enterprise-grade internal skill ecosystem platform designed to provide unified capabilities for skill building, publishing, and invocation management.

## Table of Contents

- [Core Features](#core-features)
- [Technical Architecture](#technical-architecture)
- [Quick Start](#quick-start)
- [Development Guide](#development-guide)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Related Documentation](#related-documentation)

---

## Core Features

### 1. Skill Build & Publish

- Support for multiple runtimes: Node.js, Python, Go
- Complete skill lifecycle management
- Code validation, dependency resolution, and testing
- Version control and canary deployment

### 2. Unified Gateway Invocation

- Single entry point for all skill invocations
- JWT authentication + RBAC access control
- Support for internal hosted APIs, internal standalone APIs, and third-party APIs

### 3. Access Control List (ACL)

- `any` mode: Public access (supports rate limiting, IP whitelist, etc.)
- `rbac` mode: Role-based access control (supports user/role whitelists)

### 4. Managed Application Tokens (MToken)

- Automatic third-party API token management
- Encrypted token storage and auto-refresh

### 5. Skill Market

- Skill publishing and discovery
- Support for categories and tags

---

## Technical Architecture

### Frontend

```
React 18 + TypeScript
├── Vite 5 - Build tool
├── React Router 6 - Routing
├── React Query - Data fetching
├── Zustand - State management
└── Tailwind CSS - Styling
```

### Backend

```
Python 3.11+ + FastAPI
├── SQLAlchemy 2.0 - ORM
├── Pydantic 2.0 - Data validation
├── JWT - User authentication
└── SQLite/PostgreSQL - Data storage
```

### Resource Types

| Type | Description | Example |
|-----|-------------|---------|
| `gateway` | Gateway resources with path proxy support | Internal API proxy |
| `third` | Third-party API resources | OpenAI, Salesforce |
| `mcp` | MCP server resources | Dify, n8n |

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yixuanzi/skillhub.git
cd skillhub

# Start services (includes frontend and backend)
docker-compose -f docker-compose-dev.yml up -d

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Installation

#### 1. Backend Service

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py
python scripts/seed_db.py

# Start service
python main.py
```

#### 2. Frontend Service

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 3. Using Start Script

```bash
# Run from project root
./start.sh
```

---

## Development Guide

### Environment Variables

Create `backend/.env` file:

```bash
# Database configuration
DATABASE_URL=sqlite:///./data/skillhub.db

# JWT secret key (change in production)
SECRET_KEY=your-secret-key-change-in-production

# Token expiration time
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS configuration
CORS_ORIGINS=http://localhost:5173,http://localhost:80

# Server configuration
SKILL_HOST=0.0.0.0
SKILL_PORT=8000
SKILLHUB_URL=http://localhost:8000
```

### Default Account

After initialization, use the following default account to login:

```
Username: admin
Password: admin123
```

### CLI Tool Usage

```bash
# Download CLI tool
curl http://localhost:8000/api/v1/script/bash -o skillhub.sh
chmod +x skillhub.sh

# Call third-party API
./skillhub.sh third weather-api -method GET -inputs '{"city":"Beijing"}'

# Call gateway resource
./skillhub.sh gateway backend-api -method GET -path users/123

# Call MCP server
./skillhub.sh mcp my-mcp-server -mcptool tool_name
```

---

## Project Structure

```
skillhub/
├── backend/                    # Backend service
│   ├── api/                    # API routes
│   ├── services/               # Business logic
│   ├── models/                 # Data models (SQLAlchemy)
│   ├── schemas/                # Data validation (Pydantic)
│   ├── core/                   # Core functionality
│   ├── middleware/             # Middleware
│   ├── scripts/                # Utility scripts
│   ├── tests/                  # Test files
│   ├── main.py                 # Application entry
│   └── config.py               # Configuration
│
├── frontend/                   # Frontend application
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   ├── store/              # State management
│   │   └── utils/              # Utility functions
│   ├── public/                 # Static assets
│   └── package.json
│
├── docs/                       # Project documentation
│   ├── architecture.md         # System architecture
│   ├── api-design.md           # API design
│   ├── data-model.md           # Data model
│   ├── security.md             # Security design
│   └── PRD.md                  # Product requirements
│
├── docker/                     # Docker configuration
├── docker-compose-dev.yml      # Development environment
├── docker-compose-prod.yml     # Production environment
├── Dockerfile                  # Image build
├── start.sh                    # Startup script
├── CLAUDE.md                   # Claude Code guide
└── README.md                   # This file
```

---

## API Documentation

### Authentication Methods

Two authentication methods are supported:

1. **JWT Token** (recommended for users)
   ```bash
   curl -H "Authorization: Bearer <jwt_token>" http://localhost:8000/api/v1/resources/
   ```

2. **API Key** (recommended for application integration)
   ```bash
   curl -H "X-API-Key: <api_key>" http://localhost:8000/api/v1/resources/
   ```

### Main API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/resources/` | GET/POST | Resource list/create |
| `/api/v1/acl/resources/` | GET/POST | ACL rule management |
| `/api/v1/gateway/{name}` | POST | Invoke resource |
| `/api/v1/skills/` | GET/POST | Skill market |
| `/api/v1/skill-creator/` | POST | Generate skill content |
| `/api/v1/script/bash` | GET | Get CLI tool |

Complete API documentation: `http://localhost:8000/docs`

---

## Deployment

### Production Deployment

#### Using Docker

```bash
# Use production configuration
docker-compose -f docker-compose-prod.yml up -d
```

#### Manual Deployment

Backend with Gunicorn + Uvicorn Workers:

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

Frontend build:

```bash
cd frontend
npm run build
# Output in frontend/dist/
```

### System Requirements

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ (recommended for production) |

---

## Related Documentation

- [CLAUDE.md](./CLAUDE.md) - Claude Code development guide
- [backend/README.md](./backend/README.md) - Backend service detailed documentation
- [frontend/README.md](./frontend/README.md) - Frontend application detailed documentation
- [docs/PRD.md](./docs/PRD.md) - Product requirements document
- [docs/architecture.md](./docs/architecture.md) - System architecture design
- [docs/api-design.md](./docs/api-design.md) - API interface design
- [docs/security.md](./docs/security.md) - Security design

---

## Tech Stack

### Backend
- FastAPI - Modern high-performance web framework
- SQLAlchemy - ORM toolkit
- Pydantic - Data validation
- JWT - User authentication
- SQLite/PostgreSQL - Data storage

### Frontend
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- React Query - Data fetching
- Zustand - State management
- Tailwind CSS - Styling framework

---

## License

[MIT License](LICENSE)

---

**Last Updated**: 2026-03-13
