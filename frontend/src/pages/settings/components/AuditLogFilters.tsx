import { Filter, X, Calendar } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

const selectCls = cn(
  'w-full px-3 py-2 font-mono text-sm rounded-lg border transition-all duration-200',
  'bg-void-900/50 border-void-700 text-gray-100',
  'focus:outline-none focus:border-cyber-primary'
);

const dateCls = '[color-scheme:dark]';

interface AuditLogFiltersProps {
  filters: {
    page: number;
    size: number;
    action?: string;
    resource_type?: string;
    resource_id?: string;
    user_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  };
  onFilterChange: (filters: Partial<{
    action?: string;
    resource_type?: string;
    resource_id?: string;
    user_id?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }>) => void;
  resourceTypes?: string[];
}

export const AuditLogFilters = ({
  filters,
  onFilterChange,
  resourceTypes = [],
}: AuditLogFiltersProps) => {
  const hasActiveFilters =
    filters.action ||
    filters.resource_type ||
    filters.resource_id ||
    filters.user_id ||
    filters.status ||
    filters.start_date ||
    filters.end_date;

  const handleClearAll = () => {
    onFilterChange({
      action: '',
      resource_type: '',
      resource_id: '',
      user_id: '',
      status: '',
      start_date: '',
      end_date: '',
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-400">
          <Filter className="w-4 h-4" />
          <span className="text-sm font-mono">Filters</span>
          {hasActiveFilters && (
            <span className="px-2 py-0.5 text-xs rounded bg-cyber-primary/20 text-cyber-primary">
              Active
            </span>
          )}
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="text-cyber-accent hover:text-cyber-accent/80"
          >
            <X className="w-4 h-4 mr-1" />
            Clear All
          </Button>
        )}
      </div>

      {/* Row 1: User ID · Resource Type · Status · From · To */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* User ID / Username */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            User ID / Username
          </label>
          <Input
            type="text"
            value={filters.user_id || ''}
            onChange={(e) => onFilterChange({ user_id: e.target.value || undefined })}
            placeholder="ID or username..."
            className="font-mono text-sm"
          />
        </div>

        {/* Resource Type — dynamic dropdown */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Resource Type
          </label>
          <select
            value={filters.resource_type || ''}
            onChange={(e) => onFilterChange({ resource_type: e.target.value || undefined })}
            className={selectCls}
          >
            <option value="">All Types</option>
            {resourceTypes.map((rt) => (
              <option key={rt} value={rt}>{rt}</option>
            ))}
          </select>
        </div>

        {/* Status — fixed dropdown */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Status
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => onFilterChange({ status: e.target.value || undefined })}
            className={selectCls}
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>

        {/* From date */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            From
          </label>
          <div className="relative">
            <Input
              type="datetime-local"
              value={filters.start_date || ''}
              onChange={(e) => onFilterChange({ start_date: e.target.value || undefined })}
              className={cn('pl-10', dateCls)}
            />
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          </div>
        </div>

        {/* To date */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            To
          </label>
          <div className="relative">
            <Input
              type="datetime-local"
              value={filters.end_date || ''}
              onChange={(e) => onFilterChange({ end_date: e.target.value || undefined })}
              className={cn('pl-10', dateCls)}
            />
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Row 2: Action (long) · Resource ID (short) */}
      <div className="grid grid-cols-3 gap-4">
        {/* Action — fuzzy search, takes 2/3 width */}
        <div className="col-span-2">
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Action
          </label>
          <Input
            type="text"
            value={filters.action || ''}
            onChange={(e) => onFilterChange({ action: e.target.value || undefined })}
            placeholder="Search action, e.g. post /api/v1/skills..."
            className="font-mono text-sm"
          />
        </div>

        {/* Resource ID — exact match, takes 1/3 width */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Resource ID
          </label>
          <Input
            type="text"
            value={filters.resource_id || ''}
            onChange={(e) => onFilterChange({ resource_id: e.target.value || undefined })}
            placeholder="Resource ID..."
            className="font-mono text-sm"
          />
          <p className="mt-1 text-xs text-gray-600 font-mono">
            Filter gateway / resource call logs
          </p>
        </div>
      </div>
    </div>
  );
};
