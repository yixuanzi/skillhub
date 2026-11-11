import { useState, useEffect } from 'react';
import { Plus, Key, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Card } from '@/components/ui/Card';

interface APIKeyFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; expires_at?: string }) => void;
}

export const APIKeyFormModal = ({ isOpen, onClose, onSubmit }: APIKeyFormModalProps) => {
  const [name, setName] = useState('');
  const [expiration, setExpiration] = useState<'never' | '30' | '90' | '365'>('never');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setName('');
      setExpiration('never');
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      const expires_at = expiration !== 'never'
        ? new Date(Date.now() + parseInt(expiration) * 24 * 60 * 60 * 1000).toISOString()
        : undefined;

      onSubmit({ name: name.trim(), expires_at });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 animate-slide-in">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-cyber-primary/10 border border-cyber-primary/30">
            <Key className="w-5 h-5 text-cyber-primary" />
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold text-gray-100">Create API Key</h2>
            <p className="text-sm text-gray-500">
              Generate a new API key for programmatic access
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <Label htmlFor="name">Key Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Production API Key"
              className="mt-1.5"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              A descriptive name to help you identify this key
            </p>
          </div>

          {/* Expiration */}
          <div>
            <Label htmlFor="expiration">Expiration</Label>
            <select
              id="expiration"
              value={expiration}
              onChange={(e) => setExpiration(e.target.value as typeof expiration)}
              className="mt-1.5 w-full px-4 py-2 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
            >
              <option value="never">Never</option>
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="365">1 year</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Keys that don't expire are convenient but less secure
            </p>
          </div>

          {/* Warning */}
          <Card className="p-3 border-cyber-secondary/30 bg-cyber-secondary/5">
            <div className="flex gap-2">
              <AlertCircle className="w-4 h-4 text-cyber-secondary flex-shrink-0 mt-0.5" />
              <p className="text-xs text-gray-400">
                This key acts as you: anyone holding it can do whatever your account can do.
                It will be displayed only once, so copy it and store it securely.
              </p>
            </div>
          </Card>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={!name.trim()}
              className="group"
            >
              <Plus className="w-4 h-4 mr-2 transition-transform group-hover:rotate-90" />
              Create API Key
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
