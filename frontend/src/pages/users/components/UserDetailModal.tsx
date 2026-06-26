import { useState, useEffect } from 'react';
import { Mail, Calendar, Shield, User, Edit, Eye, EyeOff, Loader2, Check, X, CheckCircle } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { cn } from '@/utils/cn';
import { useUpdateUser, useUser } from '@/hooks/use-user-management';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  roles: Array<{
    id: string;
    name: string;
    description?: string;
    permissions?: Array<{ id: string; resource: string; action: string }>;
  }>;
  created_at: string;
  updated_at?: string;
}

interface Props {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const toUTCDate = (ts: string) => new Date(/[Z+]/.test(ts) ? ts : ts + 'Z');
const formatDate = (ts: string) =>
  toUTCDate(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

const Row = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="flex items-start gap-3 py-1.5 border-b border-void-700/40 last:border-0">
    <span className="w-24 shrink-0 text-xs font-mono text-gray-500 uppercase pt-0.5">{label}</span>
    <span className="flex-1 min-w-0">{children}</span>
  </div>
);

export const UserDetailModal: React.FC<Props> = ({ user, open, onOpenChange }) => {
  const { data: latestUser, isLoading } = useUser(user?.id || '');
  const currentUser = latestUser || user;

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({ username: '', email: '', password: '', confirmPassword: '', is_active: true });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const updateUser = useUpdateUser();

  useEffect(() => {
    if (currentUser) {
      setEditData({ username: currentUser.username, email: currentUser.email, password: '', confirmPassword: '', is_active: currentUser.is_active });
      setError(''); setSuccess(''); setIsEditing(false);
    }
  }, [currentUser, open]);

  if (!user) return null;

  if (isLoading) {
    return (
      <Modal isOpen={open} onClose={() => onOpenChange(false)} title="User Details">
        <div className="flex items-center justify-center py-10">
          <Loader2 className="w-6 h-6 text-cyber-primary animate-spin" />
        </div>
      </Modal>
    );
  }

  if (!currentUser) return null;

  const handleCancel = () => {
    setIsEditing(false);
    setEditData({ username: currentUser.username, email: currentUser.email, password: '', confirmPassword: '', is_active: currentUser.is_active });
    setError('');
  };

  const handleSave = async () => {
    setError(''); setSuccess('');
    if (!editData.username || editData.username.length < 3) { setError('Username must be at least 3 characters'); return; }
    if (!editData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editData.email)) { setError('Please enter a valid email address'); return; }
    if (editData.password) {
      if (editData.password.length < 8) { setError('Password must be at least 8 characters'); return; }
      if (editData.password !== editData.confirmPassword) { setError('Passwords do not match'); return; }
    }
    try {
      const data: Record<string, unknown> = {
        ...(editData.username !== currentUser.username && { username: editData.username }),
        ...(editData.email !== currentUser.email && { email: editData.email }),
        ...(editData.is_active !== currentUser.is_active && { is_active: editData.is_active }),
        ...(editData.password && { password: editData.password }),
      };
      await updateUser.mutateAsync({ userId: currentUser.id, data });
      setSuccess('User updated successfully');
      setIsEditing(false);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to update user');
    }
  };

