import { useState } from 'react';
import { useACLRules, useAuditLogs } from '@/hooks/useACL';
import { Card, Badge, Table, TableHeader, TableBody, TableRow, TableHead, TableCell, Loading, Button } from '@/components/ui';
import { Shield, Plus, History } from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/date';

export const ACLPage = () => {
  const { data: rulesData, isLoading } = useACLRules();
  const [activeTab, setActiveTab] = useState<'rules' | 'logs'>('rules');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  const rules = rulesData?.data?.items || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Access Control
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Manage ACL rules and audit logs
          </p>
        </div>
        <Button variant="primary">
          <Plus className="w-4 h-4" />
          New Rule
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-void-700">
        <button
          onClick={() => setActiveTab('rules')}
          className={cn(
            'px-4 py-2 font-mono text-sm transition-all border-b-2 -mb-px',
            activeTab === 'rules'
              ? 'text-cyber-primary border-cyber-primary'
              : 'text-gray-500 border-transparent hover:text-gray-300'
          )}
        >
          <Shield className="w-4 h-4 inline mr-2" />
          Rules ({rules.length})
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={cn(
            'px-4 py-2 font-mono text-sm transition-all border-b-2 -mb-px',
            activeTab === 'logs'
              ? 'text-cyber-primary border-cyber-primary'
              : 'text-gray-500 border-transparent hover:text-gray-300'
          )}
        >
          <History className="w-4 h-4 inline mr-2" />
          Audit Logs
        </button>
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <Card>
          {rules.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="w-12 h-12 text-gray-700 mx-auto mb-4" />
              <p className="text-gray-500 font-mono">No ACL rules configured</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Resource</TableHead>
                  <TableHead>Access Mode</TableHead>
                  <TableHead>Conditions</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
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
                      <code className="text-sm font-mono text-cyber-primary">
                        {rule.resourceId}
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={rule.accessMode === 'any' ? 'success' : 'info'}
                        className="text-xs"
                      >
                        {rule.accessMode.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {rule.conditions.rateLimit && (
                          <p className="text-xs text-gray-400">
                            Rate Limit: {rule.conditions.rateLimit.maxRequests}/
                            {rule.conditions.rateLimit.windowSeconds}s
                          </p>
                        )}
                        {rule.conditions.ipWhitelist && rule.conditions.ipWhitelist.length > 0 && (
                          <p className="text-xs text-gray-400">
                            IP Whitelist: {rule.conditions.ipWhitelist.length} IPs
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={rule.enabled ? 'success' : 'default'}>
                        {rule.enabled ? 'Active' : 'Disabled'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <button className="text-cyber-primary hover:text-cyber-secondary text-sm font-mono mr-3">
                        Edit
                      </button>
                      <button className="text-cyber-accent hover:text-cyber-accent/80 text-sm font-mono">
                        Delete
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <Card>
          <div className="text-center py-12">
            <History className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono mb-2">Audit logs coming soon</p>
            <p className="text-xs text-gray-600">View all access attempts and security events</p>
          </div>
        </Card>
      )}
    </div>
  );
};
