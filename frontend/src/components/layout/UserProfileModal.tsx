import { Mail, Calendar, Shield, Key, LogOut, ChevronRight } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { User as UserType } from '@/types';

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: UserType | null;
  onLogout?: () => void;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
};

export const UserProfileModal = ({ isOpen, onClose, user, onLogout }: UserProfileModalProps) => {
  if (!user) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="User Profile" size="md">
      <div className="space-y-6">
        {/* User Avatar & Basic Info */}
        <div className="flex items-center gap-4 pb-6 border-b border-void-700">
          <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold text-2xl">
            {user.username[0]?.toUpperCase()}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-display font-semibold text-gray-200">{user.username}</h3>
            <p className="text-sm text-gray-500 font-mono mt-1">ID: {user.id.slice(0, 8)}...</p>
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
            <p className="text-gray-300 font-mono text-sm">{user.email}</p>
          </div>

          {/* Account Created */}
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Member Since</span>
            </div>
            <p className="text-gray-300 text-sm">{formatDate(user.createdAt)}</p>
          </div>

          {/* Roles & Permissions */}
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Roles & Permissions</span>
            </div>
            <div className="space-y-3">
              {user.roles.map((role) => (
                <div key={role.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 font-medium text-sm">{role.name}</span>
                    <Badge className="bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary">
                      {role.permissions.length} {role.permissions.length === 1 ? 'permission' : 'permissions'}
                    </Badge>
                  </div>
                  {role.permissions.length > 0 && (
                    <div className="pl-3 border-l-2 border-void-700 space-y-1">
                      {role.permissions.map((permission) => (
                        <div key={permission.id} className="text-xs text-gray-500 flex items-center gap-2">
                          <ChevronRight className="w-3 h-3 flex-shrink-0" />
                          <span className="font-mono">
                            {permission.resource}:{permission.action}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {user.roles.length === 0 && (
                <p className="text-gray-500 text-sm italic">No roles assigned</p>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-void-700">
          <Button
            variant="secondary"
            className="flex-1"
            onClick={() => {
              onClose();
              // Navigate to settings or profile edit page if needed
            }}
          >
            <Key className="w-4 h-4 mr-2" />
            Edit Profile
          </Button>
          <Button
            variant="danger"
            className="flex-1"
            onClick={() => {
              onClose();
              onLogout?.();
            }}
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </Modal>
  );
};
