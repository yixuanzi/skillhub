import { Card } from '@/components/ui';
import { Users, Shield, Wrench } from 'lucide-react';

export const UsersPage = () => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Users & Roles
          </h1>
          <p className="font-mono text-sm text-gray-500">
            User and role management
          </p>
        </div>
      </div>

      {/* Feature Coming Soon */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Users Section */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-cyber-primary/10">
                  <Users className="w-6 h-6 text-cyber-primary" />
                </div>
                <div>
                  <h2 className="font-display text-lg font-semibold text-gray-100">
                    Users Management
                  </h2>
                  <p className="text-xs text-gray-500 font-mono">
                    Create and manage user accounts
                  </p>
                </div>
              </div>
            </div>

            <div className="text-center py-12">
              <Wrench className="w-16 h-16 text-gray-700 mx-auto mb-4" />
              <h3 className="font-display text-xl text-gray-300 mb-2">
                Feature Coming Soon
              </h3>
              <p className="text-gray-500 font-mono text-sm max-w-md mx-auto">
                User management functionality is under development.
                This will include user creation, role assignment, and permission management.
              </p>
            </div>
          </Card>
        </div>

        {/* Roles Section */}
        <div>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-lg bg-cyber-secondary/10">
                  <Shield className="w-5 h-5 text-cyber-secondary" />
                </div>
                <div>
                  <h2 className="font-display text-lg font-semibold text-gray-100">
                    Roles
                  </h2>
                  <p className="text-xs text-gray-500 font-mono">
                    Access control
                  </p>
                </div>
              </div>
            </div>

            <div className="text-center py-8">
              <Wrench className="w-12 h-12 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 font-mono text-sm">
                Role management coming soon
              </p>
            </div>
          </Card>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-primary/10">
              <Users className="w-5 h-5 text-cyber-primary" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">User Management</h3>
              <p className="text-xs text-gray-500">Create, update, and delete user accounts</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-secondary/10">
              <Shield className="w-5 h-5 text-cyber-secondary" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">Role Assignment</h3>
              <p className="text-xs text-gray-500">Assign roles to control access</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyber-warning/10">
              <Wrench className="w-5 h-5 text-cyber-warning" />
            </div>
            <div>
              <h3 className="font-mono text-sm text-gray-200 mb-1">Permissions</h3>
              <p className="text-xs text-gray-500">Fine-grained access control</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
