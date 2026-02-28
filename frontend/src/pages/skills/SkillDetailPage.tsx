import { useParams } from 'react-router-dom';
import { useSkill, useInvokeSkill } from '@/hooks/useSkills';
import { Button, Card, Badge, Loading, Modal } from '@/components/ui';
import { ArrowLeft, Play, Edit } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { Textarea } from '@/components/ui';
import { formatRelativeTime } from '@/utils/date';

export const SkillDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const { data: skill, isLoading } = useSkill(id!);
  const invokeSkill = useInvokeSkill();

  const [testModal, setTestModal] = useState(false);
  const [testParams, setTestParams] = useState('{}');
  const [testResult, setTestResult] = useState<unknown>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  if (!skill) {
    return (
      <div className="text-center py-16">
        <h2 className="font-display text-xl text-gray-300 mb-2">Skill not found</h2>
        <Link to="/skills">
          <Button variant="secondary">Back to Skills</Button>
        </Link>
      </div>
    );
  }

  const handleTest = async () => {
    try {
      const params = JSON.parse(testParams);
      const result = await invokeSkill.mutateAsync({
        skill_id: id!,
        params,
      });
      setTestResult(result);
    } catch (err) {
      setTestResult({ error: err instanceof Error ? err.message : 'Invalid JSON' });
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/skills">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            {skill.name}
          </h1>
          <p className="font-mono text-sm text-gray-500">
            {skill.category && `${skill.category} •`} v{skill.version} • by {skill.created_by}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setTestModal(true)}>
            <Play className="w-4 h-4" />
            Test
          </Button>
          <Link to={`/skills/${skill.id}/edit`}>
            <Button variant="primary">
              <Edit className="w-4 h-4" />
              Edit
            </Button>
          </Link>
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-3">
              Description
            </h3>
            <p className="text-gray-300">{skill.description}</p>
            {skill.tags && (
              <div className="mt-4">
                <h4 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-2">
                  Tags
                </h4>
                <div className="flex flex-wrap gap-2">
                  {skill.tags.split(',').map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs font-mono rounded bg-void-800 text-gray-300 border border-void-600"
                    >
                      {tag.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div>
            <h3 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-3">
              Metadata
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Version</span>
                <span className="text-sm font-mono text-gray-200">v{skill.version}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Created by</span>
                <span className="text-sm font-mono text-gray-200">{skill.created_by}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Created at</span>
                <span className="text-sm text-gray-500">{formatRelativeTime(skill.created_at)}</span>
              </div>
              {skill.updated_at !== skill.created_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Updated at</span>
                  <span className="text-sm text-gray-500">{formatRelativeTime(skill.updated_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Code/Content */}
      {skill.content && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-lg font-semibold text-gray-100">
              Code
            </h2>
            <Badge variant="info">Content</Badge>
          </div>
          <pre className="bg-void-950 p-4 rounded-lg overflow-auto max-h-96 text-sm font-mono text-gray-300">
            {skill.content}
          </pre>
        </Card>
      )}

      {/* Test Modal */}
      <Modal isOpen={testModal} onClose={() => setTestModal(false)} title="Test Skill" size="lg">
        <div className="space-y-4">
          <Textarea
            label="Parameters (JSON)"
            placeholder='{"key": "value"}'
            value={testParams}
            onChange={(e) => setTestParams(e.target.value)}
            rows={6}
          />
          <Button
            variant="primary"
            onClick={handleTest}
            disabled={invokeSkill.isPending}
            className="w-full"
          >
            <Play className="w-4 h-4" />
            {invokeSkill.isPending ? 'Running...' : 'Run Test'}
          </Button>
          {testResult !== null && (
            <div className="mt-4">
              <h4 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-2">
                Result
              </h4>
              <pre className="bg-void-950 p-4 rounded-lg overflow-auto max-h-64 text-sm font-mono text-gray-300">
                {JSON.stringify(testResult, null, 2) as string}
              </pre>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};
