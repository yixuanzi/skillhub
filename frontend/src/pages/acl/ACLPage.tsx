import { useState } from 'react';
import { useACLRules, useACLRule, useCreateACLRule, useUpdateACLRule, useDeleteACLRule } from '@/hooks/useACL';
import { useResources } from '@/hooks/useResources';
import { ACLResourceTable, ACLResourceFormModal } from '@/components/acl';
import { Card, Input, Alert } from '@/components/ui';
import { Button } from '@/components/ui/Button';
import { Search, Plus, Filter, Shield, Database, FileKey, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { ACLRule, Resource } from '@/types';

type TabType = 'rules' | 'resource-acl' | 'logs';

export const ACLPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [accessModeFilter, setAccessModeFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState<TabType>('resource-acl');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<ACLRule | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch full rule data when editing
  const { data: editingRule, isLoading: editingRuleLoading } = useACLRule(editingRuleId || '');

  // Fetch ACL rules
  const { data: rulesData, isLoading: rulesLoading } = useACLRules({
    page,
    pageSize,
  });

  // Fetch resources for ACL resource management
  const { data: resourcesData } = useResources({
    page: 1,
    pageSize: 1000, // Get all resources for dropdown
  });

  const createMutation = useCreateACLRule();
  const updateMutation = useUpdateACLRule();
  const deleteMutation = useDeleteACLRule();

  const rules = rulesData?.items || [];
  const total = rulesData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);
  const resources = resourcesData?.items || [];

  // Filter rules by search query and access mode
  const filteredRules = rules.filter((rule: ACLRule) => {
    if (accessModeFilter && rule.access_mode !== accessModeFilter) {
      return false;
    }
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      rule.resource_name.toLowerCase().includes(query) ||
      rule.resource_id.toLowerCase().includes(query) ||
      rule.access_mode.toLowerCase().includes(query)
    );
  });

  const handleCreate = async (data: any) => {
    try {
      setErrorMessage('');
      await createMutation.mutateAsync(data);
      setSuccessMessage('ACL rule created successfully!');
      setIsCreateModalOpen(false);
      // Auto-hide success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to create ACL rule');
    }
  };

  const handleEdit = (rule: ACLRule) => {
    setEditingRuleId(rule.id);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleUpdate = async (data: any) => {
    try {
      setErrorMessage('');
      await updateMutation.mutateAsync({ id: editingRuleId!, data });
      setSuccessMessage('ACL rule updated successfully!');
      setEditingRuleId(null);
      // Auto-hide success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to update ACL rule');
    }
  };

  const handleDelete = async (rule: ACLRule) => {
    try {
      setErrorMessage('');
      if (deleteConfirm?.id === rule.id) {
        await deleteMutation.mutateAsync(rule.id);
        setSuccessMessage('ACL rule deleted successfully!');
        setDeleteConfirm(null);
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setDeleteConfirm(rule);
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to delete ACL rule');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2 flex items-center gap-3">
            <Shield className="w-8 h-8 text-cyber-primary" />
            Access Control
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Manage ACL rules and resource access permissions
          </p>
        </div>
        {activeTab === 'resource-acl' && (
          <Button
            variant="primary"
            onClick={() => setIsCreateModalOpen(true)}
            className="group"
          >
            <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
            New Rule
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-void-700 overflow-x-auto" style={{ pointerEvents: 'auto' }}>
        <button
          onClick={() => setActiveTab('resource-acl')}
          className={cn(
            'px-4 py-2.5 font-mono text-sm transition-all border-b-2 -mb-px whitespace-nowrap flex items-center gap-2',
            activeTab === 'resource-acl'
              ? 'text-cyber-primary border-cyber-primary bg-cyber-primary/5'
              : 'text-gray-500 border-transparent hover:text-gray-300'
          )}
        >
          <Database className="w-4 h-4" />
          Resource ACL
          {rules.length > 0 && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-cyber-primary/20 text-cyber-primary">
              {rules.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={cn(
            'px-4 py-2.5 font-mono text-sm transition-all border-b-2 -mb-px whitespace-nowrap flex items-center gap-2',
            activeTab === 'rules'
              ? 'text-cyber-primary border-cyber-primary bg-cyber-primary/5'
              : 'text-gray-500 border-transparent hover:text-gray-300'
          )}
        >
          <FileKey className="w-4 h-4" />
          API Keys
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={cn(
            'px-4 py-2.5 font-mono text-sm transition-all border-b-2 -mb-px whitespace-nowrap flex items-center gap-2',
            activeTab === 'logs'
              ? 'text-cyber-primary border-cyber-primary bg-cyber-primary/5'
              : 'text-gray-500 border-transparent hover:text-gray-300'
          )}
        >
          Audit Logs
        </button>
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

      {/* Resource ACL Tab */}
      {activeTab === 'resource-acl' && (
        <>
          {/* Filters */}
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <Input
                  placeholder="Search ACL rules..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Access Mode Filter */}
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-500" />
                <select
                  value={accessModeFilter}
                  onChange={(e) => setAccessModeFilter(e.target.value)}
                  className="px-4 py-2 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
                >
                  <option value="">All Modes</option>
                  <option value="any">Public (Any)</option>
                  <option value="rbac">RBAC</option>
                </select>
              </div>
            </div>
          </Card>

          {/* ACL Rules Table */}
          <ACLResourceTable
            rules={filteredRules}
            loading={rulesLoading}
            onEdit={handleEdit}
            onDelete={handleDelete}
            deleteConfirm={deleteConfirm}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500 font-mono">
                Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, total)} of {total} rules
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
        </>
      )}

      {/* API Keys Tab */}
      {activeTab === 'rules' && (
        <Card>
          <div className="text-center py-12">
            <FileKey className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono mb-2">API Key Management</p>
            <p className="text-xs text-gray-600">Create and manage API keys for programmatic access</p>
          </div>
        </Card>
      )}

      {/* Audit Logs Tab */}
      {activeTab === 'logs' && (
        <Card>
          <div className="text-center py-12">
            <Shield className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono mb-2">Audit logs coming soon</p>
            <p className="text-xs text-gray-600">View all access attempts and security events</p>
          </div>
        </Card>
      )}

      {/* Create Modal */}
      <ACLResourceFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        mode="create"
        resources={resources.map((r: Resource) => ({ id: r.id, name: r.name }))}
      />

      {/* Edit Modal */}
      {editingRuleId && editingRule && !editingRuleLoading && (
        <ACLResourceFormModal
          isOpen={!!editingRuleId && !!editingRule}
          onClose={() => setEditingRuleId(null)}
          onSubmit={handleUpdate}
          rule={editingRule}
          mode="edit"
          resources={resources.map((r: Resource) => ({ id: r.id, name: r.name }))}
        />
      )}
    </div>
  );
};
