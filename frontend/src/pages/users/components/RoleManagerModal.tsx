import React, { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { Checkbox } from '@/components/ui/Checkbox';
import { Alert } from '@/components/ui/Alert';
import { useRoles, useAssignRoles } from '@/hooks/use-user-management';

interface Props {
  user: {
    id: string;
    username: string;
    roles: Array<{ id: string; name: string }>;
  };
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const RoleManagerModal: React.FC<Props> = ({ user, open, onOpenChange }) => {
  const { data: roles, isLoading } = useRoles();
  const assignRoles = useAssignRoles();

  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>(
    user.roles.map(r => r.id)
  );
  const [error, setError] = useState('');

  // Reset selected roles when user changes
  useEffect(() => {
    setSelectedRoleIds(user.roles.map(r => r.id));
    setError('');
  }, [user]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    assignRoles.mutate(
      { userId: user.id, roleIds: selectedRoleIds },
      {
        onSuccess: () => {
          onOpenChange(false);
        },
        onError: (err: any) => {
          setError(err.message || 'Failed to assign roles');
        },
      }
    );
  };

  const toggleRole = (roleId: string) => {
    setSelectedRoleIds(prev =>
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  if (isLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <div className="flex items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-void-700 border-t-cyber-primary rounded-full animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-cyber-primary" />
            Manage Roles
          </DialogTitle>
          <DialogDescription>
            Assign roles to <span className="font-mono text-cyber-primary">{user.username}</span>
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error Alert */}
          {error && (
            <Alert variant="danger">
              <span className="text-sm font-medium">{error}</span>
            </Alert>
          )}

          <div>
            <Label>Roles</Label>
            <div className="space-y-2 mt-3">
              {roles?.map((role) => (
                <div
                  key={role.id}
                  className="flex items-center gap-3 p-3 rounded-lg border border-void-700 hover:border-void-600 transition-colors"
                >
                  <Checkbox
                    id={role.id}
                    checked={selectedRoleIds.includes(role.id)}
                    onCheckedChange={() => toggleRole(role.id)}
                  />
                  <div className="flex-1">
                    <Label htmlFor={role.id} className="text-sm cursor-pointer font-mono">
                      {role.name}
                    </Label>
                    {role.description && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {role.description}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {(!roles || roles.length === 0) && (
                <p className="text-sm text-gray-500 text-center py-4">
                  No roles available. Create roles first.
                </p>
              )}
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={assignRoles.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={assignRoles.isPending}
            >
              {assignRoles.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
