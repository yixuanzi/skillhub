import { useState } from 'react';
import { useMTokens, useCreateMToken, useUpdateMToken, useDeleteMToken } from '@/hooks/useMTokens';
import { Card, Input, Alert } from '@/components/ui';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Search, Plus, Edit, Trash2, Key, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { MToken } from '@/types';

export const TokensPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [appNameFilter, setAppNameFilter] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingToken, setEditingToken] = useState<MToken | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<MToken | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [showTokenValue, setShowTokenValue] = useState<Record<string, boolean>>({});

  // Form state
  const [formData, setFormData] = useState({
    app_name: '',
    key_name: '',
    value: '',
    desc: '',
  });

  // Fetch tokens
  const { data: tokensData, isLoading: tokensLoading } = useMTokens({
    page,
    pageSize,
    app_name: appNameFilter || undefined,
  });

  const createMutation = useCreateMToken();
  const updateMutation = useUpdateMToken();
  const deleteMutation = useDeleteMToken();

  const tokens = tokensData?.items || [];
  const total = tokensData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  // Get unique app names for filter
  const appNames = Array.from(new Set(tokens.map((t) => t.app_name))).sort();

  const filteredTokens = tokens.filter((token) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      token.app_name.toLowerCase().includes(query) ||
      token.key_name.toLowerCase().includes(query) ||
      (token.desc && token.desc.toLowerCase().includes(query))
    );
  });

  const handleCreate = async () => {
    try {
      setErrorMessage('');
      await createMutation.mutateAsync(formData);
      setSuccessMessage('Token created successfully!');
      setIsCreateModalOpen(false);
      resetForm();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || 'Failed to create token');
    }
  };

  const handleEdit = (token: MToken) => {
    setEditingToken(token);
    setFormData({
      app_name: token.app_name,
      key_name: token.key_name,
      value: token.value,
      desc: token.desc || '',
    });
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleUpdate = async () => {
    if (!editingToken) return;

    try {
      setErrorMessage('');
      await updateMutation.mutateAsync({
        id: editingToken.id,
        data: formData,
      });
      setSuccessMessage('Token updated successfully!');
      setEditingToken(null);
      resetForm();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || 'Failed to update token');
    }
  };

  const handleDelete = async (token: MToken) => {
    try {
      setErrorMessage('');
      if (deleteConfirm?.id === token.id) {
        await deleteMutation.mutateAsync(token.id);
        setSuccessMessage('Token deleted successfully!');
        setDeleteConfirm(null);
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setDeleteConfirm(token);
      }
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || 'Failed to delete token');
    }
  };

  const resetForm = () => {
    setFormData({
      app_name: '',
      key_name: '',
      value: '',
      desc: '',
    });
  };

  const toggleTokenVisibility = (tokenId: string) => {
    setShowTokenValue((prev) => ({
      ...prev,
      [tokenId]: !prev[tokenId],
    }));
  };

  const maskTokenValue = (value: string) => {
    if (value.length <= 8) return '•'.repeat(value.length);
    return value.substring(0, 4) + '•'.repeat(value.length - 8) + value.substring(value.length - 4);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2 flex items-center gap-3">
            <Key className="w-8 h-8 text-cyber-primary" />
            Token Management
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Manage API tokens and keys for external services
          </p>
        </div>
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)} className="group">
          <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
          New Token
        </Button>
      </div>

      {/* Success and Error Messages */}
      {successMessage && (
        <div className="animate-slide-in">
          <Alert variant="success" className="border-cyber-primary/30 bg-cyber-primary/10">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-cyber-primary flex-shrink-0" />
              <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
            </div>
          </Alert>
        </div>
      )}

      {errorMessage && (
        <div className="animate-slide-in">
          <Alert variant="danger">
            <span className="text-sm font-medium">{errorMessage}</span>
          </Alert>
        </div>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Search tokens..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* App Name Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-500 font-mono">App:</label>
            <select
              value={appNameFilter}
              onChange={(e) => setAppNameFilter(e.target.value)}
              className="px-4 py-2 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
            >
              <option value="">All Apps</option>
              {appNames.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Tokens Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-void-700 bg-void-900/30">
                <th className="px-6 py-3 text-left text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  App Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  Key Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-void-700/50">
              {tokensLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500 font-mono">
                    Loading tokens...
                  </td>
                </tr>
              ) : filteredTokens.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <Key className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                    <p className="text-gray-500 font-mono mb-2">No tokens found</p>
                    <p className="text-xs text-gray-600">
                      {searchQuery || appNameFilter ? 'Try adjusting your filters' : 'Create your first token to get started'}
                    </p>
                  </td>
                </tr>
              ) : (
                filteredTokens.map((token) => (
                  <tr key={token.id} className="hover:bg-void-900/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Key className="w-4 h-4 text-cyber-primary" />
                        <span className="text-sm font-mono font-medium text-gray-200">{token.app_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-300">{token.key_name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono text-cyber-secondary bg-void-900/50 px-2 py-1 rounded">
                          {showTokenValue[token.id] ? token.value : maskTokenValue(token.value)}
                        </code>
                        <button
                          onClick={() => toggleTokenVisibility(token.id)}
                          className="text-gray-500 hover:text-gray-300 transition-colors"
                          title={showTokenValue[token.id] ? 'Hide value' : 'Show value'}
                        >
                          {showTokenValue[token.id] ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-400">{token.desc || '-'}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs text-gray-500 font-mono">
                        {new Date(token.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(token)}
                          className="text-gray-400 hover:text-cyber-primary"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(token)}
                          className={cn(
                            'text-gray-400 hover:text-cyber-accent',
                            deleteConfirm?.id === token.id && 'text-cyber-accent bg-cyber-accent/10'
                          )}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500 font-mono">
            Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, total)} of {total} tokens
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
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
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          resetForm();
        }}
        title="Create New Token"
        size="lg"
      >
        <form onSubmit={(e) => { e.preventDefault(); handleCreate(); }} className="space-y-5">
          {errorMessage && (
            <Alert variant="danger">
              <span className="text-sm font-medium">{errorMessage}</span>
            </Alert>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              App Name *
            </label>
            <Input
              value={formData.app_name}
              onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}
              placeholder="e.g., GitHub, OpenAI, AWS"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Key Name *
            </label>
            <Input
              value={formData.key_name}
              onChange={(e) => setFormData({ ...formData, key_name: e.target.value })}
              placeholder="e.g., API Key, Access Token"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Value *
            </label>
            <Input
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              placeholder="Enter token value"
              type="password"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Description
            </label>
            <Input
              value={formData.desc}
              onChange={(e) => setFormData({ ...formData, desc: e.target.value })}
              placeholder="Optional description"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-void-700">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setIsCreateModalOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Token'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingToken}
        onClose={() => {
          setEditingToken(null);
          resetForm();
        }}
        title="Edit Token"
        size="lg"
      >
        <form onSubmit={(e) => { e.preventDefault(); handleUpdate(); }} className="space-y-5">
          {errorMessage && (
            <Alert variant="danger">
              <span className="text-sm font-medium">{errorMessage}</span>
            </Alert>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              App Name *
            </label>
            <Input
              value={formData.app_name}
              onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}
              placeholder="e.g., GitHub, OpenAI, AWS"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Key Name *
            </label>
            <Input
              value={formData.key_name}
              onChange={(e) => setFormData({ ...formData, key_name: e.target.value })}
              placeholder="e.g., API Key, Access Token"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Value *
            </label>
            <Input
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              placeholder="Enter token value"
              type="password"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
              Description
            </label>
            <Input
              value={formData.desc}
              onChange={(e) => setFormData({ ...formData, desc: e.target.value })}
              placeholder="Optional description"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-void-700">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setEditingToken(null);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Updating...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
