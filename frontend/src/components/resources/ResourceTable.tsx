import { Resource } from '@/types';
import { Pencil, Trash2, ExternalLink, Globe, Lock, FileText } from 'lucide-react';
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

interface ResourceTableProps {
  resources: Resource[];
  loading?: boolean;
  onEdit?: (resource: Resource) => void;
  onDelete?: (resource: Resource) => void;
  deleteConfirm?: Resource | null;
}

// Type badge color mapping
const getTypeBadgeVariant = (type: Resource['type']): 'info' | 'warning' | 'success' | 'default' => {
  switch (type) {
    case 'gateway':
      return 'warning';
    case 'third':
      return 'success';
    case 'mcp':
      return 'default';
    default:
      return 'info';
  }
};

// View scope badge component
const ViewScopeBadge: React.FC<{ scope: 'public' | 'private' }> = ({ scope }) => {
  if (scope === 'public') {
    return (
      <Badge variant="outline" className="border-cyber-primary/30 text-cyber-primary">
        <Globe className="w-3 h-3 mr-1" />
        Public
      </Badge>
    );
  }
  return (
    <Badge variant="secondary" className="bg-void-800 border-void-600">
      <Lock className="w-3 h-3 mr-1" />
      Private
    </Badge>
  );
};

export const ResourceTable = ({ resources, loading, onEdit, onDelete, deleteConfirm }: ResourceTableProps) => {
  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-void-700 border-t-cyber-primary rounded-full animate-spin" />
          </div>
          <p className="text-sm text-gray-400 font-mono">Loading resources...</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (resources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-16 h-16 rounded-full bg-void-800 border border-void-600 flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <h3 className="text-lg font-mono font-semibold text-gray-300 mb-2">No Resources Found</h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          Get started by creating your first resource. Resources can be MCP servers, gateway endpoints, or third-party integrations.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-void-700 rounded-lg overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Visibility</TableHead>
            <TableHead>URL</TableHead>
            <TableHead>Description</TableHead>
            <TableHead className="w-20">Docs</TableHead>
            <TableHead>Created</TableHead>
            {(onEdit || onDelete) && <TableHead className="w-32">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {resources.map((resource) => (
            <TableRow key={resource.id}>
              <TableCell>
                <span className="font-mono font-medium text-gray-200">{resource.name}</span>
              </TableCell>
              <TableCell>
                <Badge variant={getTypeBadgeVariant(resource.type)}>{resource.type}</Badge>
              </TableCell>
              <TableCell>
                <ViewScopeBadge scope={resource.view_scope || 'public'} />
              </TableCell>
              <TableCell>
                {resource.url ? (
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-cyber-secondary hover:text-cyber-primary transition-colors duration-200"
                  >
                    <span className="text-xs font-mono truncate max-w-[200px]">{resource.url}</span>
                    <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                  </a>
                ) : (
                  <span className="text-gray-600 font-mono text-xs">—</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-sm text-gray-400 line-clamp-2 max-w-xs">
                  {resource.desc || <span className="text-gray-600">No description</span>}
                </span>
              </TableCell>
              <TableCell>
                {resource.api_description ? (
                  <div
                    className="group relative inline-block"
                    title="API documentation available"
                  >
                    <FileText className="w-4 h-4 text-cyber-secondary" />
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                      <div className="bg-void-900 border border-void-700 rounded px-2 py-1 text-xs text-gray-300 whitespace-nowrap max-w-xs">
                        API documentation available
                      </div>
                    </div>
                  </div>
                ) : (
                  <span className="text-gray-600 font-mono text-xs">—</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-xs text-gray-500 font-mono">
                  {formatRelativeTime(resource.created_at)}
                </span>
              </TableCell>
              {(onEdit || onDelete) && (
                <TableCell>
                  <div className="flex items-center gap-2">
                    {onEdit && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(resource)}
                        className="p-1.5"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                    )}
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(resource)}
                        className={cn(
                          'p-1.5 transition-all duration-200',
                          deleteConfirm?.id === resource.id
                            ? 'bg-cyber-accent/20 border border-cyber-accent text-cyber-accent animate-pulse'
                            : 'text-cyber-accent hover:text-cyber-accent'
                        )}
                      >
                        <Trash2 className="w-4 h-4" />
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
