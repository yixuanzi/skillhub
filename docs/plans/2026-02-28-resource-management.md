# Resource Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a complete resource management feature with CRUD operations, filtering, search, and JSON editor for the SkillHub frontend.

**Architecture:** Single-page application with React Query for state management, modal-based create/edit interactions, following existing patterns from UsersPage and SkillsListPage.

**Tech Stack:** React 18, TypeScript, TanStack Query, Zod, Lucide React, Tailwind CSS, existing UI components

---

## Prerequisites

**Reference Documentation:**
- Design doc: `docs/plans/2026-02-28-resource-management-design.md`
- Backend API: `backend/api/resource.py`
- Backend schema: `backend/schemas/resource.py`
- Backend model: `backend/models/resource.py`
- Similar implementation: `frontend/src/pages/users/UsersPage.tsx`
- API pattern: `frontend/src/api/users.ts`
- Hooks pattern: `frontend/src/hooks/useUsers.ts`

**Dependencies Check:**
Ensure these are installed:
```bash
cd frontend
pnpm list | grep -E "(react-query|@tanstack/react-query|zod|lucide-react)"
```

---

## Phase 1: Foundation (Types & API)

### Task 1: Add Resource Types

**Files:**
- Modify: `frontend/src/types/index.ts`

**Step 1: Add Resource interfaces**

Add to `frontend/src/types/index.ts` after the Skill Types section (around line 103):

```typescript
// Resource Types
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

export interface ResourceListResponse {
  items: Resource[];
  total: number;
  page: number;
  size: number;
}
```

**Step 2: Commit**

```bash
cd frontend
git add src/types/index.ts
git commit -m "feat(types): add Resource interfaces and types"
```

---

### Task 2: Create Resource API Client

**Files:**
- Create: `frontend/src/api/resources.ts`

**Step 1: Create API client module**

Create `frontend/src/api/resources.ts`:

```typescript
import apiClient from './client';
import { Resource, ResourceCreate, ResourceUpdate, ApiResponse, PaginatedResponse } from '@/types';

export const resourcesApi = {
  list: async (params?: { page?: number; pageSize?: number; resource_type?: string }): Promise<ApiResponse<PaginatedResponse<Resource>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Resource>>>('/resources', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.get<ApiResponse<Resource>>(`/resources/${id}`);
    return response.data;
  },

  create: async (data: ResourceCreate): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.post<ApiResponse<Resource>>('/resources', data);
    return response.data;
  },

  update: async (id: string, data: ResourceUpdate): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.put<ApiResponse<Resource>>(`/resources/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/resources/${id}`);
  },
};
```

**Step 2: Verify apiClient exists**

Check that `frontend/src/api/client.ts` exists and exports `apiClient`:
```bash
cat frontend/src/api/client.ts | grep -A 5 "export"
```

**Step 3: Commit**

```bash
cd frontend
git add src/api/resources.ts
git commit -m "feat(api): add resources API client"
```

---

### Task 3: Create React Query Hooks

**Files:**
- Create: `frontend/src/hooks/useResources.ts`

**Step 1: Create hooks module**

Create `frontend/src/hooks/useResources.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourcesApi } from '@/api/resources';
import { Resource, ResourceCreate, ResourceUpdate } from '@/types';

export const useResources = (params?: { page?: number; pageSize?: number; resource_type?: string }) => {
  return useQuery({
    queryKey: ['resources', params],
    queryFn: () => resourcesApi.list(params),
  });
};

export const useResource = (id: string) => {
  return useQuery({
    queryKey: ['resource', id],
    queryFn: () => resourcesApi.getById(id),
    enabled: !!id,
  });
};

export const useCreateResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ResourceCreate) => resourcesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};

export const useUpdateResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResourceUpdate }) =>
      resourcesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};

export const useDeleteResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => resourcesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};
```

**Step 2: Commit**

```bash
cd frontend
git add src/hooks/useResources.ts
git commit -m "feat(hooks): add resource management React Query hooks"
```

---

## Phase 2: Routing & Navigation

### Task 4: Add Resource Route

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

**Step 1: Update App.tsx routing**

Add import and route in `frontend/src/App.tsx`:

After line 7:
```typescript
import { ResourcesPage } from './pages/resources';
```

After line 80 (before settings route):
```typescript
<Route path="resources" element={<ResourcesPage />} />
```

**Step 2: Update Sidebar navigation**

