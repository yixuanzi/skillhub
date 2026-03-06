import { Filter, X, Calendar } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { cn } from '@/utils/cn';

interface FilterOption {
  value: string;
  label: string;
}

interface AuditLogFiltersProps {
  filters: {
    page: number;
    size: number;
    action?: string;
    resource_type?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
  };
  onFilterChange: (filters: Partial<{
    action?: string;
    resource_type?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
  }>) => void;
  actionOptions: FilterOption[];
  resourceTypeOptions: FilterOption[];
}

export const AuditLogFilters = ({
  filters,
  onFilterChange,
  actionOptions,
  resourceTypeOptions,
}: AuditLogFiltersProps) => {
  const hasActiveFilters =
    filters.action ||
    filters.resource_type ||
    filters.user_id ||
    filters.start_date ||
    filters.end_date;

  const handleClearAll = () => {
    onFilterChange({
      action: '',
      resource_type: '',
      user_id: '',
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Action Filter */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Action
          </label>
          <select
            value={filters.action || ''}
            onChange={(e) => onFilterChange({ action: e.target.value || undefined })}
            className={cn(
              'w-full px-3 py-2 font-mono text-sm rounded-lg border transition-all duration-200',
              'bg-void-900/50 border-void-700 text-gray-100',
              'focus:outline-none focus:border-cyber-primary'
            )}
          >
            {actionOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Resource Type Filter */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            Resource Type
          </label>
          <select
            value={filters.resource_type || ''}
            onChange={(e) => onFilterChange({ resource_type: e.target.value || undefined })}
            className={cn(
              'w-full px-3 py-2 font-mono text-sm rounded-lg border transition-all duration-200',
              'bg-void-900/50 border-void-700 text-gray-100',
              'focus:outline-none focus:border-cyber-primary'
            )}
          >
            {resourceTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Start Date Filter */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            From
          </label>
          <div className="relative">
            <Input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => onFilterChange({ start_date: e.target.value || undefined })}
              className="pl-10"
            />
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          </div>
        </div>

        {/* End Date Filter */}
        <div>
          <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
            To
          </label>
          <div className="relative">
            <Input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => onFilterChange({ end_date: e.target.value || undefined })}
              className="pl-10"
            />
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* User ID Filter */}
      <div>
        <label className="block text-xs font-mono text-gray-500 mb-1.5 uppercase">
          User ID
        </label>
        <Input
          type="text"
          value={filters.user_id || ''}
          onChange={(e) => onFilterChange({ user_id: e.target.value || undefined })}
          placeholder="Enter user ID to filter..."
          className="font-mono text-sm"
        />
      </div>
    </div>
  );
};
