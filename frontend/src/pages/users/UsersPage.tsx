import React, { useState } from 'react';
import { Users, Shield, Search, Filter } from 'lucide-react';
import { Card, Input, Alert } from '@/components/ui';
import { Button } from '@/components/ui/Button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/Select';
import { useUsers, useRoles } from '@/hooks/use-user-management';
import { UserTable, RoleManagerModal } from './components';
import { CheckCircle } from 'lucide-react';

export const UsersPage = () => {
  const [filters, setFilters] = useState({
    page: 1,
    size: 20,
    search: '',
    role_id: '',
  });

  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { data, isLoading, error } = useUsers(filters);
  const { data: roles } = useRoles();

  const users = data?.items || [];
  const total = data?.total || 0;

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleManageRoles = (user: any) => {
    setSelectedUser(user);
    setIsRoleModalOpen(true);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleRoleAssignSuccess = () => {
    setSuccessMessage('Roles updated successfully!');
    setIsRoleModalOpen(false);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const handleRoleAssignError = (error: any) => {
    setErrorMessage(error.message || 'Failed to assign roles');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Success Message */}
      {successMessage && (
        <div className="animate-slide-in">
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-cyber-primary/30 bg-cyber-primary/10">
            <CheckCircle className="w-4 h-4 text-cyber-primary flex-shrink-0" />
            <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <Alert variant="danger">
          <span className="text-sm font-medium">{errorMessage}</span>
        </Alert>
      )}

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
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Search users..."
              value={filters.search}
              onChange={(e) => handleFilterChange({ search: e.target.value })}
              className="pl-10"
            />
          </div>

          {/* Role Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <Select
              value={filters.role_id}
              onValueChange={(value) => handleFilterChange({ role_id: value })}
            >
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Roles</SelectItem>
                {roles?.map((role) => (
                  <SelectItem key={role.id} value={role.id}>
                    {role.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Page Size Selector */}
          <select
            className="h-10 px-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
            value={filters.size}
            onChange={(e) => handleFilterChange({ size: Number(e.target.value) })}
          >
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>
      </Card>

      {/* User Table */}
      <Card>
        <div className="p-4 border-b border-void-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyber-primary/10">
              <Users className="w-5 h-5 text-cyber-primary" />
            </div>
            <div>
              <h2 className="font-display text-lg font-semibold text-gray-100">
                Users
              </h2>
              <p className="text-xs text-gray-500 font-mono">
                {total} {total === 1 ? 'user' : 'users'} total
              </p>
            </div>
          </div>
        </div>

        <div className="p-4">
          <UserTable
            users={users}
            total={total}
            page={filters.page}
            size={filters.size}
            onPageChange={handlePageChange}
            onManageRoles={handleManageRoles}
          />
        </div>
      </Card>

      {/* Role Manager Modal */}
      {selectedUser && (
        <RoleManagerModal
          user={selectedUser}
          open={isRoleModalOpen}
          onOpenChange={setIsRoleModalOpen}
        />
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-primary/10">
              <Users className="w-5 h-5 text-cyber-primary" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">User Management</h3>
              <p className="text-xs text-gray-500">View and manage all user accounts</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-secondary/10">
              <Shield className="w-5 h-5 text-cyber-secondary" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">Role Assignment</h3>
              <p className="text-xs text-gray-500">Assign roles to control access</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-warning/10">
              <Filter className="w-5 h-5 text-cyber-warning" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">Filtering</h3>
              <p className="text-xs text-gray-500">Search and filter by roles</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
