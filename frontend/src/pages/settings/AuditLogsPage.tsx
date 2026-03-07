import { useState } from 'react';
import { AlertCircle, FileText, Download } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useAuditLogs } from '@/hooks/use-audit-logs';
import { AuditLogTable } from './components/AuditLogTable';
import { AuditLogFilters } from './components/AuditLogFilters';
import { AuditLogDetailModal } from './components/AuditLogDetailModal';
import { cn } from '@/utils/cn';
import { AuditLog } from '@/api/audit-logs';

interface Filters {
  page: number;
  size: number;
  action?: string;
  resource_type?: string;
  user_id?: string;
  start_date?: string;
  end_date?: string;
}

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'login', label: 'Login' },
  { value: 'logout', label: 'Logout' },
  { value: 'login_failed', label: 'Login Failed' },
  { value: 'resource.create', label: 'Resource Create' },
  { value: 'resource.update', label: 'Resource Update' },
  { value: 'resource.delete', label: 'Resource Delete' },
  { value: 'resource.read', label: 'Resource Read' },
  { value: 'skill.call', label: 'Skill Call' },
  { value: 'skill.create', label: 'Skill Create' },
  { value: 'acl.create', label: 'ACL Create' },
  { value: 'api_key.create', label: 'API Key Create' },
  { value: 'api_key.delete', label: 'API Key Delete' },
];

const RESOURCE_TYPE_OPTIONS = [
  { value: '', label: 'All Resources' },
  { value: 'resource', label: 'Resource' },
  { value: 'skill', label: 'Skill' },
  { value: 'user', label: 'User' },
  { value: 'acl', label: 'ACL' },
  { value: 'api_key', label: 'API Key' },
];

export const AuditLogsPage = () => {
  const [filters, setFilters] = useState<Filters>({
    page: 1,
    size: 20,
    action: '',
    resource_type: '',
  });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const { data: logsData, isLoading, error, refetch } = useAuditLogs(filters);

  const logs = logsData?.items || [];
  const total = logsData?.total || 0;
  const totalPages = Math.ceil(total / filters.size);

  const handleFilterChange = (newFilters: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleExport = () => {
    // Export functionality - can be implemented later
    console.log('Exporting audit logs...');
  };

  const handleDetailClick = (log: AuditLog) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const handleCloseDetailModal = () => {
    setIsDetailModalOpen(false);
    setSelectedLog(null);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-gray-100">Audit Logs</h2>
          <p className="font-mono text-sm text-gray-500">
            View all access attempts and security events
          </p>
        </div>
        <button
          onClick={handleExport}
          className="inline-flex items-center gap-2 px-4 py-2 font-mono text-sm rounded-lg border border-void-700 text-gray-400 hover:text-gray-200 hover:bg-void-800 transition-all duration-200"
        >
          <Download className="w-4 h-4" />
          Export Logs
        </button>
      </div>

      {/* Filters */}
      <AuditLogFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        actionOptions={ACTION_OPTIONS}
        resourceTypeOptions={RESOURCE_TYPE_OPTIONS}
      />

      {/* Results Info */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 font-mono">
          Showing {logs.length > 0 ? ((filters.page - 1) * filters.size) + 1 : 0}-
          {Math.min(filters.page * filters.size, total)} of {total} logs
        </p>
        {total > filters.size && (
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (filters.page <= 3) {
                pageNum = i + 1;
              } else if (filters.page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = filters.page - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={cn(
                    'w-8 h-8 font-mono text-xs rounded transition-all duration-200',
                    filters.page === pageNum
                      ? 'bg-cyber-primary/10 border border-cyber-primary text-cyber-primary'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-void-800'
                  )}
                >
                  {pageNum}
                </button>
              );
            })}
            {totalPages > 5 && filters.page < totalPages - 2 && (
              <>
                <span className="text-gray-600 px-1">...</span>
                <button
                  onClick={() => handlePageChange(totalPages)}
                  className="w-8 h-8 font-mono text-xs rounded text-gray-500 hover:text-gray-300 hover:bg-void-800 transition-all duration-200"
                >
                  {totalPages}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Logs Table */}
      <Card className="p-0 overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-2 border-cyber-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 font-mono text-sm mt-4">Loading audit logs...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-cyber-accent mx-auto mb-4" />
            <p className="text-gray-500 font-mono text-sm mb-2">Failed to load audit logs</p>
            <button
              onClick={() => refetch()}
              className="text-cyber-primary hover:text-cyber-primary/80 text-sm font-mono"
            >
              Try Again
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono text-sm mb-2">No audit logs found</p>
            <p className="text-xs text-gray-600">
              {filters.action || filters.resource_type
                ? 'Try adjusting your filters'
                : 'Logs will appear here once users interact with the system'}
            </p>
          </div>
        ) : (
          <AuditLogTable logs={logs} onDetailClick={handleDetailClick} />
        )}
      </Card>

      {/* Detail Modal */}
      <AuditLogDetailModal
        isOpen={isDetailModalOpen}
        onClose={handleCloseDetailModal}
        log={selectedLog}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500 font-mono">
            Page {filters.page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(filters.page - 1)}
              disabled={filters.page === 1}
              className={cn(
                'px-3 py-1.5 font-mono text-sm rounded-lg border transition-all duration-200',
                filters.page === 1
                  ? 'border-void-700/50 text-gray-600 cursor-not-allowed'
                  : 'border-void-700 text-gray-400 hover:text-gray-200 hover:bg-void-800'
              )}
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(filters.page + 1)}
              disabled={filters.page === totalPages}
              className={cn(
                'px-3 py-1.5 font-mono text-sm rounded-lg border transition-all duration-200',
                filters.page === totalPages
                  ? 'border-void-700/50 text-gray-600 cursor-not-allowed'
                  : 'border-void-700 text-gray-400 hover:text-gray-200 hover:bg-void-800'
              )}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogsPage;
