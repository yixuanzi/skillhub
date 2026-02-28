import { useState } from 'react';
import { useSkills, useCreateSkill, useUpdateSkill, useDeleteSkill } from '@/hooks/useSkills';
import { Button, Card, Badge, Loading } from '@/components/ui';
import { SkillFormModal } from '@/components/skills';
import { useSkillFilters } from '@/store/skillFilters';
import { Plus, Search, Edit, Trash2, Upload, ExternalLink, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { Skill } from '@/types';

export const SkillsListPage = () => {
  const { data, isLoading } = useSkills();
  const createMutation = useCreateSkill();
  const updateMutation = useUpdateSkill();
  const deleteMutation = useDeleteSkill();
  const filters = useSkillFilters();

  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const skills = data?.items || [];
  const filteredSkills = skills.filter((skill) => {
    const matchesSearch =
      !filters.search ||
      skill.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      skill.description.toLowerCase().includes(filters.search.toLowerCase());
    return matchesSearch;
  });

  const handleCreate = async (data: any) => {
    try {
      setErrorMessage('');
      await createMutation.mutateAsync(data);
      setSuccessMessage('Skill created successfully!');
      setIsCreateModalOpen(false);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to create skill');
    }
  };

  const handleOpenCreateModal = () => {
    setIsCreateModalOpen(true);
  };

  const handleEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleUpdate = async (data: any) => {
    try {
      setErrorMessage('');
      await updateMutation.mutateAsync({ id: editingSkill!.id, data });
      setSuccessMessage('Skill updated successfully!');
      setEditingSkill(null);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to update skill');
    }
  };

  const handleDelete = async (skill: Skill) => {
    try {
      setErrorMessage('');
      if (deleteConfirm === skill.id) {
        await deleteMutation.mutateAsync(skill.id);
        setSuccessMessage('Skill deleted successfully!');
        setDeleteConfirm(null);
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setDeleteConfirm(skill.id);
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to delete skill');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

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
        <Button
          variant="primary"
          onClick={handleOpenCreateModal}
          className="group"
          type="button"
        >
          <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" />
          New Skill
        </Button>
      </div>

      {/* Success and Error Messages */}
      {successMessage && (
        <div className="animate-slide-in">
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-cyber-primary/30 bg-cyber-primary/10">
            <CheckCircle className="w-4 h-4 text-cyber-primary flex-shrink-0" />
            <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="animate-slide-in">
          <div className="px-4 py-3 rounded-lg border border-cyber-accent/20 bg-cyber-accent/10">
            <span className="text-sm font-medium text-cyber-accent">{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search skills..."
              value={filters.search}
              onChange={(e) => filters.setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 font-mono text-sm bg-void-900/50 border border-void-700 rounded-lg text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyber-primary"
            />
          </div>
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
              : 'Try adjusting your search'}
          </p>
          {skills.length === 0 && (
            <Button
              variant="primary"
              onClick={handleOpenCreateModal}
              type="button"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Skill
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSkills.map((skill, index) => (
            <Card
              key={skill.id}
              className="group hover:border-cyber-primary/30 transition-all duration-200 animate-slide-in"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-display font-lg font-semibold text-gray-100 truncate group-hover:text-cyber-primary transition-colors">
                      {skill.name}
                    </h3>
                    <p className="text-xs font-mono text-gray-500 mt-1">
                      v{skill.version}
                    </p>
                  </div>
                  <Badge variant="info" className="text-xs">
                    {skill.category || 'Uncategorized'}
                  </Badge>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 line-clamp-3 mb-4 min-h-[60px]">
                  {skill.description}
                </p>

                {/* Tags */}
                {skill.tags && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {skill.tags.split(',').map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs font-mono rounded bg-void-800 text-gray-300 border border-void-600"
                      >
                        {tag.trim()}
                      </span>
                    ))}
                  </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between pt-3 border-t border-void-700">
                  <div className="text-xs font-mono text-gray-500 truncate">
                    {skill.created_by}
                  </div>
                  <div className="flex items-center gap-2">
                    <Link to={`/skills/${skill.id}`}>
                      <Button variant="ghost" size="sm" className="p-1.5">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(skill)}
                      className="p-1.5"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(skill)}
                      className={cn(
                        'p-1.5 transition-all duration-200',
                        deleteConfirm === skill.id
                          ? 'bg-cyber-accent/20 border border-cyber-accent text-cyber-accent animate-pulse'
                          : 'text-cyber-accent hover:text-cyber-accent'
                      )}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <SkillFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        mode="create"
      />

      {/* Edit Modal */}
      {editingSkill && (
        <SkillFormModal
          isOpen={!!editingSkill}
          onClose={() => setEditingSkill(null)}
          onSubmit={handleUpdate}
          skill={editingSkill}
          mode="edit"
        />
      )}
    </div>
  );
};