Add to navItems array in `frontend/src/components/layout/Sidebar.tsx` (after users, before acl):

Import icon (add to imports on line 4-12):
```typescript
import {
  LayoutDashboard,
  Box,
  Users,
  Database,  // Add this
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';
```

Add to navItems array (after line 24):
```typescript
{ path: '/resources', label: 'Resources', icon: Database },
```

**Step 3: Create placeholder page**

Create `frontend/src/pages/resources/ResourcesPage.tsx`:
```typescript
export const ResourcesPage = () => {
  return <div className="text-gray-400">Resources coming soon</div>;
};
```

Create `frontend/src/pages/resources/index.ts`:
```typescript
export { ResourcesPage } from './ResourcesPage';
```

**Step 4: Test navigation**

```bash
cd frontend
pnpm dev
```

Visit: http://localhost:5173/resources

Expected: "Resources coming soon" message, Resources link in sidebar highlighted

**Step 5: Commit**

```bash
cd frontend
git add src/App.tsx src/components/layout/Sidebar.tsx src/pages/resources/
git commit -m "feat(routing): add resources route and navigation"
```

---

## Phase 3: UI Components

### Task 5: Create JsonEditor Component

**Files:**
- Create: `frontend/src/components/resources/JsonEditor.tsx`
- Install: Check zod dependency

**Step 1: Verify zod is installed**

```bash
cd frontend
pnpm list zod
```

If not installed:
```bash
pnpm add zod
```

**Step 2: Create JsonEditor component**

Create `frontend/src/components/resources/JsonEditor.tsx`:

```typescript
import { useState } from 'react';
import { Check, AlertCircle, FileCode, Trash2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface JsonEditorProps {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
  className?: string;
}

export const JsonEditor = ({ value = '', onChange, placeholder, error, className }: JsonEditorProps) => {
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateJson = (jsonString: string): boolean => {
    if (!jsonString.trim()) {
      setValidationError(null);
      return true;
    }

    try {
      JSON.parse(jsonString);
      setValidationError(null);
      return true;
    } catch (err) {
      setValidationError(err instanceof Error ? err.message : 'Invalid JSON');
      return false;
    }
  };

  const handleChange = (newValue: string) => {
    onChange(newValue);
    validateJson(newValue);
  };

  const handleFormat = () => {
    if (!value.trim()) return;

    try {
      const parsed = JSON.parse(value);
      const formatted = JSON.stringify(parsed, null, 2);
      onChange(formatted);
      setValidationError(null);
    } catch (err) {
      setValidationError('Cannot format invalid JSON');
    }
  };

  const handleClear = () => {
    onChange('');
    setValidationError(null);
  };

  const displayError = error || validationError;

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
          Extended Data (JSON)
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleFormat}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-cyber-primary hover:bg-cyber-primary/10 rounded transition-all"
            disabled={!value.trim()}
          >
            <FileCode className="w-3 h-3" />
            Format
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-mono text-gray-400 hover:text-gray-200 hover:bg-void-800 rounded transition-all"
            disabled={!value.trim()}
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>
      </div>

      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={placeholder || '{"key": "value"}'}
          className={cn(
            'w-full min-h-[150px] p-4 font-mono text-sm rounded-lg',
            'bg-void-900/50 border border-void-700',
            'text-gray-100 placeholder:text-gray-600',
            'focus:outline-none focus:border-cyber-primary',
            'transition-all duration-200',
            'font-mono tabular-nums',
            displayError ? 'border-cyber-accent' : ''
          )}
          spellCheck={false}
        />

        {displayError && (
          <div className="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-1 bg-cyber-accent/10 border border-cyber-accent rounded text-xs text-cyber-accent font-mono">
            <AlertCircle className="w-3 h-3" />
            {displayError}
          </div>
        )}

        {!displayError && value.trim() && (
          <div className="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-1 bg-cyber-primary/10 border border-cyber-primary rounded text-xs text-cyber-primary font-mono">
            <Check className="w-3 h-3" />
            Valid JSON
          </div>
        )}
      </div>
    </div>
  );
};
```

**Step 3: Create components index**

Create `frontend/src/components/resources/index.ts`:
```typescript
export { JsonEditor } from './JsonEditor';
```

**Step 4: Commit**

```bash
cd frontend
git add src/components/resources/
git commit -m "feat(components): add JsonEditor component with validation"
```

---

### Task 6: Create ResourceFormModal Component

