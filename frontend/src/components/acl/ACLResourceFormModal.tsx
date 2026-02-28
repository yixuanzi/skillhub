import React, { useState, useEffect } from 'react';
import { Modal, Alert, Button } from '@/components/ui';
import { ACLRule, AccessMode } from '@/types';
import { Shield, Lock, Unlock } from 'lucide-react';
import { cn } from '@/utils/cn';
import { JsonEditor } from '@/components/acl';

interface ACLResourceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  rule?: ACLRule | null;
  mode: 'create' | 'edit';
  resources: Array<{ id: string; name: string }>;
}

export const ACLResourceFormModal: React.FC<ACLResourceFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  rule,
  mode,
  resources,
}) => {
  const [resourceId, setResourceId] = useState('');
  const [accessMode, setAccessMode] = useState<AccessMode>('rbac');
  const [conditionsJson, setConditionsJson] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && rule) {
        setResourceId(rule.resource_id);
        setAccessMode(rule.access_mode);
        // Set conditions JSON for editor
        const conditionsObj = rule.conditions || {};
        setConditionsJson(JSON.stringify(conditionsObj, null, 2));
      } else {
        setResourceId('');
        setAccessMode('rbac');
        // Set default conditions template (empty object for all modes)
        setConditionsJson('{}');
      }
      setError('');
    }
  }, [isOpen, mode, rule]);

  const validateForm = (): boolean => {
    if (!resourceId.trim()) {
      setError('Resource is required');
      return false;
    }

    // Validate JSON in conditions field
    if (conditionsJson.trim()) {
      try {
        const parsed = JSON.parse(conditionsJson);
        // Validate that it's an object
        if (typeof parsed !== 'object' || Array.isArray(parsed)) {
          setError('Conditions must be a JSON object');
          return false;
        }
      } catch (err) {
        setError('Invalid JSON in conditions field');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      let conditions: any = {};

      // Parse conditions from JSON editor
      if (conditionsJson.trim()) {
        conditions = JSON.parse(conditionsJson);
      }

      // Find resource name
      const resource = resources.find(r => r.id === resourceId);
      if (!resource && mode === 'create') {
        setError('Resource not found');
        return;
      }

      const data: any = {
        resource_id: resourceId,
        resource_name: resource?.name || resourceId,
        access_mode: accessMode,
      };

      if (Object.keys(conditions).length > 0) {
        data.conditions = conditions;
      }

      await onSubmit(data);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save ACL rule';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Update conditions template when access mode changes (only in create mode)
  useEffect(() => {
    if (!isOpen || mode === 'edit') return;

    // Always use empty object as default for all access modes
    if (!conditionsJson.trim() || conditionsJson === '{}') {
      setConditionsJson('{}');
    }
  }, [accessMode, isOpen, mode]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Create ACL Rule' : 'Edit ACL Rule'} size="xl">
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Error Alert */}
        {error && (
          <Alert variant="danger">
            <span className="text-sm font-medium">{error}</span>
          </Alert>
        )}

        {/* Resource Selection */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Resource *
          </label>
          <select
            value={resourceId}
            onChange={(e) => setResourceId(e.target.value)}
            disabled={mode === 'edit'}
            className="px-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200 disabled:opacity-50"
          >
            <option value="">Select a resource...</option>
            {resources.map((resource) => (
              <option key={resource.id} value={resource.id}>
                {resource.name}
              </option>
            ))}
          </select>
        </div>

        {/* Access Mode */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider flex items-center gap-2">
            {accessMode === 'any' ? (
              <Unlock className="w-4 h-4" />
            ) : (
              <Lock className="w-4 h-4" />
            )}
            Access Mode *
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setAccessMode('any')}
              className={cn(
                'p-4 rounded-lg border-2 transition-all duration-200',
                accessMode === 'any'
                  ? 'border-cyber-primary bg-cyber-primary/10 text-cyber-primary'
                  : 'border-void-700 text-gray-400 hover:border-void-600'
              )}
            >
              <div className="flex flex-col items-center gap-2">
                <Unlock className="w-6 h-6" />
                <div className="text-sm font-mono font-semibold">Public</div>
                <div className="text-xs opacity-70">Anyone can access</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setAccessMode('rbac')}
              className={cn(
                'p-4 rounded-lg border-2 transition-all duration-200',
                accessMode === 'rbac'
                  ? 'border-cyber-primary bg-cyber-primary/10 text-cyber-primary'
                  : 'border-void-700 text-gray-400 hover:border-void-600'
              )}
            >
              <div className="flex flex-col items-center gap-2">
                <Lock className="w-6 h-6" />
                <div className="text-sm font-mono font-semibold">RBAC</div>
                <div className="text-xs opacity-70">Role-based access</div>
              </div>
            </button>
          </div>
        </div>

        {/* Conditions JSON Editor */}
        <div className="space-y-2">
          <p className="text-xs text-gray-500 font-mono">
            Define ACL conditions in JSON format. Supported fields: users, roles, ip_whitelist, rate_limit, time_windows, metadata
          </p>
          <JsonEditor
            value={conditionsJson}
            onChange={setConditionsJson}
            placeholder={`{\n  "roles": ["admin", "editor"],\n  "ip_whitelist": ["192.168.1.0/24"],\n  "rate_limit": {\n    "requests": 100,\n    "window": 60\n  },\n  "time_windows": [\n    {\n      "start": "09:00",\n      "end": "18:00",\n      "days": [1, 2, 3, 4, 5]\n    }\n  ],\n  "metadata": {\n    "description": "Custom condition metadata"\n  }\n}`}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-void-700">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : mode === 'create' ? 'Create Rule' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
