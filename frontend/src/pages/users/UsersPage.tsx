import { useState } from 'react';
import { Users, Shield, Search, Plus, CheckCircle } from 'lucide-react';
import { Card, Input, Alert } from '@/components/ui';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { useUsers, useRoles, useDeleteUser } from '@/hooks/use-user-management';
import { UserTable, RoleManagerModal, UserDetailModal, UserCreateModal, RolesTab } from './components';

export const UsersPage = () => {
  const [activeTab, setActiveTab] = useState('users');

  // Users tab state
  const [filters, setFilters] = useState({ page: 1, size: 20, search: '' });
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { data } = useUsers(filters);
  const { data: rolesData } = useRoles();
  const deleteUser = useDeleteUser();

  const users = data?.items || [];
  const total = data?.total || 0;
  const roles = rolesData?.items || [];

  const showSuccess = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const handleFilterChange = (newFilters: Partial<typeof filters>) =>
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));

  const handleManageRoles = (user: any) => {
    setSelectedUser(user);
    setIsRoleModalOpen(true);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleViewDetails = (user: any) => {
    setSelectedUser(user);
    setIsDetailModalOpen(true);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleDelete = async (user: any) => {
    if (deleteConfirm !== user.id) {
      setDeleteConfirm(user.id);
      return;
    }
    setErrorMessage('');
    try {
      await deleteUser.mutateAsync(user.id);
      showSuccess(`User "${user.username}" deleted`);
      setDeleteConfirm(null);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to delete user');
      setDeleteConfirm(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">Users & Roles</h1>
        <p className="font-mono text-sm text-gray-500">Manage user accounts and access control roles</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="users" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="roles" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Roles
          </TabsTrigger>
        </TabsList>

        {/* ── Users Tab ── */}
        <TabsContent value="users">
          <div className="space-y-4">
            {successMessage && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-cyber-primary/30 bg-cyber-primary/10 animate-slide-in">
                <CheckCircle className="w-4 h-4 text-cyber-primary flex-shrink-0" />
                <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
              </div>
            )}
            {errorMessage && (
              <Alert variant="danger">
                <span className="text-sm font-medium">{errorMessage}</span>
              </Alert>
            )}

            {/* Filters */}
            <Card className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <Input
                    placeholder="Search users..."
                    value={filters.search}
                    onChange={e => handleFilterChange({ search: e.target.value })}
                    className="pl-10"
                  />
                </div>
                <select
                  className="h-10 px-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
                  value={filters.size}
                  onChange={e => handleFilterChange({ size: Number(e.target.value) })}
                >
                  <option value={20}>20 per page</option>
                  <option value={50}>50 per page</option>
                  <option value={100}>100 per page</option>
                </select>
              </div>
            </Card>

            {/* Table */}
            <Card>
              <div className="p-4 border-b border-void-700 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-cyber-primary/10">
                    <Users className="w-5 h-5 text-cyber-primary" />
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-semibold text-gray-100">Users</h2>
                    <p className="text-xs text-gray-500 font-mono">
                      {total} {total === 1 ? 'user' : 'users'} total
                    </p>
                  </div>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsCreateModalOpen(true)}
                  className="group"
                >
                  <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
                  New User
                </Button>
              </div>
              <div className="p-4">
                <UserTable
                  users={users}
                  total={total}
                  page={filters.page}
                  size={filters.size}
                  onPageChange={page => setFilters(prev => ({ ...prev, page }))}
                  onManageRoles={handleManageRoles}
                  onViewDetails={handleViewDetails}
                  onDelete={handleDelete}
                  deleteConfirm={deleteConfirm}
                />
              </div>
            </Card>
          </div>
        </TabsContent>

        {/* ── Roles Tab ── */}
        <TabsContent value="roles">
          <RolesTab />
        </TabsContent>
      </Tabs>

      {/* Modals */}
      <UserCreateModal
        open={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        roles={roles || []}
      />
      {selectedUser && (
        <RoleManagerModal
          user={selectedUser}
          open={isRoleModalOpen}
          onOpenChange={setIsRoleModalOpen}
        />
      )}
      {selectedUser && (
        <UserDetailModal
          user={selectedUser}
          open={isDetailModalOpen}
          onOpenChange={setIsDetailModalOpen}
        />
      )}
    </div>
  );
};
