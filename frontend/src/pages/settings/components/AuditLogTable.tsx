import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/utils/cn';
import { AuditLog } from '@/api/audit-logs';

interface AuditLogTableProps {
  logs: AuditLog[];
}

export const AuditLogTable = ({ logs }: AuditLogTableProps) => {
  const getActionLabel = (action: string) => {
    return action.replace(/\./g, ' ').replace(/_/g, ' ');
  };

  const getActionColor = (action: string) => {
    if (action.includes('create')) return 'text-cyber-primary';
    if (action.includes('delete') || action.includes('revoke') || action.includes('failed')) return 'text-cyber-accent';
    if (action.includes('update')) return 'text-cyber-secondary';
    return 'text-gray-300';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatTimestamp(timestamp);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-void-700/50 bg-void-900/30">
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Timestamp
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Action
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Resource
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              User
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              IP Address
            </th>
            <th className="text-left py-3 px-4 font-mono text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr
              key={log.id}
              className={cn(
                'border-b border-void-700/30 transition-colors',
                'hover:bg-void-800/30'
              )}
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-gray-500" />
                  <div>
                    <div className="text-sm text-gray-300">{formatTimestamp(log.created_at)}</div>
                    <div className="text-xs text-gray-500">{getRelativeTime(log.created_at)}</div>
                  </div>
                </div>
              </td>
              <td className="py-3 px-4">
                <span className={cn(
                  'text-sm font-medium',
                  getActionColor(log.action)
                )}>
                  {getActionLabel(log.action)}
                </span>
              </td>
              <td className="py-3 px-4">
                <div className="flex flex-col">
                  <span className="text-sm text-gray-300">
                    {log.resource_type || '-'}
                  </span>
                  {log.resource_id && (
                    <span className="text-xs text-gray-500 font-mono">
                      {log.resource_id.slice(0, 8)}...
                    </span>
                  )}
                </div>
              </td>
              <td className="py-3 px-4">
                <span className="text-sm text-gray-300">
                  {log.user_id ? (
                    <span className="font-mono text-xs">
                      {log.user_id.slice(0, 8)}...
                    </span>
                  ) : (
                    <span className="text-gray-500">System</span>
                  )}
                </span>
              </td>
              <td className="py-3 px-4">
                <span className="font-mono text-sm text-gray-400">
                  {log.ip_address || '-'}
                </span>
              </td>
              <td className="py-3 px-4">
                {log.status === 'success' ? (
                  <Badge variant="success" className="text-xs bg-green-500/10 border-green-500/30 text-green-400">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Success
                  </Badge>
                ) : (
                  <Badge variant="danger" className="text-xs">
                    <XCircle className="w-3 h-3 mr-1" />
                    {log.status}
                  </Badge>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