  return (
    <Modal isOpen={open} onClose={() => onOpenChange(false)} title="User Details">
      <div className="space-y-4 text-sm">
        {success && (
          <Alert variant="success" className="flex items-center gap-2 py-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span className="text-sm">{success}</span>
          </Alert>
        )}
        {error && <Alert variant="danger"><span className="text-sm">{error}</span></Alert>}

        {/* Header */}
        <div className="flex items-center gap-3 pb-3 border-b border-void-700">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold text-base shrink-0">
            {currentUser.username[0]?.toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            {isEditing ? (
              <Input
                value={editData.username}
                onChange={(e) => setEditData({ ...editData, username: e.target.value })}
                className="h-7 text-sm font-semibold"
                minLength={3} maxLength={50}
              />
            ) : (
              <p className="text-gray-100 font-semibold truncate">{currentUser.username}</p>
            )}
            <p className="text-xs text-gray-500 font-mono truncate">{currentUser.id}</p>
          </div>
          <Badge variant={currentUser.is_active ? 'success' : 'secondary'} className="text-xs shrink-0">
            {currentUser.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Fields */}
        <div className="bg-void-900/50 rounded-lg px-3 py-1 border border-void-700">
          <Row label="Email">
            {isEditing ? (
              <Input type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })} className="h-7 text-sm" />
            ) : (
              <span className="font-mono text-gray-300 text-xs">{currentUser.email}</span>
            )}
          </Row>

          {isEditing && (
            <Row label="Status">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setEditData({ ...editData, is_active: !editData.is_active })}
                  className={cn('relative w-10 h-5 rounded-full transition-colors duration-200', editData.is_active ? 'bg-cyber-primary' : 'bg-void-700')}
                >
                  <div className={cn('absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200', editData.is_active ? 'left-5' : 'left-0.5')} />
                </button>
                <span className="text-xs text-gray-400">{editData.is_active ? 'Active' : 'Inactive'}</span>
              </div>
            </Row>
          )}

          {isEditing && (
            <Row label="Password">
              <div className="space-y-1.5">
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={editData.password}
                    onChange={(e) => setEditData({ ...editData, password: e.target.value })}
                    placeholder="Leave empty to keep current"
                    className="h-7 text-sm pr-8"
                    minLength={8}
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-2 top-1.5 text-gray-500 hover:text-gray-300">
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
                {editData.password && (
                  <div className="relative">
                    <Input
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={editData.confirmPassword}
                      onChange={(e) => setEditData({ ...editData, confirmPassword: e.target.value })}
                      placeholder="Confirm new password"
                      className="h-7 text-sm pr-8"
                    />
                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-2 top-1.5 text-gray-500 hover:text-gray-300">
                      {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                )}
              </div>
            </Row>
          )}

          <Row label="Created">
            <span className="text-gray-400 text-xs">{formatDate(currentUser.created_at)}</span>
          </Row>
          {currentUser.updated_at && (
            <Row label="Updated">
              <span className="text-gray-400 text-xs">{formatDate(currentUser.updated_at)}</span>
            </Row>
          )}
        </div>

        {/* Roles */}
        <div>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Shield className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Roles</span>
          </div>
          {currentUser.roles.length === 0 ? (
            <p className="text-xs text-gray-500 italic px-1">No roles assigned</p>
          ) : (
            <div className="bg-void-900/50 rounded-lg px-3 py-1 border border-void-700 space-y-0">
              {currentUser.roles.map((role) => (
                <div key={role.id} className="flex items-center justify-between py-1.5 border-b border-void-700/40 last:border-0">
                  <span className="text-gray-300 text-xs font-mono">{role.name}</span>
                  <Badge className="text-xs bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary">
                    {role.permissions?.length ?? 0} perms
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t border-void-700">
          {isEditing ? (
            <>
              <Button variant="secondary" size="sm" className="flex items-center gap-1.5" onClick={handleCancel} disabled={updateUser.isPending}>
                <X className="w-3.5 h-3.5" /> Cancel
              </Button>
              <Button variant="primary" size="sm" className="flex items-center gap-1.5" onClick={handleSave} disabled={updateUser.isPending}>
                {updateUser.isPending ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving...</> : <><Check className="w-3.5 h-3.5" /> Save</>}
              </Button>
            </>
          ) : (
            <>
              <Button variant="secondary" size="sm" onClick={() => onOpenChange(false)}>Close</Button>
              <Button variant="primary" size="sm" className="flex items-center gap-1.5" onClick={() => setIsEditing(true)}>
                <Edit className="w-3.5 h-3.5" /> Edit
              </Button>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
};
