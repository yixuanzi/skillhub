import { useState, useEffect } from 'react';
import {
  Mail,
  Calendar,
  Shield,
  User,
  Edit,
  Eye,
  EyeOff,
  Loader2,
  Check,
  X,
  CheckCircle
} from 'lucide-react';
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
    permissions?: Array<{
      id: string;
      resource: string;
      action: string;
    }>;
  }>;
  created_at: string;
  updated_at?: string;
}

interface Props {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const UserDetailModal: React.FC<Props> = ({ user, open, onOpenChange }) => {
  // Fetch the latest user data from the server
  const { data: latestUser, isLoading: isLoadingUser } = useUser(user?.id || '');
  // Use the latest data if available, otherwise fall back to the prop
  const currentUser = latestUser || user;

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    is_active: true,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const updateUser = useUpdateUser();

  useEffect(() => {
    if (currentUser) {
      setEditData({
        username: currentUser.username,
        email: currentUser.email,
        password: '',
        confirmPassword: '',
        is_active: currentUser.is_active,
      });
      setError('');
      setSuccess('');
      setIsEditing(false);
    }
  }, [currentUser, open]);

  if (!user) return null;

  // Show loading state while fetching latest user data
  if (isLoadingUser) {
    return (
      <Modal isOpen={open} onClose={() => onOpenChange(false)} title="User Details" size="lg">
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 text-cyber-primary animate-spin" />
            <p className="text-sm text-gray-400 font-mono">Loading user details...</p>
          </div>
        </div>
      </Modal>
    );
  }

  // Safety check - if currentUser is null, don't render
  if (!currentUser) {
    return null;
  }

  const handleEdit = () => {
    setIsEditing(true);
    setError('');
    setSuccess('');
  };

  const handleCancel = () => {
    setIsEditing(false);
    if (!currentUser) return;
    setEditData({
      username: currentUser.username,
      email: currentUser.email,
      password: '',
      confirmPassword: '',
      is_active: currentUser.is_active,
    });
    setError('');
  };

