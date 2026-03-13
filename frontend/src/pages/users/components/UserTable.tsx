import React from 'react';
import { Shield, ChevronLeft, ChevronRight } from 'lucide-react';
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

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  roles: Array<{ id: string; name: string }>;
  created_at: string;
}

interface Props {
  users: User[];
  total: number;
  page: number;
  size: number;
  onPageChange: (page: number) => void;
  onManageRoles: (user: User) => void;
}

export const UserTable: React.FC<Props> = ({
  users,
  total,
  page,
  size,
  onPageChange,
  onManageRoles
}) => {
  const totalPages = Math.ceil(total / size);

  // Loading state
  if (users.length === 0 && total > 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-void-700 border-t-cyber-primary rounded-full animate-spin" />
          </div>
          <p className="text-sm text-gray-400 font-mono">Loading users...</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-16 h-16 rounded-full bg-void-800 border border-void-600 flex items-center justify-center mb-4">
          <Shield className="w-8 h-8 text-gray-500" />
        </div>
        <h3 className="text-lg font-mono font-semibold text-gray-300 mb-2">No Users Found</h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          No users match your current filters. Try adjusting your search or filter criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="border border-void-700 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Roles</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-32">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-cyber-primary/10 flex items-center justify-center">
                      <span className="text-xs font-mono font-medium text-cyber-primary">
                        {user.username.slice(0, 2).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-200">{user.username}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </div>
                </TableCell>

                <TableCell>
                  <div className="flex gap-1 flex-wrap">
                    {user.roles.map((role) => (
                      <Badge key={role.id} variant="secondary" className="text-xs">
                        {role.name}
                      </Badge>
                    ))}
                    {user.roles.length === 0 && (
                      <span className="text-sm text-gray-600">No roles</span>
                    )}
                  </div>
                </TableCell>

                <TableCell>
                  <Badge
                    variant={user.is_active ? 'success' : 'secondary'}
                    className={cn(
                      user.is_active ? 'bg-cyber-primary/10 text-cyber-primary border-cyber-primary/30' : ''
                    )}
                  >
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </TableCell>

                <TableCell className="text-sm">
                  <span className="text-gray-500 font-mono">
                    {formatRelativeTime(user.created_at)}
                  </span>
                </TableCell>

                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onManageRoles(user)}
                    className="p-1.5"
                  >
                    <Shield className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="p-1.5"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-gray-500 font-mono px-2">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className="p-1.5"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}
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
