import { useState } from 'react';
import { useResources, useCreateResource, useUpdateResource, useDeleteResource } from '@/hooks/useResources';
import { ResourceTable } from '@/components/resources/ResourceTable';
import { ResourceFormModal } from '@/components/resources/ResourceFormModal';
import { Card, Input, Alert } from '@/components/ui';
import { Button } from '@/components/ui/Button';
import { Search, Plus, Filter, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Resource } from '@/types';

export const ResourcesPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingResource, setEditingResource] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<any>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { data, isLoading } = useResources({
    page,
    pageSize,
    resource_type: typeFilter || undefined,
  });

  const createMutation = useCreateResource();
  const updateMutation = useUpdateResource();
  const deleteMutation = useDeleteResource();

  const resources = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  // Filter resources by search query
  const filteredResources = resources.filter((resource: Resource) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      resource.name.toLowerCase().includes(query) ||
      resource.desc?.toLowerCase().includes(query) ||
      resource.type.toLowerCase().includes(query)
    );
  });

  const handleCreate = async (data: any) => {
    try {
      setErrorMessage('');
      await createMutation.mutateAsync(data);
      setSuccessMessage('Resource created successfully!');
      setIsCreateModalOpen(false);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to create resource');
    }
  };

  const handleEdit = (resource: any) => {
    setEditingResource(resource);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleUpdate = async (data: any) => {
    try {
      setErrorMessage('');
      await updateMutation.mutateAsync({ id: editingResource.id, data });
      setSuccessMessage('Resource updated successfully!');
      setEditingResource(null);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to update resource');
    }
  };

  const handleDelete = async (resource: any) => {
    try {
      setErrorMessage('');
      if (deleteConfirm?.id === resource.id) {
        await deleteMutation.mutateAsync(resource.id);
        setSuccessMessage('Resource deleted successfully!');
        setDeleteConfirm(null);
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setDeleteConfirm(resource);
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to delete resource');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Success and Error Messages */}
      {successMessage && (
        <div className="animate-slide-in">
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-cyber-primary/30 bg-cyber-primary/10">
            <CheckCircle className="w-4 h-4 text-cyber-primary flex-shrink-0" />
            <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="animate-slide-in">
          <Alert variant="danger">
            <span className="text-sm font-medium">{errorMessage}</span>
          </Alert>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2 flex items-center gap-3">
            <span className="text-cyber-primary">&lt;</span>
            Resources
            <span className="text-cyber-primary">/&gt;</span>
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Manage build artifacts, gateway endpoints, and third-party integrations
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setIsCreateModalOpen(true)}
          className="group"
        >
          <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
          New Resource
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Search resources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
            >
              <option value="">All Types</option>
              <option value="build">Build</option>
              <option value="gateway">Gateway</option>
              <option value="third">Third Party</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Resource Table */}
      <ResourceTable
        resources={filteredResources}
        loading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        deleteConfirm={deleteConfirm}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500 font-mono">
            Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, total)} of {total} resources
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={cn(
                      'w-8 h-8 font-mono text-sm rounded transition-all duration-200',
                      page === pageNum
                        ? 'bg-cyber-primary/10 border border-cyber-primary text-cyber-primary'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-void-800'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      <ResourceFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        mode="create"
      />

      {/* Edit Modal */}
      <ResourceFormModal
        isOpen={!!editingResource}
        onClose={() => setEditingResource(null)}
        onSubmit={handleUpdate}
        resource={editingResource}
        mode="edit"
      />
    </div>
  );
};