**Files:**
- Create: `frontend/src/components/resources/ResourceFormModal.tsx`

**Step 1: Create ResourceFormModal component**

Create `frontend/src/components/resources/ResourceFormModal.tsx`:

```typescript
import { useEffect } from 'react';
import { Modal, Input, Alert, Button } from '@/components/ui';
import { JsonEditor } from './JsonEditor';
import { Resource, ResourceCreate, ResourceType } from '@/types';
import { cn } from '@/utils/cn';

interface ResourceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ResourceCreate) => void;
  resource?: Resource;
  isLoading?: boolean;
  error?: string;
}

const resourceTypes: { value: ResourceType; label: string }[] = [
  { value: 'build', label: 'Build Resource' },
  { value: 'gateway', label: 'Gateway Resource' },
  { value: 'third', label: 'Third Party Resource' },
];

export const ResourceFormModal = ({
  isOpen,
  onClose,
  onSubmit,
  resource,
  isLoading,
  error,
}: ResourceFormModalProps) => {
  const isEditing = !!resource;

  // Form state - using a simple object since we don't have a form library
  const [formData, setFormData] = useState<ResourceCreate>({
    name: '',
    type: 'build',
    desc: '',
    url: '',
    ext: undefined,
  });
  const [extJson, setExtJson] = useState('');

  useEffect(() => {
    if (resource) {
      setFormData({
        name: resource.name,
        type: resource.type,
        desc: resource.desc || '',
        url: resource.url || '',
        ext: resource.ext,
      });
      setExtJson(resource.ext ? JSON.stringify(resource.ext, null, 2) : '');
    } else {
      setFormData({
        name: '',
        type: 'build',
        desc: '',
        url: '',
        ext: undefined,
      });
      setExtJson('');
    }
  }, [resource, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Parse ext JSON if provided
    let ext: Record<string, unknown> | undefined;
    if (extJson.trim()) {
      try {
        ext = JSON.parse(extJson);
      } catch (err) {
        return; // JsonEditor will show error
      }
    }

    onSubmit({
      ...formData,
      ext,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? 'Edit Resource' : 'Create Resource'}>
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <Alert variant="danger">
            {error}
          </Alert>
        )}

        <Input
          label="Resource Name"
          type="text"
          placeholder="my-resource"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
            Resource Type
          </label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value as ResourceType })}
            className={cn(
              'px-4 py-2.5 font-mono text-sm rounded-lg',
              'bg-void-900/50 border border-void-700',
              'text-gray-100',
              'focus:outline-none focus:border-cyber-primary',
              'transition-all duration-200'
            )}
            required
          >
            {resourceTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="URL (Optional)"
          type="url"
          placeholder="https://example.com/resource"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
        />

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
            Description (Optional)
          </label>
          <textarea
            value={formData.desc}
            onChange={(e) => setFormData({ ...formData, desc: e.target.value })}
            placeholder="Resource description..."
            className={cn(
              'px-4 py-2.5 font-mono text-sm rounded-lg min-h-[80px]',
              'bg-void-900/50 border border-void-700',
              'text-gray-100 placeholder:text-gray-600',
              'focus:outline-none focus:border-cyber-primary',
              'transition-all duration-200'
            )}
          />
        </div>

        <JsonEditor
          value={extJson}
          onChange={setExtJson}
          placeholder='{"key": "value"}'
        />

        <div className="flex justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : isEditing ? 'Update Resource' : 'Create Resource'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
```

Add missing import:
```typescript
import { useState, useEffect } from 'react';
```

**Step 2: Update components index**

Update `frontend/src/components/resources/index.ts`:
```typescript
export { JsonEditor } from './JsonEditor';
export { ResourceFormModal } from './ResourceFormModal';
```

**Step 3: Commit**

```bash
cd frontend
git add src/components/resources/
git commit -m "feat(components): add ResourceFormModal component"
```

---

### Task 7: Create ResourceTable Component

**Files:**
- Create: `frontend/src/components/resources/ResourceTable.tsx`

**Step 1: Create ResourceTable component**

Create `frontend/src/components/resources/ResourceTable.tsx`:

