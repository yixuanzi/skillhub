import { Clock, User, Server, Globe, CheckCircle, XCircle, AlertCircle, FileText } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { AuditLog } from '@/api/audit-logs';
import { cn } from '@/utils/cn';

interface AuditLogDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  log: AuditLog | null;
}

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: 'numeric',
  });
};

const getActionLabel = (action: string) => {
  return action.replace(/\./g, ' ').replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
};

const getActionColor = (action: string) => {
  if (action.includes('create')) return 'text-cyber-primary';
  if (action.includes('delete') || action.includes('revoke') || action.includes('failed')) return 'text-cyber-accent';
  if (action.includes('update')) return 'text-cyber-secondary';
  return 'text-gray-300';
};

export const AuditLogDetailModal = ({ isOpen, onClose, log }: AuditLogDetailModalProps) => {
  if (!log) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Audit Log Details">
      <div className="space-y-6">
        {/* Status Badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {log.status === 'success' ? (
              <Badge variant="success" className="text-sm bg-green-500/10 border-green-500/30 text-green-400">
                <CheckCircle className="w-4 h-4 mr-1.5" />
                Success
              </Badge>
            ) : (
              <Badge variant="danger" className="text-sm">
                <XCircle className="w-4 h-4 mr-1.5" />
                {log.status}
              </Badge>
            )}
          </div>
          <span className="text-xs text-gray-500 font-mono">ID: {log.id.slice(0, 8)}...</span>
        </div>

        {/* Action */}
        <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Action</span>
          </div>
          <p className={cn('text-lg font-semibold', getActionColor(log.action))}>
            {getActionLabel(log.action)}
          </p>
        </div>

        {/* Timestamp */}
        <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Timestamp</span>
          </div>
          <p className="text-gray-300">{formatTimestamp(log.created_at)}</p>
        </div>

        {/* User Information */}
        <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">User</span>
          </div>
          <p className="text-gray-300">
            {log.username ? (
              <span className="font-mono text-sm bg-void-800 px-2 py-1 rounded">
                {log.username}
              </span>
            ) : (
              <span className="text-gray-500">System</span>
            )}
          </p>
        </div>

        {/* Resource Information */}
        {(log.resource_type || log.resource_id) && (
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-2">
              <Server className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Resource</span>
            </div>
            <div className="space-y-2">
              {log.resource_type && (
                <div>
                  <span className="text-xs text-gray-500 block mb-1">Type</span>
                  <span className="text-gray-300 font-mono text-sm">{log.resource_type}</span>
                </div>
              )}
              {log.resource_id && (
                <div>
                  <span className="text-xs text-gray-500 block mb-1">ID</span>
                  <span className="text-gray-300 font-mono text-sm bg-void-800 px-2 py-1 rounded block w-fit">
                    {log.resource_id}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Network Information */}
        <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Network</span>
          </div>
          <div className="space-y-2">
            {log.ip_address && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">IP Address</span>
                <span className="text-gray-300 font-mono text-sm">{log.ip_address}</span>
              </div>
            )}
            {log.user_agent && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">User Agent</span>
                <span className="text-gray-400 text-xs break-all">{log.user_agent}</span>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {log.error_message && (
          <div className="bg-red-500/5 rounded-lg p-4 border border-red-500/30">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-4 h-4 text-cyber-accent" />
              <span className="text-xs font-mono text-cyber-accent uppercase tracking-wider">Error</span>
            </div>
            <p className="text-cyber-accent text-sm">{log.error_message}</p>
          </div>
        )}

        {/* Additional Details */}
        {log.details && Object.keys(log.details).length > 0 && (
          <div className="bg-void-900/50 rounded-lg p-4 border border-void-700">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Additional Details</span>
            </div>
            <div className="space-y-2">
              {Object.entries(log.details).map(([key, value]) => (
                <div key={key} className="border-b border-void-700/50 pb-2 last:border-0 last:pb-0">
                  <span className="text-xs text-gray-500 block mb-1 font-mono">{key}</span>
                  <span className="text-gray-300 text-sm break-all">
                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
