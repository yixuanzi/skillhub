# Phase 1.1b QA Readiness Checklist

## Purpose
This checklist verifies that Phase 1.1b features are fully implemented and ready for E2E testing.

## Backend Readiness

### Resource Model (`backend/models/resource.py`)
- [ ] `ResourceType` enum includes `MCP = "mcp"`
- [ ] `view_scope` column exists (String, Enum: public/private)
- [ ] `owner_id` column exists (String, ForeignKey to users)
- [ ] `api_description` column exists (Text, nullable)
- [ ] Database migration applied successfully

### Resource Schemas (`backend/schemas/resource.py`)
- [ ] `ResourceCreate` schema includes:
  - [ ] `view_scope: ViewScope` (required)
  - [ ] `owner_id: str` (optional, defaults to current user)
  - [ ] `api_description: str` (optional)
  - [ ] `mcp_config: McpConfig` (optional for type=mcp)
- [ ] `McpConfig` schema defined with:
  - [ ] `transport: Literal['stdio', 'sse', 'ws']`
  - [ ] `command: str` (for stdio)
  - [ ] `args: list[str]` (for stdio)
  - [ ] `env: dict[str, str]` (for stdio)
  - [ ] `timeout: int` (optional)
  - [ ] `endpoint: str` (for sse/ws)

### MCP Service (`backend/services/mcp_service.py`)
- [ ] `MCPService.create()` creates MCP config
- [ ] `MCPService.call()` executes MCP server commands
- [ ] `MCPService.resolve_tokens()` replaces ${token:name} placeholders
- [ ] Handles stdio transport (subprocess execution)
- [ ] Handles sse/ws transport (HTTP/WebSocket calls)
- [ ] Timeout enforcement works correctly
- [ ] Error handling for invalid commands

### Resource Service (`backend/services/resource_service.py`)
- [ ] `ResourceService.create()` sets owner_id to current user
- [ ] `ResourceService.list_accessible()` filters by view_scope
- [ ] `ResourceService.get_accessible()` checks visibility + ACL
- [ ] Public resources visible to all authenticated users
- [ ] Private resources only visible to owner or ACL-authorized users

### ACL Service (`backend/services/acl_resource_service.py`)
- [ ] `ACLResourceService.check_permission()` integrates with view_scope
- [ ] `ACLResourceService.get_accessibility_info()` returns visibility info
- [ ] ACL rules work with both public and private resources

### Resource API (`backend/api/resource.py`)
- [ ] POST `/api/v1/resources` accepts MCP resources
- [ ] GET `/api/v1/resources` respects view_scope filtering
- [ ] GET `/api/v1/resources/{id}` enforces visibility
- [ ] GET `/api/v1/resources/{id}/accessibility` endpoint exists
- [ ] PUT/DELETE endpoints enforce ownership/admin checks

### User Management API (`backend/api/user_management.py`)
- [ ] GET `/api/v1/users` lists users (admin-only)
- [ ] GET `/api/v1/users/{id}/roles` returns user roles (admin-only)
- [ ] PUT `/api/v1/users/{id}/roles` assigns roles (admin-only)
- [ ] PUT `/api/v1/users/{id}/deactivate` deactivates user (admin-only)
- [ ] GET `/api/v1/users/roles/` lists all roles (admin-only)
- [ ] All endpoints require admin role
- [ ] Non-admins get 403 Forbidden

## Frontend Readiness

### Resources Page
- [ ] File exists: `frontend/src/pages/resources/ResourceCreatePage.tsx`
- [ ] File exists: `frontend/src/pages/resources/components/ResourceFormModal.tsx`
- [ ] Resource form includes:
  - [ ] Name input (required)
  - [ ] Description textarea (optional)
  - [ ] Type select (gateway, third, mcp)
  - [ ] URL input (for gateway/third)
  - [ ] MCP config section (shows when type=mcp):
    - [ ] Transport select (stdio, sse, ws)
    - [ ] Command input (for stdio)
    - [ ] Args input (for stdio)
    - [ ] Timeout input
    - [ ] Endpoint input (for sse/ws)
  - [ ] View scope select (public, private)
  - [ ] API description textarea (optional)
- [ ] Form validation works correctly
- [ ] Submit creates resource via API
- [ ] Success/error toasts display

### Resource Table
- [ ] File exists: `frontend/src/pages/resources/components/ResourceTable.tsx`
- [ ] Table shows view_scope column with:
  - [ ] Globe icon for public resources
  - [ ] Lock icon for private resources
- [ ] Table shows owner column
- [ ] API description indicator icon (with tooltip)
- [ ] Table is responsive

### Users Page
- [ ] File exists: `frontend/src/pages/users/UsersPage.tsx`
- [ ] File exists: `frontend/src/pages/users/components/UserTable.tsx`
- [ ] File exists: `frontend/src/pages/users/components/RoleManagerModal.tsx`
- [ ] File exists: `frontend/src/hooks/use-user-management.ts`
- [ ] User table displays:
  - [ ] Username and email
  - [ ] Avatar with initials
  - [ ] Assigned roles (badges)
  - [ ] Active/Inactive status
  - [ ] Creation date
  - [ ] "Manage Roles" button
- [ ] Search functionality works
- [ ] Role filter dropdown works
- [ ] Pagination works
- [ ] Only admins see Users navigation link

### Role Manager Modal
- [ ] Modal shows current user roles
- [ ] Checkboxes for each available role
- [ ] Save changes button calls API
- [ ] Success closes modal
- [ ] Error shows inline message

### Navigation
- [ ] Resources link exists in navigation
- [ ] Users link only shows for admin users
- [ ] Non-admins cannot access /users directly

## Testing Infrastructure

### E2E Tests
- [ ] File: `frontend/e2e/resources.spec.ts` exists
- [ ] File: `frontend/e2e/users.spec.ts` exists
- [ ] Playwright configured correctly
- [ ] Test user accounts exist (admin, regular user)

### Test Data
- [ ] Admin user account: `admin@example.com`
- [ ] Regular user account: `user@example.com`
- [ ] Test roles exist (admin, user)
- [ ] Database is seeded with initial data

## Documentation

### API Documentation
- [ ] OpenAPI/Swagger docs include MCP schemas
- [ ] view_scope enum documented
- [ ] User management endpoints documented
- [ ] Example requests provided

### User Documentation
- [ ] File: `docs/mcp-resources.md` exists
- [ ] File: `docs/user-management.md` exists
- [ ] README.md updated with v1.1 features

## Sign-Off

### Backend Developer
- [ ] All backend code committed and pushed
- [ ] Database migrations applied
- [ ] API tested manually

### Frontend Developer
- [ ] All frontend code committed and pushed
- [ ] Components render without errors
- [ ] Forms submit correctly

### QA Engineer (Ready to Start Testing When All Above Checked)
- [ ] Can login as admin and regular user
- [ ] Can access Resources page
- [ ] Can access Users page (as admin)
- [ ] Can create MCP resources
- [ ] Can set view_scope
- [ ] Can assign roles to users

## Testing Starts When:
1. All items in this checklist are complete
2. Code is deployed to staging environment
3. Test data is seeded
4. QA Engineer confirms readiness

---

**Last Updated:** 2026-03-06
**Phase:** 1.1b Resources & User Management
**QA Engineer:** qa-engineer
