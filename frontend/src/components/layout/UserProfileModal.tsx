import { useState } from 'react';
import { Mail, Calendar, Shield, Key, LogOut, Edit } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { User as UserType } from '@/types';
import { EditProfileModal, ChangePasswordModal } from './UserEditModals';

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: UserType | null;
  onLogout?: () => void;
}

const toUTCDate = (ts: string) => new Date(/[Z+]/.test(ts) ? ts : ts + 'Z');
const formatDate = (ts: string) =>
  toUTCDate(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

const Row = ({ icon: Icon, label, children }: { icon: React.ElementType; label: string; children: React.ReactNode }) => (
  <div className="flex items-start gap-3 py-1.5 border-b border-void-700/40 last:border-0">
    <div className="flex items-center gap-1.5 w-28 shrink-0 pt-0.5">
      <Icon className="w-3.5 h-3.5 text-gray-500" />
      <span className="text-xs font-mono text-gray-500 uppercase">{label}</span>
    </div>
    <span className="flex-1 min-w-0">{children}</span>
  </div>
);

export const UserProfileModal = ({ isOpen, onClose, user, onLogout }: UserProfileModalProps) => {
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);

  if (!user) return null;

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Profile">
        <div className="space-y-4 text-sm">
          {/* Header */}
          <div className="flex items-center gap-3 pb-3 border-b border-void-700">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold text-base shrink-0">
              {user.username[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-gray-100 font-semibold truncate">{user.username}</p>
              <p className="text-xs text-gray-500 font-mono">#{user.id.slice(0, 8)}</p>
            </div>
          </div>

          {/* Details */}
          <div className="bg-void-900/50 rounded-lg px-3 py-1 border border-void-700">
            <Row icon={Mail} label="Email">
              <span className="font-mono text-gray-300 text-xs">{user.email}</span>
            </Row>
            <Row icon={Calendar} label="Since">
              <span className="text-gray-400 text-xs">{formatDate(user.createdAt)}</span>
            </Row>
          </div>

          {/* Roles */}
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <Shield className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Roles</span>
            </div>
            {user.roles.length === 0 ? (
              <p className="text-xs text-gray-500 italic px-1">No roles assigned</p>
            ) : (
              <div className="bg-void-900/50 rounded-lg px-3 py-1 border border-void-700">
                {user.roles.map((role) => (
                  <div key={role.id} className="flex items-center justify-between py-1.5 border-b border-void-700/40 last:border-0">
                    <span className="text-gray-300 text-xs font-mono">{role.name}</span>
                    <Badge className="text-xs bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary">
                      {role.permissions.length} perms
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-void-700">
            <Button variant="secondary" size="sm" className="flex items-center justify-center gap-1.5" onClick={() => setIsEditProfileOpen(true)}>
              <Edit className="w-3.5 h-3.5" /> Edit
            </Button>
            <Button variant="secondary" size="sm" className="flex items-center justify-center gap-1.5" onClick={() => setIsChangePasswordOpen(true)}>
              <Key className="w-3.5 h-3.5" /> Password
            </Button>
            <Button variant="danger" size="sm" className="flex items-center justify-center gap-1.5" onClick={() => { onClose(); onLogout?.(); }}>
              <LogOut className="w-3.5 h-3.5" /> Logout
            </Button>
          </div>
        </div>
      </Modal>

      <EditProfileModal isOpen={isEditProfileOpen} onClose={() => setIsEditProfileOpen(false)} user={user} />
      <ChangePasswordModal isOpen={isChangePasswordOpen} onClose={() => setIsChangePasswordOpen(false)} />
    </>
  );
};
