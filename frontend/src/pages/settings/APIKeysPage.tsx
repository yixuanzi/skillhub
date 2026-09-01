import { useState } from 'react';
import { Key, Plus, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Alert } from '@/components/ui/Alert';
import {
  useAPIKeys,
  useCreateAPIKey,
  useDeleteAPIKey,
  useUpdateAPIKey,
  useRotateAPIKey,
} from '@/hooks/use-api-keys';
import { APIKeyTable } from './components/APIKeyTable';
import { APIKeyFormModal } from './components/APIKeyFormModal';
import { APIKeyDisplayModal } from './components/APIKeyDisplayModal';

const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === 'object' && error !== null) {
    const response = (
      error as {
        response?: { data?: { error?: { message?: unknown }; detail?: unknown } };
      }
    ).response;

    if (typeof response?.data?.error?.message === 'string') {
      return response.data.error.message;
    }
    if (typeof response?.data?.detail === 'string') {
      return response.data.detail;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
};

export const APIKeysPage = () => {
  const { data: apiKeys, isLoading: isLoadingKeys, error: keysError } = useAPIKeys();
  const createMutation = useCreateAPIKey();
  const deleteMutation = useDeleteAPIKey();
  const updateMutation = useUpdateAPIKey();
  const rotateMutation = useRotateAPIKey();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [displayKey, setDisplayKey] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const allKeys = apiKeys || [];

  const handleCreateKey = async (data: { name: string; scopes: string[]; expires_at?: string }) => {
    try {
      setErrorMessage('');
      const response = await createMutation.mutateAsync(data);
      setDisplayKey(response.key);
      setIsFormModalOpen(false);
      setSuccessMessage('API key created successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, 'Failed to create API key'));
    }
  };

  const handleDeleteKey = async (id: string) => {
    try {
      setErrorMessage('');
      if (deleteConfirm === id) {
        await deleteMutation.mutateAsync(id);
        setSuccessMessage('API key deleted successfully!');
        setDeleteConfirm(null);
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setDeleteConfirm(id);
      }
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, 'Failed to delete API key'));
    }
  };

  const handleToggleKey = async (key: { id: string; is_active: boolean }) => {
    try {
      setErrorMessage('');
      await updateMutation.mutateAsync({
        id: key.id,
        data: { is_active: !key.is_active },
      });
      setDeleteConfirm(null);
      setSuccessMessage(`API key ${key.is_active ? 'disabled' : 'enabled'} successfully!`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, 'Failed to update API key'));
    }
  };

  const handleRotateKey = async (id: string) => {
    try {
      setErrorMessage('');
      const response = await rotateMutation.mutateAsync(id);
      setDisplayKey(response.key);
      setSuccessMessage('API key rotated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: unknown) {
      setErrorMessage(getErrorMessage(error, 'Failed to rotate API key'));
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Success Message */}
      {successMessage && (
        <div className="animate-slide-in">
          <Alert variant="success" className="border-cyber-primary/30 bg-cyber-primary/10">
            <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
          </Alert>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="animate-slide-in">
          <Alert variant="danger">
            <span className="text-sm font-medium">{errorMessage}</span>
          </Alert>
        </div>
      )}

      {/* API Keys Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-semibold text-gray-100">API Keys</h2>
          <p className="font-mono text-sm text-gray-500">
            Manage your personal API keys for programmatic access
          </p>
        </div>
        <Button variant="primary" onClick={() => setIsFormModalOpen(true)} className="group">
          <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
          Create New Key
        </Button>
      </div>

      {/* Info Alert */}
      <Card className="p-4 border-cyber-secondary/30 bg-cyber-secondary/5">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-cyber-secondary flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-cyber-secondary">About API Keys</p>
            <p className="text-xs text-gray-400">
              API keys allow you to authenticate with the SkillHub API programmatically. Each key
              can have specific scopes (permissions), can be disabled temporarily, and can be
              deleted permanently. Store your keys securely and treat them like passwords.
            </p>
          </div>
        </div>
      </Card>

      {/* API Keys Table */}
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="font-mono text-sm font-semibold text-gray-300 uppercase tracking-wider">
            API Keys ({allKeys.length})
          </h3>
        </div>
        {isLoadingKeys ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-2 border-cyber-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 font-mono text-sm mt-4">Loading API keys...</p>
          </div>
        ) : keysError ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-cyber-accent mx-auto mb-4" />
            <p className="text-gray-500 font-mono text-sm">Failed to load API keys</p>
          </div>
        ) : allKeys.length === 0 ? (
          <div className="text-center py-12">
            <Key className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono text-sm mb-2">No API keys yet</p>
            <p className="text-xs text-gray-600">Create your first API key to get started</p>
          </div>
        ) : (
          <APIKeyTable
            apiKeys={allKeys}
            onDelete={handleDeleteKey}
            onToggleActive={handleToggleKey}
            onRotate={handleRotateKey}
            deleteConfirm={deleteConfirm}
          />
        )}
      </Card>

      {/* Create Modal */}
      <APIKeyFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSubmit={handleCreateKey}
      />

      {/* Display Modal */}
      {displayKey && <APIKeyDisplayModal apiKey={displayKey} onClose={() => setDisplayKey(null)} />}
    </div>
  );
};

export default APIKeysPage;
