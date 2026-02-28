# Resource Management Feature Design

**Date:** 2026-02-28
**Status:** Approved
**Approach:** Single Integrated Page with Modals

## Overview

Implement a comprehensive resource management feature for the SkillHub frontend that enables users to perform full CRUD operations on system resources (build, gateway, and third-party resources) through a single-page interface with modal-based create/edit interactions.

## Requirements

### Functional Requirements
1. **List Resources**: Display all resources with pagination
2. **Filter Resources**: Filter by resource type (build/gateway/third) and search by name/description
3. **Create Resource**: Add new resources via modal form
4. **Update Resource**: Edit existing resources via modal form
5. **Delete Resource**: Remove resources with confirmation
6. **JSON Editor**: Edit `ext` field with validation

### Non-Functional Requirements
- Consistent with existing UI/UX patterns (UsersPage, SkillsListPage)
- Responsive design for desktop and tablet
- Loading states for all async operations
- Error handling with user-friendly messages
- Real-time JSON validation for ext field

## Architecture

### File Structure
```
frontend/src/
├── pages/resources/
│   ├── ResourcesPage.tsx          # Main page component
│   └── index.ts                   # Exports
├── hooks/
│   └── useResources.ts            # React Query hooks
├── api/
│   └── resources.ts               # API client
├── components/resources/
│   ├── ResourceTable.tsx          # Table component
│   ├── ResourceFormModal.tsx      # Modal for create/edit
│   ├── JsonEditor.tsx             # JSON editor component
│   └── index.ts                   # Exports
└── types/
    └── index.ts                   # Add Resource types
```

### Technology Stack
- **State Management**: React Query (TanStack Query)
- **Validation**: Zod for JSON validation
- **UI Components**: Existing Modal, Table, Input, Badge, Alert
- **Icons**: Lucide React
- **Routing**: React Router (protected route)

### Data Models

#### Resource Type
```typescript
export type ResourceType = 'build' | 'gateway' | 'third';

export interface Resource {
  id: string;
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ResourceCreate {
  name: string;
  desc?: string;
  type: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
}

export interface ResourceUpdate {
  name?: string;
  desc?: string;
  type?: ResourceType;
  url?: string;
  ext?: Record<string, unknown>;
}
```

## Component Design

### 1. ResourcesPage (Main Container)

**Responsibilities:**
- Fetch and display resources
- Handle search and filter state
- Coordinate modal open/close
- Display notifications

**State:**
```typescript
{
  searchQuery: string,
  typeFilter: ResourceType | 'all',
  isModalOpen: boolean,
  editingResource: Resource | null,
  deleteConfirmation: Resource | null
}
```

**Layout:**
```
├── Header
│   ├── Title & Stats
│   ├── Search Input
│   ├── Type Filter (Select)
│   └── "Add Resource" Button
├── ResourceTable
└── ResourceFormModal (conditional)
└── DeleteConfirmationDialog (conditional)
```

### 2. ResourceTable (Display Component)

**Columns:**
- Name (with link to view details)
- Type (color-coded badge)
- URL (truncated with tooltip)
- Description (truncated)
- Created At (relative time)
- Actions (Edit, Delete buttons)

**Features:**
- Empty state illustration
- Loading skeleton
- Animated row entrance
- Pagination controls

**Type Badge Colors:**
- `build`: Blue/Cyber Primary
- `gateway`: Purple/Cyber Secondary
- `third`: Green/Success

### 3. ResourceFormModal (Form Component)

**Form Fields:**
1. **Name** (required, text input)
   - Min length: 1, Max length: 255
   - Unique validation on backend

2. **Type** (required, select)
   - Options: build, gateway, third
   - Default: build

3. **URL** (optional, text input)
   - Max length: 2048
   - URL format validation

4. **Description** (optional, textarea)
   - Multi-line text support

5. **Ext** (optional, JSON editor)
   - Custom JsonEditor component
   - JSON validation
   - Format/Clear helpers

**Validation:**
- Client-side validation before submission
- Backend error display
- Real-time JSON validation

**Modes:**
- Create: Empty form
- Edit: Pre-filled with existing data

### 4. JsonEditor (Reusable Component)

**Features:**
- Syntax highlighting (basic)
- JSON validation with error display
- Format JSON button
- Clear button
- Error line indicator
- Copy to clipboard

**Validation:**
- Real-time JSON.parse() validation
- Display syntax errors with line numbers
- Prevent form submission if invalid

**Props:**
```typescript
interface JsonEditorProps {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
}
```

## Data Flow

### Read Flow
```
User navigates to /resources
→ ResourcesPage mounts
→ useResources hook executes
→ API call: GET /api/v1/resources
→ Loading state displayed
→ Response received
→ Resources displayed in table
```

