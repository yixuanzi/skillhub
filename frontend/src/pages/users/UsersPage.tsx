import { useUsers, useRoles } from '@/hooks/useUsers';
import { Card, Badge, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, Loading } from '@/components/ui';
import { UserPlus, Shield } from 'lucide-react';
import { formatRelativeTime } from '@/utils/date';

export const UsersPage = () => {
  const { data: usersData, isLoading } = useUsers();
  const { data: rolesData } = useRoles();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  const users = usersData?.data?.items || [];
  const roles = rolesData?.data || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Users & Roles
          </h1>
          <p className="font-mono text-sm text-gray-500">
            {users.length} users • {roles.length} roles
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-cyber-primary/10 border border-cyber-primary text-cyber-primary rounded-lg font-mono text-sm hover:bg-cyber-primary/20 transition-all">
          <UserPlus className="w-4 h-4" />
          Add User
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Users List */}
        <div className="lg:col-span-2">
          <Card>
            <h2 className="font-display text-lg font-semibold text-gray-100 mb-4">
              Users
            </h2>
            {users.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No users found</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Roles</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user, index) => (
                    <TableRow
                      key={user.id}
                      className="animate-slide-in"
                      style={{ animationDelay: `${index * 0.05}s` }}
                    >
                      <TableCell>
                        <div>
                          <p className="font-mono text-sm text-gray-200">{user.username}</p>
                          <p className="text-xs text-gray-500">{user.email}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 flex-wrap">
                          {user.roles.map((role) => (
                            <Badge key={role.id} variant="info" className="text-xs">
                              {role.name}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-500">
                          {formatRelativeTime(user.createdAt)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <button className="text-cyber-primary hover:text-cyber-secondary text-sm font-mono">
                          Edit
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </div>

        {/* Roles List */}
        <div>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-gray-100">
                Roles
              </h2>
              <Shield className="w-5 h-5 text-cyber-secondary" />
            </div>
            <div className="space-y-2">
              {roles.map((role) => (
                <div
                  key={role.id}
                  className="p-3 rounded-lg bg-void-900/50 border border-void-700 hover:border-void-600 transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-mono text-sm text-gray-200">{role.name}</p>
                    <Badge variant="info" className="text-xs">
                      {role.permissions.length} perms
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500">
                    {role.permissions.slice(0, 2).map((p) => p.resource).join(', ')}
                    {role.permissions.length > 2 && '...'}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
