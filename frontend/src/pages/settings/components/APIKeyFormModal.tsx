import { useState, useEffect } from 'react';
import { Plus, Key, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Checkbox } from '@/components/ui/Checkbox';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/utils/cn';

const AVAILABLE_SCOPES = [
  { value: 'resources:read', label: 'Resources - Read', description: 'Read resource configurations' },
  { value: 'resources:write', label: 'Resources - Write', description: 'Create and modify resources' },
  { value: 'skills:read', label: 'Skills - Read', description: 'View skill definitions' },
  { value: 'skills:call', label: 'Skills - Call', description: 'Execute skills' },
  { value: 'skills:write', label: 'Skills - Write', description: 'Create and modify skills' },
  { value: 'acl:read', label: 'ACL - Read', description: 'View ACL rules' },
  { value: 'acl:write', label: 'ACL - Write', description: 'Modify ACL rules' },
  { value: 'users:read', label: 'Users - Read', description: 'View user information' },
  { value: 'audit:read', label: 'Audit Logs - Read', description: 'View audit logs' },
];

interface APIKeyFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; scopes: string[]; expires_at?: string }) => void;
}

export const APIKeyFormModal = ({ isOpen, onClose, onSubmit }: APIKeyFormModalProps) => {
  const [name, setName] = useState('');
  const [scopes, setScopes] = useState<string[]>([]);
  const [expiration, setExpiration] = useState<'never' | '30' | '90' | '365'>('never');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setName('');
      setScopes([]);
      setExpiration('never');
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() && scopes.length > 0) {
      const expires_at = expiration !== 'never'
        ? new Date(Date.now() + parseInt(expiration) * 24 * 60 * 60 * 1000).toISOString()
        : undefined;

      onSubmit({ name: name.trim(), scopes, expires_at });
    }
  };

  const toggleScope = (scope: string) => {
    setScopes((prev) =>
      prev.includes(scope)
        ? prev.filter((s) => s !== scope)
        : [...prev, scope]
    );
  };

  const selectAll = () => {
    setScopes(AVAILABLE_SCOPES.map((s) => s.value));
  };

  const selectNone = () => {
    setScopes([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 animate-slide-in">
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

          {/* Scopes */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <Label>Permissions (Scopes)</Label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={selectAll}
                  className="text-xs text-cyber-primary hover:text-cyber-primary/80 transition-colors"
                >
                  Select All
                </button>
                <span className="text-gray-600">|</span>
                <button
                  type="button"
                  onClick={selectNone}
                  className="text-xs text-cyber-accent hover:text-cyber-accent/80 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
              {AVAILABLE_SCOPES.map((scope) => (
                <div
                  key={scope.value}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border transition-all duration-200',
                    scopes.includes(scope.value)
                      ? 'bg-cyber-primary/5 border-cyber-primary/30'
                      : 'bg-void-900/30 border-void-700/50 hover:border-void-600'
                  )}
                >
                  <Checkbox
                    id={scope.value}
                    checked={scopes.includes(scope.value)}
                    onCheckedChange={() => toggleScope(scope.value)}
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor={scope.value}
                      className={cn(
                        'cursor-pointer text-sm font-medium',
                        scopes.includes(scope.value) ? 'text-cyber-primary' : 'text-gray-300'
                      )}
                    >
                      {scope.label}
                    </Label>
                    <p className="text-xs text-gray-500 mt-0.5">{scope.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected scopes summary */}
            {scopes.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {scopes.map((scope) => (
                  <Badge key={scope} variant="secondary" className="text-xs">
                    {scope}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Warning */}
          <Card className="p-3 border-cyber-secondary/30 bg-cyber-secondary/5">
            <div className="flex gap-2">
              <AlertCircle className="w-4 h-4 text-cyber-secondary flex-shrink-0 mt-0.5" />
              <p className="text-xs text-gray-400">
                Your API key will be displayed only once. Make sure to copy and store it securely.
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
              disabled={!name.trim() || scopes.length === 0}
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
