import React, { useState, useEffect } from 'react';
import { Modal, Input, Textarea, Alert, Button } from '@/components/ui';
import { Skill, SkillCreateRequest } from '@/types';
import { Code, Tag as TagIcon, FolderOpen } from 'lucide-react';

interface SkillFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SkillCreateRequest) => Promise<void>;
  skill?: Skill | null;
  mode: 'create' | 'edit';
}

export const SkillFormModal: React.FC<SkillFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  skill,
  mode,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState('');
  const [version, setVersion] = useState('1.0.0');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && skill) {
        setName(skill.name);
        setDescription(skill.description || '');
        setContent(skill.content || '');
        setCategory(skill.category || '');
        setTags(skill.tags || '');
        setVersion(skill.version || '1.0.0');
      } else {
        setName('');
        setDescription('');
        setContent('');
        setCategory('');
        setTags('');
        setVersion('1.0.0');
      }
      setError('');
    }
  }, [isOpen, mode, skill]);

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setError('Name is required');
      return false;
    }

    if (!description.trim()) {
      setError('Description is required');
      return false;
    }

    // Validate tags format (comma-separated)
    if (tags.trim()) {
      const tagList = tags.split(',').map(t => t.trim());
      if (tagList.some(t => !t)) {
        setError('Tags cannot be empty');
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
      const data: SkillCreateRequest = {
        name: name.trim(),
        description: description.trim(),
        content: content.trim() || undefined,
        category: category.trim() || undefined,
        tags: tags.trim() || undefined,
        version: version.trim(),
      };

      await onSubmit(data);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save skill';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Create New Skill' : 'Edit Skill'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Error Alert */}
        {error && (
          <Alert variant="danger">
            <span className="text-sm font-medium">{error}</span>
          </Alert>
        )}

        {/* Name Field */}
        <Input
          label="Skill Name *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Data Processor"
          required
        />

        {/* Description Field */}
        <Textarea
          label="Description *"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what this skill does..."
          rows={3}
          required
        />

        {/* Content Field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Code className="w-4 h-4" />
            Code / Content
          </label>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter the skill code or content..."
            rows={6}
            className="font-mono text-sm"
          />
        </div>

        {/* Category Field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <FolderOpen className="w-4 h-4" />
            Category
          </label>
          <Input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g., data-processing"
          />
        </div>

        {/* Tags Field */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <TagIcon className="w-4 h-4" />
            Tags (comma-separated)
          </label>
          <Input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g., python, data, api"
          />
          <p className="text-xs text-gray-500">
            Separate multiple tags with commas
          </p>
        </div>

        {/* Version Field */}
        <Input
          label="Version"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          placeholder="1.0.0"
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
            {loading ? 'Saving...' : mode === 'create' ? 'Create Skill' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
