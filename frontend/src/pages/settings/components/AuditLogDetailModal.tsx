import { Clock, CheckCircle, XCircle, FileText } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { AuditLog } from '@/api/audit-logs';
import { cn } from '@/utils/cn';

interface AuditLogDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  log: AuditLog | null;
}

const toUTCDate = (ts: string) => new Date(/[Z+]/.test(ts) ? ts : ts + 'Z');

const formatTimestamp = (timestamp: string) =>
  toUTCDate(timestamp).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: 'numeric',
  });

const getActionColor = (action: string) => {
  if (action.includes('create')) return 'text-cyber-primary';
  if (action.includes('delete') || action.includes('revoke') || action.includes('failed')) return 'text-cyber-accent';
  if (action.includes('update')) return 'text-cyber-secondary';
  return 'text-gray-300';
};

const Row = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="flex items-start gap-3 py-1.5 border-b border-void-700/40 last:border-0">
    <span className="w-28 shrink-0 text-xs font-mono text-gray-500 uppercase pt-0.5">{label}</span>
    <span className="flex-1 min-w-0">{children}</span>
  </div>
);

export const AuditLogDetailModal = ({ isOpen, onClose, log }: AuditLogDetailModalProps) => {
  if (!log) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Audit Log Details">
      <div className="space-y-4 text-sm">
        {/* Meta row: status + id + timestamp */}
        <div className="flex items-center gap-3 flex-wrap">
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
          <span className="text-xs text-gray-500 font-mono">#{log.id.slice(0, 8)}</span>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatTimestamp(log.created_at)}
          </span>
        </div>

        {/* Core fields */}
        <div className="bg-void-900/50 rounded-lg px-3 py-1 border border-void-700">
          <Row label="Action">
            <span className={cn('font-mono font-medium break-all', getActionColor(log.action))}>
              {log.action}
            </span>
          </Row>
          <Row label="User">
            {log.username
              ? <span className="font-mono text-gray-200">{log.username}</span>
              : <span className="text-gray-500">—</span>}
          </Row>
          {log.resource_type && (
            <Row label="Resource Type">
              <span className="font-mono text-gray-300">{log.resource_type}</span>
            </Row>
          )}
          {log.resource_id && (
            <Row label="Resource ID">
              <span className="font-mono text-gray-300 break-all">{log.resource_id}</span>
            </Row>
          )}
          {log.ip_address && (
            <Row label="IP">
              <span className="font-mono text-gray-400">{log.ip_address}</span>
            </Row>
          )}
          {log.user_agent && (
            <Row label="User Agent">
              <span className="text-gray-500 text-xs break-all">{log.user_agent}</span>
            </Row>
          )}
          {log.error_message && (
            <Row label="Error">
              <span className="text-cyber-accent">{log.error_message}</span>
            </Row>
          )}
        </div>

        {/* Details — formatted JSON */}
        {log.details && Object.keys(log.details).length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <FileText className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Details</span>
            </div>
            <pre className="bg-void-950 border border-void-700 rounded-lg px-3 py-2.5 text-xs font-mono text-gray-300 overflow-auto max-h-64 leading-relaxed">
              {JSON.stringify(log.details, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </Modal>
  );
};