### Create Flow
```
User clicks "Add Resource"
→ Modal opens (mode: create)
→ User fills form
→ User clicks submit
→ Client validation
→ useCreateResource mutation
→ API call: POST /api/v1/resources
→ Loading state on button
→ Success: Close modal, invalidate queries, toast success
→ Error: Display error in modal
```

### Update Flow
```
User clicks "Edit" on resource
→ Fetch resource by ID (if not in cache)
→ Modal opens (mode: edit, pre-filled)
→ User modifies form
→ User clicks submit
→ Client validation
→ useUpdateResource mutation
→ API call: PUT /api/v1/resources/{id}
→ Same success/error handling
```

### Delete Flow
```
User clicks "Delete"
→ Confirmation dialog opens
→ User confirms
→ useDeleteResource mutation
→ API call: DELETE /api/v1/resources/{id}
→ Success: Invalidate queries, toast success, close dialog
→ Error: Toast error
```

### Filter Flow
```
User types in search OR changes type filter
→ Local state updates
→ useResources hook refetches with params
→ API call: GET /api/v1/resources?type={type}
→ Table updates with filtered results
```

## API Integration

### Endpoints
```typescript
// GET /api/v1/resources
list(params?: { page?: number; size?: number; resource_type?: string })

// GET /api/v1/resources/{id}
getById(id: string)

// POST /api/v1/resources
create(data: ResourceCreate)

// PUT /api/v1/resources/{id}
update(id: string, data: ResourceUpdate)

// DELETE /api/v1/resources/{id}
delete(id: string)
```

### API Client (resources.ts)
```typescript
export const resourcesApi = {
  list: async (params) => { ... },
  getById: async (id) => { ... },
  create: async (data) => { ... },
  update: async (id, data) => { ... },
  delete: async (id) => { ... }
};
```

### React Query Hooks (useResources.ts)
```typescript
export const useResources = (params?) => useQuery(...)
export const useResource = (id) => useQuery(...)
export const useCreateResource = () => useMutation(...)
export const useUpdateResource = () => useMutation(...)
export const useDeleteResource = () => useMutation(...)
```

## Error Handling

### Network Errors
- Global error interceptor in apiClient
- User-friendly toast notifications
- Retry logic for failed requests

### Validation Errors
- Inline error messages in form
- Field-specific error display
- Real-time JSON validation feedback

### Not Found Errors
- Display "Resource not found" message
- Option to navigate back to list

### Permission Errors
- Redirect to login if 401
- Display "Access denied" if 403

## UI/UX Considerations

### Design System Compliance
- Use existing color scheme (cyber-primary, cyber-secondary, void-*)
- Consistent spacing and typography
- Font: JetBrains Mono for data, Orbitron for headers

### Animations
- Page fade-in: `animate-fade-in`
- Table rows: `animate-slide-in` with stagger
- Modal: Scale-in animation
- Button hover: Color transitions

### Responsive Design
- Table: Horizontal scroll on mobile
- Modal: Full-screen on mobile, centered on desktop
- Filters: Stack on mobile, row on desktop

### Accessibility
- Keyboard navigation support
- ARIA labels on interactive elements
- Focus management in modals
- Screen reader friendly

## Testing Strategy

### Unit Tests
- JsonEditor component validation
- Form validation logic
- Filter logic

### Integration Tests
- API client functions
- React Query hooks
- Error handling

### E2E Tests
- Create resource flow
- Edit resource flow
- Delete resource flow
- Filter and search
- Pagination

## Implementation Phases

### Phase 1: Foundation
1. Add Resource types to types/index.ts
2. Create API client (resources.ts)
3. Create React Query hooks (useResources.ts)
4. Update routing and navigation

### Phase 2: Core Components
1. Create ResourcesPage with basic structure
2. Create ResourceTable component
3. Implement list view with loading states

### Phase 3: Forms & Modals
1. Create ResourceFormModal component
2. Create JsonEditor component
3. Implement create functionality
4. Implement edit functionality

### Phase 4: Actions & Polish
1. Implement delete with confirmation
2. Add search and filter functionality
3. Add success/error notifications
4. Add animations and transitions

### Phase 5: Testing & Documentation
1. Write unit tests
2. Write integration tests
3. Write E2E tests
4. Update user documentation

## Success Criteria

- [ ] Users can view all resources in a table
- [ ] Users can create new resources via modal
- [ ] Users can edit existing resources via modal
- [ ] Users can delete resources with confirmation
- [ ] Users can filter by resource type
- [ ] Users can search by name/description
- [ ] JSON editor validates and formats JSON
- [ ] All operations show appropriate loading states
- [ ] Errors are handled gracefully with user feedback
- [ ] Design is consistent with existing pages

## Future Enhancements

- Bulk operations (delete multiple)
- Export resources to CSV/JSON
- Advanced filters (date range, multiple types)
- Resource detail page with full history
- Resource usage statistics
- Resource dependencies visualization