```typescript
import { Resource } from '@/types';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, Badge } from '@/components/ui';
import { Edit, Trash2, ExternalLink } from 'lucide-react';
import { formatRelativeTime } from '@/utils/date';

interface ResourceTableProps {
  resources: Resource[];
  onEdit: (resource: Resource) => void;
  onDelete: (resource: Resource) => void;
  isLoading?: boolean;
}

const getTypeColor = (type: string): 'info' | 'warning' | 'success' => {
  switch (type) {
    case 'build':
      return 'info';
    case 'gateway':
      return 'warning';
    case 'third':
      return 'success';
    default:
      return 'info';
  }
};

export const ResourceTable = ({ resources, onEdit, onDelete, isLoading }: ResourceTableProps) => {
  if (isLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        Loading resources...
      </div>
    );
  }

  if (resources.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-2">No resources found</p>
        <p className="text-sm text-gray-600">Create your first resource to get started</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>URL</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Created</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {resources.map((resource, index) => (
          <TableRow
            key={resource.id}
            className="animate-slide-in"
            style={{ animationDelay: `${index * 0.05}s` }}
          >
            <TableCell>
              <div>
                <p className="font-mono text-sm text-gray-200">{resource.name}</p>
                <p className="text-xs text-gray-500">{resource.id}</p>
              </div>
            </TableCell>
            <TableCell>
              <Badge variant={getTypeColor(resource.type)} className="text-xs">
                {resource.type}
              </Badge>
            </TableCell>
            <TableCell>
              {resource.url ? (
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-cyber-primary hover:text-cyber-secondary text-sm"
                >
                  <span className="truncate max-w-[200px]">{resource.url}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              ) : (
                <span className="text-gray-600 text-sm">—</span>
              )}
            </TableCell>
            <TableCell>
              <span className="text-sm text-gray-400 line-clamp-2">
                {resource.desc || '—'}
              </span>
            </TableCell>
            <TableCell>
              <span className="text-sm text-gray-500">
                {formatRelativeTime(resource.created_at)}
              </span>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => onEdit(resource)}
                  className="p-2 text-cyber-primary hover:text-cyber-secondary hover:bg-void-800 rounded transition-all"
                  title="Edit resource"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDelete(resource)}
                  className="p-2 text-gray-400 hover:text-cyber-accent hover:bg-void-800 rounded transition-all"
                  title="Delete resource"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
```

**Step 2: Update components index**

Update `frontend/src/components/resources/index.ts`:
```typescript
export { JsonEditor } from './JsonEditor';
export { ResourceFormModal } from './ResourceFormModal';
export { ResourceTable } from './ResourceTable';
```

**Step 3: Commit**

```bash
cd frontend
git add src/components/resources/
git commit -m "feat(components): add ResourceTable component"
```

---

## Phase 4: Main Page Integration

### Task 8: Create ResourcesPage

**Files:**
- Modify: `frontend/src/pages/resources/ResourcesPage.tsx`

**Step 1: Implement ResourcesPage**

Replace the placeholder content in `frontend/src/pages/resources/ResourcesPage.tsx`:

```typescript
import { useState } from 'react';
import { useResources, useCreateResource, useUpdateResource, useDeleteResource } from '@/hooks/useResources';
import { Card, Input, Button, Alert } from '@/components/ui';
import { ResourceTable, ResourceFormModal } from '@/components/resources';
import { Plus, Search } from 'lucide-react';
import { Resource, ResourceType } from '@/types';

export const ResourcesPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | undefined>();
  const [deleteConfirmation, setDeleteConfirmation] = useState<Resource | undefined>();
  const [formError, setFormError] = useState('');

  // Build query params
  const queryParams = {
    page: 1,
    pageSize: 100,
    ...(typeFilter !== 'all' && { resource_type: typeFilter }),
  };

  const { data: resourcesData, isLoading, error } = useResources(queryParams);
  const createMutation = useCreateResource();
  const updateMutation = useUpdateResource();
  const deleteMutation = useDeleteResource();

  const resources = resourcesData?.data?.items || [];

  // Filter by search query (client-side for simplicity)
  const filteredResources = resources.filter((resource) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      resource.name.toLowerCase().includes(query) ||
      resource.desc?.toLowerCase().includes(query)
    );
  });

  const handleOpenCreateModal = () => {
    setEditingResource(undefined);
    setFormError('');
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (resource: Resource) => {
    setEditingResource(resource);
    setFormError('');
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingResource(undefined);
    setFormError('');
  };

  const handleSubmit = async (data: { name: string; type: ResourceType; desc?: string; url?: string; ext?: Record<string, unknown> }) => {
    setFormError('');
    try {
      if (editingResource) {
        await updateMutation.mutateAsync({ id: editingResource.id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      handleCloseModal();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setFormError(message);
    }
  };

  const handleDelete = async (resource: Resource) => {
    if (!window.confirm(`Are you sure you want to delete resource "${resource.name}"?`)) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(resource.id);
    } catch (err: unknown) {
      console.error('Failed to delete resource:', err);
      alert('Failed to delete resource. Please try again.');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Resources
          </h1>
          <p className="font-mono text-sm text-gray-500">
            {resources.length} {resources.length === 1 ? 'resource' : 'resources'}
          </p>
        </div>
        <Button
          variant="primary"
          onClick={handleOpenCreateModal}
          className="inline-flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Resource
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-cyber-primary transition-all"
            />
          </div>
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all sm:w-48"
        >
          <option value="all">All Types</option>
          <option value="build">Build</option>
          <option value="gateway">Gateway</option>
          <option value="third">Third Party</option>
        </select>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="danger">
          Failed to load resources. Please refresh the page.
        </Alert>
      )}

      {/* Resources Table */}
      <Card>
        <ResourceTable
          resources={filteredResources}
          onEdit={handleOpenEditModal}
          onDelete={handleDelete}
          isLoading={isLoading}
        />
      </Card>

      {/* Create/Edit Modal */}
      <ResourceFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSubmit={handleSubmit}
        resource={editingResource}
        isLoading={createMutation.isPending || updateMutation.isPending}
        error={formError}
      />
    </div>
  );
};
```

