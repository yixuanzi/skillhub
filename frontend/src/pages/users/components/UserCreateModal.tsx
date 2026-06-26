import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Checkbox } from '@/components/ui/Checkbox';
import { Alert } from '@/components/ui/Alert';
import apiClient from '@/api/client';
import { useQueryClient } from '@tanstack/react-query';

interface Role {
  id: string;
  name: string;
  description?: string;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roles: Role[];
}

export const UserCreateModal = ({ open, onOpenChange, roles }: Props) => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ username: '', email: '', password: '', is_active: true });
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [isPending, setIsPending] = useState(false);

  const reset = () => {
    setForm({ username: '', email: '', password: '', is_active: true });
    setSelectedRoleIds([]);
    setError('');
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  const toggleRole = (id: string) =>
    setSelectedRoleIds(prev => prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.username.length < 3) { setError('Username must be at least 3 characters'); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) { setError('Invalid email address'); return; }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return; }

    setIsPending(true);
    try {
      await apiClient.post('/admin/users/', {
        ...form,
        role_ids: selectedRoleIds,
      });
      queryClient.invalidateQueries({ queryKey: ['users'] });
      handleClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-cyber-primary" />
            Create User
          </DialogTitle>
          <DialogDescription>Add a new user account</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <Alert variant="danger"><span className="text-sm">{error}</span></Alert>}

          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })}
              placeholder="Enter username"
              minLength={3}
              maxLength={50}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="Enter email"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="Min 8 characters"
              minLength={8}
              required
            />
          </div>

          {roles.length > 0 && (
            <div className="space-y-2">
              <Label>Roles (optional)</Label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {roles.map(role => (
                  <div
                    key={role.id}
                    className="flex items-center gap-3 p-2.5 rounded-lg border border-void-700 hover:border-void-600 transition-colors"
                  >
                    <Checkbox
                      id={`create-${role.id}`}
                      checked={selectedRoleIds.includes(role.id)}
                      onCheckedChange={() => toggleRole(role.id)}
                    />
                    <Label htmlFor={`create-${role.id}`} className="text-sm cursor-pointer font-mono">
                      {role.name}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={handleClose} disabled={isPending}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isPending}>
              {isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
