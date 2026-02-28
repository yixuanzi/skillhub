import { useParams } from 'react-router-dom';
import { useSkill, useSkillVersions, useBuildSkill, usePublishSkill, useInvokeSkill } from '@/hooks/useSkills';
import { Button, Card, Badge, Loading, Modal } from '@/components/ui';
import { ArrowLeft, Build, Upload, Play, Code } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { Textarea } from '@/components/ui';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/date';

export const SkillDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const { data: skillData, isLoading } = useSkill(id!);
  const { data: versionsData } = useSkillVersions(id!);
  const buildSkill = useBuildSkill();
  const publishSkill = usePublishSkill();
  const invokeSkill = useInvokeSkill();

  const [buildModal, setBuildModal] = useState(false);
  const [testModal, setTestModal] = useState(false);
  const [testParams, setTestParams] = useState('{}');
  const [testResult, setTestResult] = useState<unknown>(null);
  const [publishModal, setPublishModal] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<string>('');

  const skill = skillData?.data;
  const versions = versionsData?.data || [];

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

  const handleBuild = async () => {
    await buildSkill.mutateAsync(id!);
    setBuildModal(false);
  };

  const handlePublish = async () => {
    if (selectedVersion) {
      await publishSkill.mutateAsync({ id: id!, version: selectedVersion });
      setPublishModal(false);
    }
  };

  const handleTest = async () => {
    try {
      const params = JSON.parse(testParams);
      const result = await invokeSkill.mutateAsync({
        skillId: id!,
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
            {skill.type} • {skill.runtime} • v{skill.currentVersion}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setBuildModal(true)}>
            <Build className="w-4 h-4" />
            Build
          </Button>
          <Button variant="secondary" onClick={() => setTestModal(true)}>
            <Play className="w-4 h-4" />
            Test
          </Button>
          {skill.status === 'draft' && (
            <Button variant="primary" onClick={() => setPublishModal(true)}>
              <Upload className="w-4 h-4" />
              Publish
            </Button>
          )}
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
          </div>
          <div>
            <h3 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-3">
              Metadata
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Status</span>
                <Badge variant={skill.status === 'published' ? 'success' : 'warning'}>
                  {skill.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Current Version</span>
                <span className="text-sm font-mono text-gray-200">v{skill.currentVersion}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Created</span>
                <span className="text-sm text-gray-500">{formatRelativeTime(skill.createdAt)}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Versions */}
      <Card>
        <h2 className="font-display text-lg font-semibold text-gray-100 mb-4">
          Version History
        </h2>
        {versions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No versions yet</p>
        ) : (
          <div className="space-y-3">
            {versions.map((version, index) => (
              <div
                key={version.id}
                className={cn(
                  'flex items-center justify-between p-4 rounded-lg border transition-all',
                  version.status === 'published'
                    ? 'bg-cyber-primary/5 border-cyber-primary/20'
                    : 'bg-void-900/50 border-void-800',
                  index === 0 && 'border-l-2 border-l-cyber-primary'
                )}
              >
                <div className="flex items-center gap-4">
                  <Code className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="font-mono text-sm text-gray-200">v{version.version}</p>
                    <p className="text-xs text-gray-500">
                      {formatRelativeTime(version.createdAt)}
                    </p>
                  </div>
                </div>
                <Badge variant={version.status === 'published' ? 'success' : 'default'}>
                  {version.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Build Modal */}
      <Modal isOpen={buildModal} onClose={() => setBuildModal(false)} title="Build Skill" size="sm">
        <div className="space-y-4">
          <p className="text-gray-300">
            Build and package the skill with its dependencies. This will create a new version.
          </p>
          <div className="flex gap-3 justify-end">
            <Button variant="ghost" onClick={() => setBuildModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleBuild}
              disabled={buildSkill.isPending}
            >
              {buildSkill.isPending ? 'Building...' : 'Build'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Publish Modal */}
      <Modal isOpen={publishModal} onClose={() => setPublishModal(false)} title="Publish Skill" size="sm">
        <div className="space-y-4">
          <p className="text-gray-300">Select a version to publish:</p>
          <div className="space-y-2">
            {versions.map((version) => (
              <button
                key={version.id}
                onClick={() => setSelectedVersion(version.version)}
                className={cn(
                  'w-full p-3 rounded-lg border text-left transition-all',
                  selectedVersion === version.version
                    ? 'bg-cyber-primary/10 border-cyber-primary'
                    : 'bg-void-900/50 border-void-700 hover:border-void-600'
                )}
              >
                <p className="font-mono text-sm text-gray-200">v{version.version}</p>
                <p className="text-xs text-gray-500">{formatRelativeTime(version.createdAt)}</p>
              </button>
            ))}
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="ghost" onClick={() => setPublishModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handlePublish}
              disabled={!selectedVersion || publishSkill.isPending}
            >
              {publishSkill.isPending ? 'Publishing...' : 'Publish'}
            </Button>
          </div>
        </div>
      </Modal>

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
          {testResult && (
            <div className="mt-4">
              <h4 className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-2">
                Result
              </h4>
              <pre className="bg-void-950 p-4 rounded-lg overflow-auto max-h-64 text-sm font-mono text-gray-300">
                {JSON.stringify(testResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};