**Step 2: Test the page**

```bash
cd frontend
pnpm dev
```

Visit: http://localhost:5173/resources

Expected:
- Resources page with header
- Search and filter controls
- Empty state or list of resources
- "Add Resource" button opens modal
- All CRUD operations working

**Step 3: Commit**

```bash
cd frontend
git add src/pages/resources/
git commit -m "feat(page): implement ResourcesPage with full CRUD operations"
```

---

## Phase 5: Polish & Testing

### Task 9: Add Date Utility (if missing)

**Files:**
- Check: `frontend/src/utils/date.ts`

**Step 1: Check if date utility exists**

```bash
cat frontend/src/utils/date.ts
```

If missing or doesn't have `formatRelativeTime`, add it:

```typescript
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
};
```

**Step 2: Commit if modified**

```bash
cd frontend
git add src/utils/date.ts
git commit -m "feat(utils): add formatRelativeTime utility"
```

---

### Task 10: Add Success/Error Notifications

**Files:**
- Check if toast library exists, if not add simple implementation

**Step 1: Check for existing notification system**

```bash
cd frontend
grep -r "toast\|notification" src/ --include="*.ts" --include="*.tsx" | head -5
```

If none exists, add a simple toast context or use alert/console for now (can be enhanced later).

For now, the ResourceFormModal already shows errors inline, and we use `alert()` for delete confirmation. This is acceptable for MVP.

**Step 2: Document future enhancement**

Add TODO comment in ResourcesPage:
```typescript
// TODO: Add toast notifications for success/error feedback
// Consider using react-hot-toast or similar library
```

**Step 3: Commit if changes made**

```bash
cd frontend
git add .
git commit -m "docs: add TODO for toast notifications"
```

---

### Task 11: Write Unit Tests for JsonEditor

**Files:**
- Create: `frontend/src/components/resources/JsonEditor.test.tsx`

**Step 1: Check test setup**

```bash
cd frontend
cat package.json | grep -A 5 "test"
```

**Step 2: Write JsonEditor tests**

Create `frontend/src/components/resources/JsonEditor.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { JsonEditor } from './JsonEditor';

describe('JsonEditor', () => {
  it('renders empty editor', () => {
    render(<JsonEditor value="" onChange={vi.fn()} />);
    expect(screen.getByPlaceholderText('{"key": "value"}')).toBeInTheDocument();
  });

  it('displays valid JSON indicator', () => {
    render(<JsonEditor value='{"test": true}' onChange={vi.fn()} />);
    expect(screen.getByText('Valid JSON')).toBeInTheDocument();
  });

  it('shows validation error for invalid JSON', () => {
    render(<JsonEditor value='{"invalid"' onChange={vi.fn()} />);
    expect(screen.getByText(/Invalid JSON/)).toBeInTheDocument();
  });

  it('formats JSON on format button click', () => {
    const handleChange = vi.fn();
    render(
      <JsonEditor
        value='{"a":1,"b":2}'
        onChange={handleChange}
      />
    );

    const formatButton = screen.getByText('Format');
    fireEvent.click(formatButton);

    expect(handleChange).toHaveBeenCalledWith(
      expect.stringContaining('\n')
    );
  });

  it('clears content on clear button click', () => {
    const handleChange = vi.fn();
    render(
      <JsonEditor
        value='{"test": true}'
        onChange={handleChange}
      />
    );

    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);

    expect(handleChange).toHaveBeenCalledWith('');
  });
});
```

