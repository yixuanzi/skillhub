import { ACLRule, AccessMode } from '@/types';
import { Pencil, Trash2, Shield, Unlock, Lock, Clock, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table';
import { cn } from '@/utils/cn';

interface ACLResourceTableProps {
  rules: ACLRule[];
  loading?: boolean;
  onEdit?: (rule: ACLRule) => void;
  onDelete?: (rule: ACLRule) => void;
  deleteConfirm?: ACLRule | null;
}

// Access mode badge variant mapping
const getAccessModeBadgeVariant = (mode: AccessMode): 'success' | 'info' => {
  return mode === 'any' ? 'success' : 'info';
};

export const ACLResourceTable = ({
  rules,
  loading,
  onEdit,
  onDelete,
  deleteConfirm,
}: ACLResourceTableProps) => {
  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-void-700 border-t-cyber-primary rounded-full animate-spin" />
          </div>
          <p className="text-sm text-gray-400 font-mono">Loading ACL rules...</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (rules.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-16 h-16 rounded-full bg-void-800 border border-void-600 flex items-center justify-center mb-4">
          <Shield className="w-8 h-8 text-gray-500" />
        </div>
        <h3 className="text-lg font-mono font-semibold text-gray-300 mb-2">No ACL Rules Found</h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          ACL rules control access to your resources. Create your first rule to secure a resource.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-void-700 rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Resource</TableHead>
            <TableHead>Access Mode</TableHead>
            <TableHead>Conditions</TableHead>
            <TableHead>Role Bindings</TableHead>
            <TableHead>Created</TableHead>
            {(onEdit || onDelete) && <TableHead className="w-32">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rules.map((rule, index) => (
            <TableRow
              key={rule.id}
              className="animate-slide-in"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <TableCell>
                <div className="flex flex-col gap-1">
                  <code className="text-sm font-mono text-cyber-primary">
                    {rule.resource_name}
                  </code>
                  <code className="text-xs font-mono text-gray-600">
                    {rule.resource_id}
                  </code>
                </div>
              </TableCell>
              <TableCell>
                <Badge
                  variant={getAccessModeBadgeVariant(rule.access_mode)}
                  className={cn(
                    'text-xs font-mono uppercase tracking-wider',
                    rule.access_mode === 'any' && 'gap-1.5'
                  )}
                >
                  {rule.access_mode === 'any' ? (
                    <>
                      <Unlock className="w-3 h-3" />
                      Public
                    </>
                  ) : (
                    <>
                      <Lock className="w-3 h-3" />
                      RBAC
                    </>
                  )}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="space-y-1.5">
                  {rule.conditions?.rate_limit && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span className="font-mono">
                        {rule.conditions.rate_limit.requests}/
                        {rule.conditions.rate_limit.window}s
                      </span>
                    </div>
                  )}
                  {rule.conditions?.ip_whitelist && rule.conditions.ip_whitelist.length > 0 && (
                    <div className="text-xs text-gray-400">
                      <span className="font-mono">
                        {rule.conditions.ip_whitelist.length} IP(s)
                      </span>
                    </div>
                  )}
                  {rule.conditions?.time_windows && rule.conditions.time_windows.length > 0 && (
                    <div className="text-xs text-gray-400">
                      <span className="font-mono">
                        {rule.conditions.time_windows.length} time window(s)
                      </span>
                    </div>
                  )}
                  {rule.conditions?.roles && rule.conditions.roles.length > 0 && (
                    <div className="text-xs text-gray-400">
                      <span className="font-mono">
                        {rule.conditions.roles.length} role(s)
                      </span>
                    </div>
                  )}
                  {!rule.conditions?.rate_limit &&
                    !rule.conditions?.ip_whitelist &&
                    !rule.conditions?.time_windows &&
                    !rule.conditions?.roles && (
                      <span className="text-xs text-gray-600 font-mono">No conditions</span>
                    )}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {rule.role_bindings && rule.role_bindings.length > 0 ? (
                    rule.role_bindings.map((binding) => (
                      <span
                        key={binding.id}
                        className="px-2 py-0.5 text-xs font-mono rounded bg-void-800 text-gray-300 border border-void-600"
                        title={`Permissions: ${binding.permissions.join(', ')}`}
                      >
                        {binding.role_name || binding.role_id}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-600 font-mono">—</span>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <span className="text-xs text-gray-500 font-mono">
                  {formatRelativeTime(rule.created_at)}
                </span>
              </TableCell>
              {(onEdit || onDelete) && (
                <TableCell>
                  <div className="flex items-center gap-2">
                    {onEdit && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(rule)}
                        className="p-1.5"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                    )}
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(rule)}
                        className={cn(
                          'p-1.5 transition-all duration-200',
                          deleteConfirm?.id === rule.id
                            ? 'bg-cyber-accent/20 border border-cyber-accent text-cyber-accent animate-pulse'
                            : 'text-cyber-accent hover:text-cyber-accent'
                        )}
                      >
                        {deleteConfirm?.id === rule.id ? (
                          <AlertTriangle className="w-4 h-4" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

// Helper function for relative time formatting
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 604800)}w ago`;
  if (seconds < 31536000) return `${Math.floor(seconds / 2592000)}mo ago`;
  return `${Math.floor(seconds / 31536000)}y ago`;
}
