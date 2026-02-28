import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateSkill } from '@/hooks/useSkills';
import { Button, Input, Textarea, Card } from '@/components/ui';
import { ArrowLeft, Upload } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SkillType, SkillRuntime } from '@/types';

export const SkillCreatePage = () => {
  const navigate = useNavigate();
  const createSkill = useCreateSkill();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'business_logic' as SkillType,
    runtime: 'python' as SkillRuntime,
    code: '',
    requirements: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await createSkill.mutateAsync(formData);
      if (result.data) {
        navigate(`/skills/${result.data.id}`);
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
              label="Skill Name"
              placeholder="my-awesome-skill"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />

            <Textarea
              label="Description"
              placeholder="Describe what this skill does..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              rows={3}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
                  Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as SkillType })}
                  className="px-4 py-2.5 font-mono text-sm bg-void-900/50 border border-void-700 rounded-lg text-gray-200 focus:outline-none focus:border-cyber-primary"
                  required
                >
                  <option value="business_logic">Business Logic</option>
                  <option value="api_proxy">API Proxy</option>
                  <option value="ai_llm">AI/LLM</option>
                  <option value="data_processing">Data Processing</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
                  Runtime
                </label>
                <select
                  value={formData.runtime}
                  onChange={(e) => setFormData({ ...formData, runtime: e.target.value as SkillRuntime })}
                  className="px-4 py-2.5 font-mono text-sm bg-void-900/50 border border-void-700 rounded-lg text-gray-200 focus:outline-none focus:border-cyber-primary"
                  required
                >
                  <option value="python">Python 3.11+</option>
                  <option value="nodejs">Node.js 18+</option>
                  <option value="go">Go 1.22+</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Upload className="w-5 h-5 text-cyber-primary" />
              <h3 className="font-display font-semibold text-gray-100">
                Source Code
              </h3>
            </div>
            <Textarea
              placeholder="# Paste your skill code here..."
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              required
              rows={12}
              className="font-mono text-xs"
            />
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <h3 className="font-display font-semibold text-gray-100">
              Dependencies
            </h3>
            <Textarea
              label="requirements.txt"
              placeholder="fastapi==0.104.0&#10;pydantic==2.5.0&#10;httpx==0.25.0"
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              rows={5}
              className="font-mono text-xs"
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
