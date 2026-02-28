import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateSkill } from '@/hooks/useSkills';
import { Button, Input, Textarea, Card } from '@/components/ui';
import { ArrowLeft, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export const SkillCreatePage = () => {
  const navigate = useNavigate();
  const createSkill = useCreateSkill();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    content: '',
    category: '',
    tags: '',
    version: '1.0.0',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await createSkill.mutateAsync({
        name: formData.name.trim(),
        description: formData.description.trim(),
        content: formData.content.trim() || undefined,
        category: formData.category.trim() || undefined,
        tags: formData.tags.trim() || undefined,
        version: formData.version.trim(),
      });
      if (result) {
        navigate(`/skills/${result.id}`);
      }
    } catch (err) {
      console.error('Failed to create skill:', err);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <Link to="/skills">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Create New Skill
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Define your skill configuration
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <div className="space-y-5">
            <Input
              label="Skill Name *"
              placeholder="e.g., Data Processor"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />

            <Textarea
              label="Description *"
              placeholder="Describe what this skill does..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              rows={3}
            />

            <Input
              label="Category"
              placeholder="e.g., data-processing"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            />

            <Input
              label="Tags (comma-separated)"
              placeholder="e.g., python, data, api"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            />

            <Input
              label="Version"
              placeholder="1.0.0"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
            />
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Plus className="w-5 h-5 text-cyber-primary" />
              <h3 className="font-display font-semibold text-gray-100">
                Content
              </h3>
            </div>
            <Textarea
              placeholder="# Paste your skill code or content here..."
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              rows={12}
              className="font-mono text-sm"
            />
          </div>
        </Card>

        <div className="flex gap-3 justify-end">
          <Link to="/skills">
            <Button type="button" variant="ghost">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            variant="primary"
            disabled={createSkill.isPending}
          >
            {createSkill.isPending ? 'Creating...' : 'Create Skill'}
          </Button>
        </div>
      </form>
    </div>
  );
};
