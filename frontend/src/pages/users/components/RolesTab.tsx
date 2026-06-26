import { useState } from 'react';
import { Plus, Pencil, Trash2, Shield, AlertTriangle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table';
import { cn } from '@/utils/cn';
import { useRoles, useCreateRole, useUpdateRole, useDeleteRole } from '@/hooks/use-user-management';

interface Role {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

const formatRelativeTime = (dateString: string) => {
  const seconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return `${Math.floor(seconds / 604800)}w ago`;
};

interface RoleFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  role?: Role | null;
}

const RoleFormModal = ({ open, onOpenChange, role }: RoleFormModalProps) => {
  const isEdit = !!role;
  const createRole = useCreateRole();
  const updateRole = useUpdateRole();

  const [form, setForm] = useState({ name: role?.name || '', description: role?.description || '' });
  const [error, setError] = useState('');

  const isPending = createRole.isPending || updateRole.isPending;

  const handleClose = () => {
    setError('');
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!form.name.trim()) { setError('Role name is required'); return; }

    try {
      if (isEdit && role) {
        await updateRole.mutateAsync({ roleId: role.id, data: { name: form.name, description: form.description || undefined } });
      } else {
        await createRole.mutateAsync({ name: form.name, description: form.description || undefined });
      }
      handleClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${isEdit ? 'update' : 'create'} role`);
    }
  };

  // sync form when role changes
  if (open && role && form.name !== role.name && !error) {
    setForm({ name: role.name, description: role.description || '' });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-cyber-primary" />
            {isEdit ? 'Edit Role' : 'Create Role'}
          </DialogTitle>
          <DialogDescription>
            {isEdit ? `Editing role: ${role?.name}` : 'Create a new role for access control'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <Alert variant="danger"><span className="text-sm">{error}</span></Alert>}

          <div className="space-y-2">
            <Label htmlFor="role-name">Name</Label>
            <Input
              id="role-name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. editor, viewer"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role-desc">Description (optional)</Label>
            <Input
              id="role-desc"
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              placeholder="Describe what this role can do"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={handleClose} disabled={isPending}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isPending}>
              {isPending ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Role'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const RolesTab = () => {
  const [filters, setFilters] = useState({ page: 1, size: 20, search: '' });
  const [searchInput, setSearchInput] = useState('');

  const { data, isLoading } = useRoles(filters);
  const roles = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / filters.size);

  const deleteRole = useDeleteRole();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Role | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSearch = (value: string) => {
    setSearchInput(value);
    setFilters(prev => ({ ...prev, search: value, page: 1 }));
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role);
    setIsFormOpen(true);
  };

  const handleDelete = async (role: Role) => {
    if (deleteConfirm?.id !== role.id) {
      setDeleteConfirm(role);
      return;
    }
    setError('');
    try {
      await deleteRole.mutateAsync(role.id);
      setSuccess(`Role "${role.name}" deleted`);
      setDeleteConfirm(null);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete role');
      setDeleteConfirm(null);
    }
  };

  return (
    <div className="space-y-4">
      {success && (
        <Alert variant="success"><span className="text-sm">{success}</span></Alert>
      )}
      {error && (
        <Alert variant="danger"><span className="text-sm">{error}</span></Alert>
      )}

      <Card>
        <div className="p-4 border-b border-void-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyber-secondary/10">
              <Shield className="w-5 h-5 text-cyber-secondary" />
            </div>
            <div>
              <h2 className="font-display text-lg font-semibold text-gray-100">Roles</h2>
              <p className="text-xs text-gray-500 font-mono">
                {total} {total === 1 ? 'role' : 'roles'} total
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                placeholder="Search roles..."
                value={searchInput}
                onChange={e => handleSearch(e.target.value)}
                className="pl-9 h-9 w-48"
              />
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => { setEditingRole(null); setIsFormOpen(true); }}
              className="group"
            >
              <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
              New Role
            </Button>
          </div>
        </div>

        <div className="p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-void-700 border-t-cyber-primary rounded-full animate-spin" />
            </div>
          ) : roles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-void-800 border border-void-600 flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-gray-500" />
              </div>
              <h3 className="text-lg font-mono font-semibold text-gray-300 mb-2">
                {filters.search ? 'No Roles Found' : 'No Roles Yet'}
              </h3>
              <p className="text-sm text-gray-500 text-center">
                {filters.search
                  ? `No roles match "${filters.search}"`
                  : 'Create your first role to start managing access control.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
            <div className="border border-void-700 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-28">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map((role, index) => (
                    <TableRow
                      key={role.id}
                      className="animate-slide-in"
                      style={{ animationDelay: `${index * 0.04}s` }}
                    >
                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <Badge variant="secondary" className="w-fit font-mono text-xs">
                            {role.name}
                          </Badge>
                          <code className="text-xs text-gray-600 font-mono">{role.id}</code>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-400">
                          {role.description || <span className="text-gray-600 italic">No description</span>}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-gray-500 font-mono">
                          {formatRelativeTime(role.created_at)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(role)}
                            className="p-1.5"
                            title="Edit role"
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(role)}
                            className={cn(
                              'p-1.5 transition-all duration-200',
                              deleteConfirm?.id === role.id
                                ? 'bg-cyber-accent/20 border border-cyber-accent text-cyber-accent animate-pulse'
                                : 'text-cyber-accent hover:text-cyber-accent'
                            )}
                            title={deleteConfirm?.id === role.id ? 'Confirm delete' : 'Delete role'}
                          >
                            {deleteConfirm?.id === role.id
                              ? <AlertTriangle className="w-4 h-4" />
                              : <Trash2 className="w-4 h-4" />
                            }
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={filters.page === 1}
                  className="p-1.5"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-500 font-mono px-2">
                  Page {filters.page} of {totalPages}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={filters.page === totalPages}
                  className="p-1.5"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
            </div>
          )}
        </div>
      </Card>

      <RoleFormModal
        open={isFormOpen}
        onOpenChange={(open) => {
          setIsFormOpen(open);
          if (!open) setEditingRole(null);
        }}
        role={editingRole}
      />
    </div>
  );
};