**Step 3: Run tests**

```bash
cd frontend
pnpm test JsonEditor
```

Expected: All tests pass

**Step 4: Commit**

```bash
cd frontend
git add src/components/resources/JsonEditor.test.tsx
git commit -m "test(components): add JsonEditor unit tests"
```

---

### Task 12: End-to-End Testing (Manual)

**Step 1: Test full user flow**

```bash
cd frontend
pnpm dev
```

**Manual Test Checklist:**

1. **Navigate to Resources page**
   - [ ] Sidebar "Resources" link works
   - [ ] Page loads without errors
   - [ ] Empty state shows correctly

2. **Create Resource**
   - [ ] Click "Add Resource" button
   - [ ] Modal opens with empty form
   - [ ] Fill in name: "test-resource"
   - [ ] Select type: "build"
   - [ ] Add URL: "https://example.com"
   - [ ] Add description: "Test resource"
   - [ ] Add ext JSON: `{"env": "dev", "region": "us-east-1"}`
   - [ ] Click "Format" - JSON formats correctly
   - [ ] Click "Create Resource"
   - [ ] Modal closes, resource appears in table

3. **Edit Resource**
   - [ ] Click Edit button on resource
   - [ ] Modal opens with pre-filled data
   - [ ] Change description
   - [ ] Click "Update Resource"
   - [ ] Modal closes, changes reflected

4. **Filter & Search**
   - [ ] Type filter dropdown works
   - [ ] Search input filters by name
   - [ ] Combined filters work

5. **Delete Resource**
   - [ ] Click Delete button
   - [ ] Confirmation dialog appears
   - [ ] Confirm deletion
   - [ ] Resource removed from table

6. **Error Handling**
   - [ ] Try to create duplicate name (backend validation)
   - [ ] Try invalid JSON in ext field
   - [ ] Network error handling

**Step 2: Document any issues found**

If issues found, fix them and commit fixes with message:
```bash
git commit -m "fix: resolve issues found during E2E testing"
```

---

### Task 13: Final Documentation & Cleanup

**Files:**
- Update: README or docs if needed

**Step 1: Update feature documentation**

If project has user-facing docs, add Resources section.

**Step 2: Code review checklist**

- [ ] All components follow existing patterns
- [ ] TypeScript types are correct
- [ ] No console errors or warnings
- [ ] Responsive design works
- [ ] Accessibility: keyboard navigation, ARIA labels
- [ ] Loading states for all async operations
- [ ] Error messages are user-friendly
- [ ] Code follows project conventions

**Step 3: Final commit**

```bash
cd frontend
git add .
git commit -m "feat: complete resource management feature implementation"
```

**Step 4: Create pull request (if using Git flow)**

```bash
git checkout -b feature/resource-management
git push origin feature/resource-management
```

Create PR with:
- Title: "feat: Add resource management feature"
- Description: References design doc `docs/plans/2026-02-28-resource-management-design.md`

---

## Success Criteria Verification

Run through this checklist to confirm implementation is complete:

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

---

## Future Enhancements (Out of Scope for MVP)

- Toast notifications library integration
- Bulk operations (delete multiple)
- Export resources to CSV/JSON
- Advanced filters (date range, multiple types)
- Resource detail page with full history
- Resource usage statistics
- Resource dependencies visualization
- Pagination for large datasets
- Optimistic updates for better UX

---

## Notes for Developer

**Common Issues:**
1. **CORS errors**: Ensure backend API is running and accessible
2. **Auth errors**: Check that JWT token is valid and being sent
3. **Type errors**: Run `pnpm type-check` if available
4. **Import errors**: Verify all paths use `@/` alias correctly

**Debugging:**
- Use React Query DevTools for state debugging
- Check Network tab in browser DevTools
- Look for console errors and warnings

**Code Style:**
- Follow existing patterns in UsersPage and SkillsListPage
- Use existing UI components when possible
- Keep components small and focused
- Prefer composition over complex props

---

**End of Implementation Plan**
