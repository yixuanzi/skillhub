import React, { useState, useEffect } from 'react';
import { Modal, Input, Textarea, Alert, Button } from '@/components/ui';
import { JsonEditor } from './JsonEditor';
import { Resource, ResourceCreate, ResourceType } from '@/types';

interface ResourceFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ResourceCreate) => Promise<void>;
  resource?: Resource;
  mode: 'create' | 'edit';
}

export const ResourceFormModal: React.FC<ResourceFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  resource,
  mode,
}) => {
  const [name, setName] = useState('');
  const [type, setType] = useState<ResourceType>('build');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [ext, setExt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && resource) {
        setName(resource.name);
        setType(resource.type);
        setUrl(resource.url || '');
        setDescription(resource.desc || '');
        setExt(resource.ext ? JSON.stringify(resource.ext, null, 2) : '');
      } else {
        setName('');
        setType('build');
        setUrl('');
        setDescription('');
        setExt('');
      }
      setError('');
    }
  }, [isOpen, mode, resource]);

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setError('Name is required');
      return false;
    }

    // Validate JSON in ext field if provided
    if (ext.trim()) {
      try {
        JSON.parse(ext);
      } catch (err) {
        setError('Invalid JSON in extended properties');
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
      const data: ResourceCreate = {
        name: name.trim(),
        type,
        url: url.trim() || undefined,
        desc: description.trim() || undefined,
        ext: ext.trim() ? JSON.parse(ext) : undefined,
      };

      await onSubmit(data);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save resource';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const resourceTypes: { value: ResourceType; label: string }[] = [
    { value: 'build', label: 'Build' },
    { value: 'gateway', label: 'Gateway' },
    { value: 'third', label: 'Third Party' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Create Resource' : 'Edit Resource'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Error Alert */}
        {error && (
          <Alert variant="danger">
            <span className="text-sm font-medium">{error}</span>
          </Alert>
        )}

        {/* Name Field */}
        <Input
          label="Name *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter resource name"
          required
        />

        {/* Type Field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
            Type *
          </label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as ResourceType)}
            className="px-4 py-2.5 font-mono text-sm rounded-lg bg-void-900/50 border border-void-700 text-gray-100 focus:outline-none focus:border-cyber-primary transition-all duration-200"
          >
            {resourceTypes.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* URL Field */}
        <Input
          label="URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          type="url"
        />

        {/* Description Field */}
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter resource description"
          rows={3}
        />

        {/* Extended Properties (JSON) */}
        <JsonEditor
          value={ext}
          onChange={setExt}
          placeholder='{\n  "key": "value"\n}'
        />

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
            {loading ? 'Saving...' : mode === 'create' ? 'Create Resource' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
