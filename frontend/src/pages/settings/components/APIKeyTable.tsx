import { Trash2, RefreshCw, Calendar, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';
import { APIKey } from '@/api/api-keys';

interface APIKeyTableProps {
  apiKeys: APIKey[];
  onRevoke: (id: string) => void;
  onRotate: (id: string) => void;
  deleteConfirm: string | null;
}

export const APIKeyTable = ({ apiKeys, onRevoke, onRotate, deleteConfirm }: APIKeyTableProps) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getRelativeTime = (dateString: string | null) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  const isExpiringSoon = (expiresAt: string | null) => {
    if (!expiresAt) return false;
    const expiryDate = new Date(expiresAt);
    const now = new Date();
    const diffDays = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays > 0 && diffDays <= 7;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-void-700/50">
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Key Prefix
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Scopes
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Expires
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Last Used
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="text-right py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {apiKeys.map((key) => {
            const isDeleting = deleteConfirm === key.id;
            const expiringSoon = isExpiringSoon(key.expires_at);

            return (
              <tr
                key={key.id}
                className={cn(
                  'border-b border-void-700/30 transition-colors',
                  !key.is_active && 'opacity-60'
                )}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-100">{key.name}</span>
                    {expiringSoon && (
                      <Badge variant="danger" className="text-xs">Expiring Soon</Badge>
                    )}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <code className="font-mono text-sm text-gray-400 bg-void-900/50 px-2 py-1 rounded">
                    {key.key_prefix}••••••••
                  </code>
                </td>
                <td className="py-3 px-4">
                  <div className="flex gap-1 flex-wrap">
                    {key.scopes.map((scope) => (
                      <Badge key={scope} variant="secondary" className="text-xs">
                        {scope}
                      </Badge>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-3.5 h-3.5 text-gray-500" />
                    <span className={cn(
                      'text-gray-400',
                      expiringSoon && 'text-cyber-accent'
                    )}>
                      {formatDate(key.expires_at)}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="w-3.5 h-3.5 text-gray-500" />
                    <span className="text-gray-400">
                      {getRelativeTime(key.last_used_at) || formatDate(key.last_used_at)}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <Badge
                    variant={key.is_active ? 'success' : 'secondary'}
                    className={cn(
                      'text-xs',
                      key.is_active && 'bg-cyber-primary/10 border-cyber-primary/30'
                    )}
                  >
                    {key.is_active ? 'Active' : 'Revoked'}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center justify-end gap-2">
                    {key.is_active && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRotate(key.id)}
                          title="Rotate key"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                        <Button
                          variant={isDeleting ? 'danger' : 'ghost'}
                          size="sm"
                          onClick={() => onRevoke(key.id)}
                          title={isDeleting ? 'Confirm revoke' : 'Revoke key'}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
