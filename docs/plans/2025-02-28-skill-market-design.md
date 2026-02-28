# Skill Market Management Module - Design Document

**Date**: 2025-02-28
**Author**: Claude
**Status**: Approved

## Overview

Design and implementation of a skill market management module providing CRUD operations for managing AI agent skills. This module enables users to create, read, update, and delete skills with support for categorization, tagging, and versioning.

## Database Schema

### Table: skill_list

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PRIMARY KEY, UUID | Unique identifier |
| name | String(255) | UNIQUE, NOT NULL, INDEX | Skill name |
| desc | Text | NULLABLE | Description |
| content | Text | NULLABLE | Markdown documentation |
| author | String(255) | NOT NULL, INDEX | Author name |
| category | String(100) | NULLABLE, INDEX | Skill category |
| tags | String(500) | NULLABLE | Comma-separated tags |
| version | String(50) | DEFAULT "1.0.0" | Semantic version |
| create_time | DateTime | DEFAULT NOW() | Creation timestamp |
| last_time | DateTime | DEFAULT NOW(), ON UPDATE | Last update timestamp |

### Indexes
- `ix_skill_list_name` - UNIQUE index on name
- `ix_skill_list_category` - Index on category
- `ix_skill_list_author` - Index on author

## API Design

### Base Path
`/api/v1/skills`

### Endpoints

#### 1. Create Skill
**POST** `/api/v1/skills`

Request Body:
```json
{
  "name": "Data ETL Skill",
  "desc": "Extract, transform, load data",
  "content": "# Usage\n...",
  "author": "John Doe",
  "category": "data-processing",
  "tags": "etl,postgres,automation",
  "version": "1.0.0"
}
```

Response: `201 Created`
```json
{
  "id": "uuid-string",
  "name": "Data ETL Skill",
  "desc": "Extract, transform, load data",
  "content": "# Usage\n...",
  "author": "John Doe",
  "category": "data-processing",
  "tags": "etl,postgres,automation",
  "version": "1.0.0",
  "create_time": "2025-02-28T10:00:00Z",
  "last_time": "2025-02-28T10:00:00Z"
}
```

#### 2. List Skills
**GET** `/api/v1/skills?page=1&size=20&category=data-processing&tags=etl,postgres&author=John`

Query Parameters:
- `page` (optional): Page number, default 1, min 1
- `size` (optional): Items per page, default 20, min 1, max 100
- `category` (optional): Filter by category
- `tags` (optional): Filter by tags (comma-separated)
- `author` (optional): Filter by author

Response: `200 OK`
```json
{
  "items": [...],
  "total": 45,
  "page": 1,
  "size": 20
}
```

#### 3. Get Skill by ID
**GET** `/api/v1/skills/{id}`

Response: `200 OK` (skill object) or `404 Not Found`

#### 4. Update Skill
**PUT** `/api/v1/skills/{id}`

Request Body: All fields optional
```json
{
  "name": "Updated Name",
  "desc": "Updated description",
  "category": "new-category"
}
```

Response: `200 OK` (updated skill) or `404 Not Found`

#### 5. Delete Skill
**DELETE** `/api/v1/skills/{id}`

Response: `204 No Content` or `404 Not Found`

### Authentication
All endpoints require authentication via JWT token in `Authorization: Bearer <token>` header.

## File Structure

```
backend/
├── models/
│   ├── __init__.py          # Modified: Import SkillList
│   └── skill_list.py        # NEW: SkillList model
├── schemas/
│   └── skill_list.py        # NEW: Pydantic schemas
├── api/
│   └── skill_list.py        # NEW: FastAPI router
├── services/
│   └── skill_list_service.py # NEW: Business logic
├── tests/
│   └── test_skill_list.py   # NEW: Unit & integration tests
└── main.py                  # Modified: Register router
```

## Component Design

### 1. Model (models/skill_list.py)
- SQLAlchemy model with UUID primary key
- Hybrid properties if needed for JSON fields
- Table indexes for performance
- Follows existing resource model pattern

### 2. Schemas (schemas/skill_list.py)
Pydantic schemas:
- `SkillListBase` - Common fields
- `SkillListCreate` - Required fields for creation
- `SkillListUpdate` - All optional fields for updates
- `SkillListResponse` - Response with timestamps
- `SkillListListResponse` - Paginated list response

### 3. Service (services/skill_list_service.py)
Business logic methods:
- `create(db, data)` - Create with validation
- `get_by_id(db, id)` - Retrieve by ID
- `list_all(db, skip, limit)` - List with pagination
- `list_by_category(db, category, skip, limit)` - Filter by category
- `list_by_author(db, author, skip, limit)` - Filter by author
- `list_by_tags(db, tags, skip, limit)` - Filter by tags
- `update(db, id, data)` - Update with validation
- `delete(db, id)` - Delete by ID
- Helper methods for counting

### 4. API Router (api/skill_list.py)
FastAPI endpoints:
- All routes use `get_current_active_user` dependency
- Standard HTTP status codes (201, 200, 204, 400, 404)
- Proper error handling with HTTPException
- Pagination support with query parameters

## Error Handling

### Validation Rules
- **name**: Required, 1-255 chars, unique
- **author**: Required, 1-255 chars
- **desc**: Optional, max 10,000 chars
- **content**: Optional, max 100,000 chars
- **category**: Optional, max 100 chars
- **tags**: Optional, comma-separated, max 500 chars
- **version**: Optional, defaults to "1.0.0"

### Error Responses
- `400 Bad Request` - Validation errors (duplicate name, etc.)
- `404 Not Found` - Resource not found
- `401 Unauthorized` - Missing or invalid authentication
- `422 Unprocessable Entity` - Pydantic validation errors

### Custom Exceptions
Uses existing exceptions from `core/exceptions.py`:
- `ValidationException` - Business logic validation
- `NotFoundException` - Resource not found

## Testing Strategy

### Unit Tests (Service Layer)
- Create skill with valid data
- Create skill fails with duplicate name
- Get skill by ID (found and not found)
- List skills with pagination
- List skills filtered by category, author, tags
- Update skill (partial and full updates)
- Update skill fails with duplicate name
- Delete skill (success and not found)

### Integration Tests (API Layer)
- POST /api/v1/skills - 201 Created, 400 Duplicate
- GET /api/v1/skills - 200 With pagination and filters
- GET /api/v1/skills/{id} - 200 Found, 404 Not found
- PUT /api/v1/skills/{id} - 200 Updated, 404 Not found
- DELETE /api/v1/skills/{id} - 204 Success, 404 Not found
- All endpoints - 401 Unauthorized

### Test Fixtures
- `db` - Database session
- `client` - FastAPI test client
- `test_user` - Authenticated user
- `auth_headers` - Headers with JWT token

## Implementation Notes

1. **Follow existing patterns**: Mirror the resource module implementation exactly
2. **Authentication**: All endpoints require `get_current_active_user` dependency
3. **Validation**: Use Pydantic for request validation, custom exceptions for business logic
4. **Database**: Use SQLAlchemy ORM with UUID primary keys
5. **Timestamps**: Use `create_time` and `last_time` field names as specified
6. **Tags**: Store as comma-separated string (simpler than JSON array for querying)

## Success Criteria

- ✅ All CRUD endpoints working correctly
- ✅ Authentication required for all operations
- ✅ Proper validation and error handling
- ✅ Pagination and filtering working
- ✅ Test coverage > 80%
- ✅ Consistent with existing codebase patterns
