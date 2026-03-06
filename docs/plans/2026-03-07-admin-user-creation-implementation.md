# Admin User Creation Feature - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add admin-only user creation endpoint and modal UI for creating users with password, roles, and activation status.

**Architecture:** Single POST endpoint `/admin/users/` that creates user via AuthService.register() and assigns roles in one transaction. Frontend modal with form validation calls this endpoint and refreshes user list on success.

**Tech Stack:** FastAPI (backend), React + TypeScript (frontend), React Query, Pydantic schemas

---

## Task 1: Add AdminUserCreate Schema

**Files:**
- Modify: `backend/api/user_management.py` (add after line 83)

**Step 1: Add the AdminUserCreate schema**

```python
class AdminUserCreate(BaseModel):
    """Schema for admin user creation."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., format="email")
    password: str = Field(..., min_length=8, max_length=100)
    role_ids: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
```

**Step 2: Verify file compiles**

Run: `cd backend && python -c "from api.user_management import AdminUserCreate; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/api/user_management.py
git commit -m "feat: add AdminUserCreate schema

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Add AdminUserResponse Schema

**Files:**
- Modify: `backend/api/user_management.py` (add after UserResponse class around line 48)

**Step 1: Add AdminUserResponse schema**

```python
class AdminUserResponse(BaseModel):
    """Response with created user including roles."""
    id: str
    username: str
    email: str
    is_active: bool
    roles: List[RoleResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Verify file compiles**

Run: `cd backend && python -c "from api.user_management import AdminUserResponse; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/api/user_management.py
git commit -m "feat: add AdminUserResponse schema

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Write Backend Test for Create User Success

**Files:**
- Modify: `backend/tests/test_user_management_api.py`

**Step 1: Add failing test for user creation**

```python
def test_create_user_as_admin_success(client, admin_token, db_session):
    """Test admin can create user successfully."""
    # First get a valid role to assign
    role_response = client.get(
        "/admin/roles/list",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert role_response.status_code == 200
    roles = role_response.json()
    role_id = roles[0]["id"] if roles else None

    response = client.post(
        "/admin/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "role_ids": [role_id] if role_id else [],
            "is_active": True
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_user_management_api.py::test_create_user_as_admin_success -v`
Expected: FAIL with 404 Not Found (endpoint doesn't exist yet)

**Step 3: Commit test**

```bash
git add backend/tests/test_user_management_api.py
git commit -m "test: add failing test for admin create user

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Implement Create User Endpoint

**Files:**
- Modify: `backend/api/user_management.py` (add after require_admin function around line 95)

**Step 1: Implement the create_user endpoint**

```python
@router.post("/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user (admin-only).

    Args:
        user_data: User creation data with optional roles
        db: Database session
        current_user: Authenticated user (must be admin)

    Returns:
        Created user with assigned roles

    Raises:
        HTTPException 403: If user is not admin
        HTTPException 400: If username/email exists or roles not found
    """
    require_admin(current_user)

    # Import AuthService for user creation logic
    from services.auth_service import AuthService
    from schemas.auth import UserCreate as AuthUserCreate
    from core.exceptions import ValidationException

    # Create user using AuthService
    try:
        auth_data = AuthUserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        new_user = AuthService.register(db, auth_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Set is_active if provided
    if user_data.is_active is not None:
        new_user.is_active = user_data.is_active
        db.commit()

    # Assign roles if provided
    if user_data.role_ids:
        # Verify all roles exist
        roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        if len(roles) != len(user_data.role_ids):
            # Rollback user creation
            db.delete(new_user)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more roles not found"
            )

        # Assign roles
        new_user.roles = roles
        db.commit()
        db.refresh(new_user)

    # Eager load roles for response
    db.refresh(new_user)
    user_with_roles = db.query(User).options(selectinload(User.roles)).filter(User.id == new_user.id).first()

    return AdminUserResponse.model_validate(user_with_roles)
```

**Step 2: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_user_management_api.py::test_create_user_as_admin_success -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/api/user_management.py
git commit -m "feat: implement admin create user endpoint

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Write Backend Test for Duplicate Username

**Files:**
- Modify: `backend/tests/test_user_management_api.py`

**Step 1: Add failing test for duplicate username**

```python
def test_create_user_duplicate_username_fails(client, admin_token, db_session):
    """Test creating user with duplicate username fails."""
    # Create first user
    client.post(
        "/admin/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "duplicate",
            "email": "user1@example.com",
            "password": "securepass123"
        }
    )

    # Try to create with same username
    response = client.post(
        "/admin/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "duplicate",
            "email": "user2@example.com",
            "password": "securepass123"
        }
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
```

**Step 2: Run test**

Run: `cd backend && python -m pytest tests/test_user_management_api.py::test_create_user_duplicate_username_fails -v`
Expected: PASS (AuthService already handles this)

**Step 3: Commit**

```bash
git add backend/tests/test_user_management_api.py
git commit -m "test: add duplicate username validation test

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Write Backend Test for Non-Admin Access

**Files:**
- Modify: `backend/tests/test_user_management_api.py`

**Step 1: Add test for non-admin access denied**

```python
def test_create_user_non_admin_fails(client, user_token):
    """Test non-admin cannot create users."""
    response = client.post(
        "/admin/users/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "username": "shouldnotwork",
            "email": "fail@example.com",
            "password": "securepass123"
        }
    )

    assert response.status_code == 403
```

**Step 2: Run test**

Run: `cd backend && python -m pytest tests/test_user_management_api.py::test_create_user_non_admin_fails -v`
Expected: PASS (require_admin handles this)

**Step 3: Commit**

```bash
git add backend/tests/test_user_management_api.py
git commit -m "test: add non-admin access denied test

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Add useCreateUser Hook

**Files:**
- Modify: `frontend/src/hooks/use-user-management.ts`

**Step 1: Add useCreateUser hook**

```typescript
interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role_ids: string[];
  is_active: boolean;
}

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userData: CreateUserRequest) =>
      apiClient.post<User>('/admin/users/', userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/hooks/use-user-management.ts
git commit -m "feat: add useCreateUser hook

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Create CreateUserModal Component

**Files:**
- Create: `frontend/src/pages/users/components/CreateUserModal.tsx`

**Step 1: Write CreateUserModal component**

```typescript
import React, { useState } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { useCreateUser, useRoles } from '@/hooks/use-user-management';
import { cn } from '@/utils/cn';

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface FormData {
  username: string;
  email: string;
  password: string;
  role_ids: string[];
  is_active: boolean;
}

export const CreateUserModal: React.FC<Props> = ({
  open,
  onOpenChange,
  onSuccess
}) => {
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    password: '',
    role_ids: [],
    is_active: true
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [apiError, setApiError] = useState('');

  const { data: roles } = useRoles();
  const createUser = useCreateUser();

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.username || formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Valid email is required';
    }
    if (!formData.password || formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError('');

    if (!validateForm()) return;

    try {
      await createUser.mutateAsync(formData);
      onOpenChange(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        role_ids: [],
        is_active: true
      });
      onSuccess?.();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to create user';
      setApiError(message);
    }
  };

  const handleRoleToggle = (roleId: string) => {
    setFormData(prev => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId)
        ? prev.role_ids.filter(id => id !== roleId)
        : [...prev.role_ids, roleId]
    }));
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Modal */}
      <div className="relative bg-void-900 border border-void-700 rounded-lg shadow-xl w-full max-w-md mx-4 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-void-700">
          <h2 className="text-xl font-semibold text-gray-100">Create User</h2>
          <button
            onClick={() => onOpenChange(false)}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* API Error */}
          {apiError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {apiError}
            </div>
          )}

          {/* Username */}
          <div>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="Enter username"
              className={cn(errors.username && 'border-red-500')}
            />
            {errors.username && (
              <p className="text-sm text-red-400 mt-1">{errors.username}</p>
            )}
          </div>

          {/* Email */}
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="user@example.com"
              className={cn(errors.email && 'border-red-500')}
            />
            {errors.email && (
              <p className="text-sm text-red-400 mt-1">{errors.email}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Enter password (min 8 characters)"
                className={cn(errors.password && 'border-red-500', 'pr-10')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-sm text-red-400 mt-1">{errors.password}</p>
            )}
          </div>

          {/* Roles */}
          <div>
            <Label>Roles (Optional)</Label>
            <div className="mt-2 space-y-2 max-h-32 overflow-y-auto border border-void-700 rounded-lg p-3">
              {roles?.map((role) => (
                <label
                  key={role.id}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={formData.role_ids.includes(role.id)}
                    onChange={() => handleRoleToggle(role.id)}
                    className="w-4 h-4 rounded border-void-700 bg-void-800 text-cyber-primary focus:ring-cyber-primary"
                  />
                  <span className="text-sm text-gray-300">{role.name}</span>
                </label>
              ))}
              {(!roles || roles.length === 0) && (
                <p className="text-sm text-gray-500">No roles available</p>
              )}
            </div>
          </div>

          {/* Active Status */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isActive"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded border-void-700 bg-void-800 text-cyber-primary focus:ring-cyber-primary"
            />
            <Label htmlFor="isActive" className="cursor-pointer">
              Active (user can log in)
            </Label>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createUser.isPending}
              className="flex-1"
            >
              {createUser.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/pages/users/components/CreateUserModal.tsx
git commit -m "feat: add CreateUserModal component

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Export CreateUserModal from Components Index

**Files:**
- Modify: `frontend/src/pages/users/components/index.ts`

**Step 1: Add CreateUserModal export**

```typescript
export { UserTable } from './UserTable';
export { RoleManagerModal } from './RoleManagerModal';
export { CreateUserModal } from './CreateUserModal';
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/pages/users/components/index.ts
git commit -m "feat: export CreateUserModal from components index

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Update UsersPage to Add Create Button

**Files:**
- Modify: `frontend/src/pages/users/UsersPage.tsx`

**Step 1: Import CreateUserModal and add state**

Add to imports (around line 7):
```typescript
import { UserTable, RoleManagerModal, CreateUserModal } from './components';
```

Add state after existing state (around line 21):
```typescript
const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
```

**Step 2: Add Create User button to header**

Replace header section (around lines 73-83) with:
```typescript
{/* Header */}
<div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
  <div>
    <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
      Users & Roles
    </h1>
    <p className="font-mono text-sm text-gray-500">
      Manage users and their role assignments
    </p>
  </div>
  <Button onClick={() => setIsCreateModalOpen(true)}>
    Create User
  </Button>
</div>
```

**Step 3: Add success handler for modal**

Add after handleRoleAssignError (around line 52):
```typescript
const handleUserCreated = () => {
  setSuccessMessage('User created successfully!');
  setTimeout(() => setSuccessMessage(''), 3000);
};
```

**Step 4: Add CreateUserModal to JSX**

Add before RoleManagerModal (around line 163):
```typescript
{/* Create User Modal */}
<CreateUserModal
  open={isCreateModalOpen}
  onOpenChange={setIsCreateModalOpen}
  onSuccess={handleUserCreated}
/>
```

**Step 5: Verify TypeScript compiles**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: No errors

**Step 6: Commit**

```bash
git add frontend/src/pages/users/UsersPage.tsx
git commit -m "feat: add Create User button and modal to UsersPage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 11: Run All Backend Tests

**Files:** None (verification step)

**Step 1: Run all user management tests**

Run: `cd backend && python -m pytest tests/test_user_management_api.py -v`
Expected: All tests PASS

**Step 2: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All existing tests still PASS

---

## Task 12: Manual Testing

**Files:** None (manual verification)

**Step 1: Start backend server**

Run: `cd backend && python -m uvicorn main:app --reload`

**Step 2: Start frontend server**

Run: `cd frontend && pnpm dev`

**Step 3: Test the feature manually**

1. Login as admin user
2. Navigate to `/users`
3. Click "Create User" button
4. Fill in form with valid data
5. Select some roles
6. Click "Create User"
7. Verify: Modal closes, success message shows, new user appears in list
8. Try creating duplicate username - verify error shows
9. Try with invalid email - verify validation error

**Step 4: Verify role assignment**

1. Click role icon on newly created user
2. Verify assigned roles are shown

---

## Task 13: Final Integration Test

**Files:** None (verification step)

**Step 1: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v --cov=.</exec>

Run: `cd frontend && pnpm test`

**Step 2: Verify build succeeds**

Run: `cd frontend && pnpm build`
Expected: Build completes without errors

**Step 3: Final commit**

```bash
git add .
git commit -m "test: verify admin user creation feature complete

- All backend tests passing
- All frontend tests passing
- Build successful
- Manual testing complete

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

This implementation adds:
1. **Backend**: `POST /admin/users/` endpoint for creating users with roles
2. **Frontend**: CreateUserModal component with form validation
3. **Integration**: Create User button on UsersPage
4. **Tests**: Backend tests for success, duplicate username, and non-admin access

**Total estimated time:** 45-60 minutes
**Files modified:** 4 (2 backend, 2 frontend)
**Files created:** 2 (1 component, 1 plan doc)