  const handleSave = async () => {
    if (!currentUser) return;

    setError('');
    setSuccess('');

    // Validation
    if (!editData.username || editData.username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }

    if (!editData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (editData.password) {
      if (editData.password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }
      if (editData.password !== editData.confirmPassword) {
        setError('Passwords do not match');
        return;
      }
    }

    try {
      const data: {
        username?: string;
        email?: string;
        is_active?: boolean;
        password?: string;
      } = {
        username: editData.username !== currentUser.username ? editData.username : undefined,
        email: editData.email !== currentUser.email ? editData.email : undefined,
        is_active: editData.is_active !== currentUser.is_active ? editData.is_active : undefined,
      };

      if (editData.password) {
        data.password = editData.password;
      }

      // Remove undefined values
      Object.keys(data).forEach(key => {
        const k = key as keyof typeof data;
        if (data[k] === undefined) delete data[k];
      });

      await updateUser.mutateAsync({ userId: currentUser.id, data });
      setSuccess('User updated successfully');
      setIsEditing(false);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to update user');
    }
  };

  return (
    <Modal isOpen={open} onClose={() => onOpenChange(false)} title="User Details" size="lg">
      <div className="space-y-6">
        {/* Success Message */}
        {success && (
          <Alert variant="success" className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm">{success}</span>
          </Alert>
        )}

        {/* Error Message */}
        {error && (
          <Alert variant="danger">
            <span className="text-sm">{error}</span>
          </Alert>
        )}

        {/* User Avatar & Basic Info */}
        <div className="flex items-center gap-4 pb-6 border-b border-void-700">
          <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold text-2xl">
            {currentUser.username[0]?.toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-display font-semibold text-gray-200">
                {isEditing ? (
                  <Input
                    value={editData.username}
                    onChange={(e) => setEditData({ ...editData, username: e.target.value })}
                    className="h-8 text-lg font-semibold"
                    minLength={3}
                    maxLength={50}
                  />
                ) : (
                  currentUser.username
                )}
              </h3>
              {isEditing && (
                <Badge variant={editData.is_active ? 'success' : 'secondary'}>
                  {editData.is_active ? 'Active' : 'Inactive'}
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-500 font-mono mt-1">ID: {currentUser.id}</p>
          </div>
        </div>

        {/* User Details */}
        <div className="space-y-4">
          {/* Email */}
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-2">
              <Mail className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Email</span>
            </div>
            {isEditing ? (
              <Input
                type="email"
                value={editData.email}
                onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                placeholder="Enter email"
              />
            ) : (
              <p className="text-gray-300 font-mono text-sm">{currentUser.email}</p>
            )}
          </div>

          {/* Account Status (only in edit mode) */}
          {isEditing && (
            <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <User className="w-4 h-4 text-gray-500" />
                    <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                      Account Status
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Enable or disable this user account
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setEditData({ ...editData, is_active: !editData.is_active })}
                  className={cn(
                    'relative w-12 h-6 rounded-full transition-colors duration-200',
                    editData.is_active ? 'bg-cyber-primary' : 'bg-void-700'
                  )}
                >
                  <div
                    className={cn(
                      'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform duration-200',
                      editData.is_active ? 'left-7' : 'left-1'
                    )}
                  />
                </button>
              </div>
            </div>
          )}

          {/* Password Change (only in edit mode) */}
          {isEditing && (
            <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-gray-500" />
                <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                  New Password (Optional)
                </span>
              </div>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={editData.password}
                  onChange={(e) => setEditData({ ...editData, password: e.target.value })}
                  placeholder="Leave empty to keep current password"
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-500 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {editData.password && (
                <div className="relative mt-2">
                  <Input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={editData.confirmPassword}
                    onChange={(e) => setEditData({ ...editData, confirmPassword: e.target.value })}
                    placeholder="Confirm new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-3 text-gray-500 hover:text-gray-300"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Account Created */}
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                Account Information
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 mb-1">Created</p>
                <p className="text-gray-300 text-sm">{formatDate(currentUser.created_at)}</p>
              </div>
              {currentUser.updated_at && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Last Updated</p>
                  <p className="text-gray-300 text-sm">{formatDate(currentUser.updated_at)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Roles & Permissions */}
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">
                Roles & Permissions
              </span>
            </div>
            <div className="space-y-3">
              {currentUser.roles.map((role) => (
                <div key={role.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 font-medium text-sm">{role.name}</span>
                    <Badge className="bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary">
                      {role.permissions?.length || 0} {role.permissions?.length === 1 ? 'permission' : 'permissions'}
                    </Badge>
                  </div>
                  {role.permissions && role.permissions.length > 0 && (
                    <div className="pl-3 border-l-2 border-void-700 space-y-1">
                      {role.permissions.map((permission) => (
                        <div key={permission.id} className="text-xs text-gray-500 flex items-center gap-2">
                          <span className="text-cyber-secondary">›</span>
                          <span className="font-mono">
                            {permission.resource}:{permission.action}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {currentUser.roles.length === 0 && (
                <p className="text-gray-500 text-sm italic">No roles assigned</p>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-void-700">
          {isEditing ? (
            <>
              <Button
                variant="secondary"
                className="flex items-center gap-2"
                onClick={handleCancel}
                disabled={updateUser.isPending}
              >
                <X className="w-4 h-4" />
                Cancel
              </Button>
              <Button
                variant="primary"
                className="flex items-center gap-2"
                onClick={handleSave}
                disabled={updateUser.isPending}
              >
                {updateUser.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="secondary"
                className="flex items-center gap-2"
                onClick={() => onOpenChange(false)}
              >
                Close
              </Button>
              <Button
                variant="primary"
                className="flex items-center gap-2"
                onClick={handleEdit}
              >
                <Edit className="w-4 h-4" />
                Edit User
              </Button>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
};
