import { useState, useEffect } from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { useUpdateUser, useChangePassword } from '@/hooks/useAuth';
import { User } from '@/types';

interface EditProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
}

export const EditProfileModal = ({ isOpen, onClose, user }: EditProfileModalProps) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const updateUser = useUpdateUser();

  useEffect(() => {
    if (user) { setUsername(user.username); setEmail(user.email); setError(''); }
  }, [user, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (username.length < 3) { setError('Username must be at least 3 characters'); return; }
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('Please enter a valid email address'); return; }
    try {
      await updateUser.mutateAsync({
        username: username !== user?.username ? username : undefined,
        email: email !== user?.email ? email : undefined,
      });
      onClose();
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to update profile');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Profile">
      <form onSubmit={handleSubmit} className="space-y-3 text-sm">
        {error && <Alert variant="danger"><span className="text-sm">{error}</span></Alert>}
        <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" minLength={3} maxLength={50} required />
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" required />
        <div className="flex gap-2 pt-2">
          <Button type="button" variant="secondary" size="sm" className="flex-1" onClick={onClose} disabled={updateUser.isPending}>Cancel</Button>
          <Button type="submit" variant="primary" size="sm" className="flex-1" disabled={updateUser.isPending}>
            {updateUser.isPending ? <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Saving...</> : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PwdInput = ({
  label, value, onChange, show, onToggle, placeholder, required, minLength,
}: {
  label: string; value: string; onChange: (v: string) => void;
  show: boolean; onToggle: () => void; placeholder?: string; required?: boolean; minLength?: number;
}) => (
  <div>
    <label className="block text-xs font-mono text-gray-400 mb-1">{label}</label>
    <div className="relative">
      <Input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
        className="pr-9"
      />
      <button type="button" onClick={onToggle} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
        {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
      </button>
    </div>
  </div>
);

export const ChangePasswordModal = ({ isOpen, onClose }: ChangePasswordModalProps) => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const changePassword = useChangePassword();

  useEffect(() => {
    if (isOpen) { setOldPassword(''); setNewPassword(''); setConfirmPassword(''); setError(''); }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPassword.length < 8) { setError('New password must be at least 8 characters'); return; }
    if (newPassword !== confirmPassword) { setError('Passwords do not match'); return; }
    try {
      await changePassword.mutateAsync({ old_password: oldPassword, new_password: newPassword });
      onClose();
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail || 'Failed to change password');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Change Password">
      <form onSubmit={handleSubmit} className="space-y-3 text-sm">
        {error && <Alert variant="danger"><span className="text-sm">{error}</span></Alert>}
        <PwdInput label="Current Password" value={oldPassword} onChange={setOldPassword} show={showOld} onToggle={() => setShowOld(!showOld)} placeholder="Current password" required />
        <PwdInput label="New Password" value={newPassword} onChange={setNewPassword} show={showNew} onToggle={() => setShowNew(!showNew)} placeholder="Min 8 characters" minLength={8} required />
        <PwdInput label="Confirm New Password" value={confirmPassword} onChange={setConfirmPassword} show={showConfirm} onToggle={() => setShowConfirm(!showConfirm)} placeholder="Confirm new password" required />
        <div className="flex gap-2 pt-2">
          <Button type="button" variant="secondary" size="sm" className="flex-1" onClick={onClose} disabled={changePassword.isPending}>Cancel</Button>
          <Button type="submit" variant="primary" size="sm" className="flex-1" disabled={changePassword.isPending}>
            {changePassword.isPending ? <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Changing...</> : 'Change Password'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
