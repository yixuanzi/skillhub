import { useState } from 'react';
import { useSkills, useDeleteSkill } from '@/hooks/useSkills';
import { Button, Card, Badge, Loading, Modal } from '@/components/ui';
import { useSkillFilters } from '@/store/skillFilters';
import { Plus, Search, Trash2, Upload } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { SkillType, SkillStatus } from '@/types';

export const SkillsListPage = () => {
  const { data, isLoading } = useSkills();
  const deleteSkill = useDeleteSkill();
  const filters = useSkillFilters();
  const [deleteModal, setDeleteModal] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  const skills = data?.data?.items || [];
  const filteredSkills = skills.filter((skill) => {
    const matchesSearch =
      !filters.search ||
      skill.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      skill.description.toLowerCase().includes(filters.search.toLowerCase());
    const matchesType = filters.type === 'all' || skill.type === filters.type;
    const matchesStatus = filters.status === 'all' || skill.status === filters.status;
    const matchesRuntime = filters.runtime === 'all' || skill.runtime === filters.runtime;
    return matchesSearch && matchesType && matchesStatus && matchesRuntime;
  });

  const handleDelete = async () => {
    if (deleteModal) {
      await deleteSkill.mutateAsync(deleteModal);
      setDeleteModal(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Skills
          </h1>
          <p className="font-mono text-sm text-gray-500">
            {skills.length} total • {filteredSkills.length} shown
          </p>
        </div>
        <Link to="/skills/new">
          <Button variant="primary" size="md">
            <Plus className="w-4 h-4" />
            Create Skill
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search skills..."
                value={filters.search}
                onChange={(e) => filters.setSearch(e.target.value)}
                className={cn(
                  'w-full pl-10 pr-4 py-2 font-mono text-sm',
                  'bg-void-900/50 border border-void-700 rounded-lg',
                  'text-gray-200 placeholder:text-gray-600',
                  'focus:outline-none focus:border-cyber-primary'
                )}
              />
            </div>
          </div>

          {/* Type Filter */}
          <select
            value={filters.type}
            onChange={(e) => filters.setType(e.target.value as SkillType | 'all')}
            className={cn(
              'px-4 py-2 font-mono text-sm',
              'bg-void-900/50 border border-void-700 rounded-lg',
              'text-gray-200',
              'focus:outline-none focus:border-cyber-primary'
            )}
          >
            <option value="all">All Types</option>
            <option value="business_logic">Business Logic</option>
            <option value="api_proxy">API Proxy</option>
            <option value="ai_llm">AI/LLM</option>
            <option value="data_processing">Data Processing</option>
          </select>

          {/* Status Filter */}
          <select
            value={filters.status}
            onChange={(e) => filters.setStatus(e.target.value as SkillStatus | 'all')}
            className={cn(
              'px-4 py-2 font-mono text-sm',
              'bg-void-900/50 border border-void-700 rounded-lg',
              'text-gray-200',
              'focus:outline-none focus:border-cyber-primary'
            )}
          >
            <option value="all">All Status</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </Card>

      {/* Skills Grid */}
      {filteredSkills.length === 0 ? (
        <Card className="text-center py-16">
          <Upload className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h3 className="font-display text-xl font-semibold text-gray-300 mb-2">
            No Skills Found
          </h3>
          <p className="text-gray-500 font-mono mb-6">
            {skills.length === 0
              ? 'Get started by creating your first skill'
              : 'Try adjusting your filters'}
          </p>
          {skills.length === 0 && (
            <Link to="/skills/new">
              <Button variant="primary">
                <Plus className="w-4 h-4" />
                Create Your First Skill
              </Button>
            </Link>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredSkills.map((skill, index) => (
            <Card
              key={skill.id}
              className="animate-slide-in group hover:border-cyber-primary/30 transition-all"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-primary/20 to-cyber-secondary/20 flex items-center justify-center">
                    <Upload className="w-5 h-5 text-cyber-primary" />
                  </div>
                  <div>
                    <Link
                      to={`/skills/${skill.id}`}
                      className="font-display font-semibold text-gray-100 hover:text-cyber-primary transition-colors"
                    >
                      {skill.name}
                    </Link>
                    <p className="text-xs text-gray-500 font-mono">
                      v{skill.currentVersion}
                    </p>
                  </div>
                </div>
                <Badge
                  variant={skill.status === 'published' ? 'success' : 'warning'}
                >
                  {skill.status}
                </Badge>
              </div>

              <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                {skill.description}
              </p>

              <div className="flex items-center gap-2 mb-4">
                <Badge variant="default" className="text-xs">
                  {skill.type}
                </Badge>
                <Badge variant="default" className="text-xs">
                  {skill.runtime}
                </Badge>
              </div>

              <div className="flex items-center gap-2 pt-4 border-t border-void-700">
                <Link to={`/skills/${skill.id}`} className="flex-1">
                  <Button variant="secondary" size="sm" className="w-full">
                    View Details
                  </Button>
                </Link>
                <button
                  onClick={() => setDeleteModal(skill.id)}
                  className="p-2 text-gray-500 hover:text-cyber-accent hover:bg-cyber-accent/10 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteModal}
        onClose={() => setDeleteModal(null)}
        title="Delete Skill"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to delete this skill? This action cannot be undone.
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              variant="ghost"
              onClick={() => setDeleteModal(null)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={deleteSkill.isPending}
            >
              {deleteSkill.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
