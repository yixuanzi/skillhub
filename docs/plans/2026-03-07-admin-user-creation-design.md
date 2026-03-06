# Admin User Creation Feature - Design

**Date:** 2026-03-07
**Status:** Approved
**Author:** Claude

## Overview

Add a "Create User" button to the Users page that allows admins to directly create users with initial password, role assignment, and activation status in a single modal interface.

## Requirements

1. Admin can create users directly from the backend
2. Admin sets the initial password (communicated to user separately)
3. Roles can be assigned during user creation
4. Users are active by default (can be toggled)
5. Single atomic operation - user creation + role assignment

## Architecture

### Backend API

**New Endpoint:** `POST /admin/users/`

**Request Schema:**
```python
class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., format="email")
    password: str = Field(..., min_length=8, max_length=100)
    role_ids: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
```

**Response Schema:**
```python
class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    roles: List[RoleResponse]
    created_at: datetime
```

**Implementation:** Add to `backend/api/user_management.py`

### Frontend Components

**New Files:**
- `frontend/src/pages/users/components/CreateUserModal.tsx`

**Modified Files:**
- `frontend/src/pages/users/UsersPage.tsx` - Add "Create User" button
- `frontend/src/hooks/use-user-management.ts` - Add `useCreateUser` hook

**UI Layout:**
```
Users & Roles                    [Create User]
─────────────────────────────────────────────────

Modal:
┌──────────────────────────────────────┐
│ Create User                    [X]   │
├──────────────────────────────────────┤
│ Username: [_________________]        │
│ Email:    [_________________]        │
│ Password: [_______________] [👁]     │
│ Roles:    [Multi-select dropdown]    │
│ Active:   [✓] Toggle                │
│           [Cancel]  [Create User]   │
└──────────────────────────────────────┘
```

## Data Flow

```
Admin clicks "Create User"
    → Modal opens
    → Admin fills form (username, email, password, roles, active)
    → Client-side validation
    → POST /admin/users/
    → Backend: require_admin() → AuthService.register() → assign roles
    → Success response
    → Modal closes, success message, list refreshes
```

## Error Handling

| Error | Status | Display |
|-------|--------|---------|
| Username exists | 400 | "Username '{username}' already exists" |
| Email exists | 400 | "Email '{email}' already exists" |
| Invalid email | 422 | Field validation |
| Password too short | 422 | Field validation |
| Role not found | 404 | "One or more roles not found" |
| Not admin | 403 | "You don't have permission" |

## Security

- Admin-only access via `require_admin()` dependency
- Password hashing via `get_password_hash()`
- Username/email uniqueness validation
- Pydantic schema validation

## Testing

**Backend:**
- `test_create_user_as_admin_success()`
- `test_create_user_with_roles_success()`
- `test_create_user_duplicate_username_fails()`
- `test_create_user_duplicate_email_fails()`
- `test_create_user_non_admin_fails()`

**Frontend:**
- Modal open/close
- Form validation
- API submission
- Error handling
- Role selection
- Password visibility toggle
