import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useSkill, useUpdateSkill } from '@/hooks/useSkills';
import { useResources } from '@/hooks/useResources';
import { useSkills } from '@/hooks/useSkills';
import { useSkillCreator } from '@/hooks/useSkillCreator';
import { Button, Input, Textarea, Card, Alert, Badge, Loading, Modal } from '@/components/ui';
import { ArrowLeft, Plus, Sparkles, Check, X, Loader2, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils/cn';

type AIGenerationMode = 'base' | 'sop' | null;

export const SkillEditPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: skill, isLoading } = useSkill(id!);
  const updateSkill = useUpdateSkill();
  const generateContent = useSkillCreator();

  // Get the return URL with tab state preserved
  const returnUrl = `/skills${searchParams.get('tab') ? `?tab=${searchParams.get('tab')}` : ''}`;
  const returnDetailUrl = `/skills/${id}${searchParams.get('tab') ? `?tab=${searchParams.get('tab')}` : ''}`;

  // Fetch resources and skills for AI generation (excluding current skill)
  const { data: resourcesData } = useResources({ page: 1, pageSize: 100 });
  const { data: skillsData } = useSkills({ page: 1, pageSize: 100 });

  const resources = resourcesData?.items || [];
  const otherSkills = skillsData?.items.filter(s => s.id !== id) || [];

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    content: '',
    category: '',
    tags: '',
    version: '1.0.0',
  });

  // AI Generation state
  const [aiMode, setAiMode] = useState<AIGenerationMode>(null);
  const [selectedResourceIds, setSelectedResourceIds] = useState<string[]>([]);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Error modal state
  const [errorModal, setErrorModal] = useState<{
    isOpen: boolean;
    message: string;
  }>({ isOpen: false, message: '' });

  // Initialize form with skill data
  useEffect(() => {
    if (skill) {
      setFormData({
        name: skill.name,
        description: skill.description || '',
        content: skill.content || '',
        category: skill.category || '',
        tags: skill.tags || '',
        version: skill.version || '1.0.0',
      });
    }
  }, [skill]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorModal({ isOpen: false, message: '' });
    setSuccessMessage('');

    try {
      await updateSkill.mutateAsync({
        id: id!,
        data: {
          name: formData.name.trim(),
          description: formData.description.trim(),
          content: formData.content.trim() || undefined,
          category: formData.category.trim() || undefined,
          tags: formData.tags.trim() || undefined,
          version: formData.version.trim(),
        },
      });
      setSuccessMessage('Skill updated successfully!');
      setTimeout(() => {
        navigate(returnDetailUrl);
      }, 1000);
    } catch (err) {
      // Extract error message from API response
      let errorMessage = 'Failed to update skill';
      if (err && typeof err === 'object') {
        if ('response' in err && err.response && typeof err.response === 'object' && 'data' in err.response) {
          const data = err.response.data as { detail?: string };
          if (data.detail) {
            errorMessage = data.detail;
          }
        } else if ('message' in err && typeof err.message === 'string') {
          errorMessage = err.message;
        }
      }
      setErrorModal({ isOpen: true, message: errorMessage });
    }
  };

  const handleAIGenerate = async () => {
    if (!aiMode) return;

    setGenerationError('');
    setIsGenerating(true);

    try {
      const request = {
        type: aiMode,
        ...(aiMode === 'base' && {
          resource_id_list: selectedResourceIds.length > 0 ? selectedResourceIds : undefined,
        }),
        ...(aiMode === 'sop' && {
          skill_id_list: selectedSkillIds.length > 0 ? selectedSkillIds : undefined,
          userinput: userInput || undefined,
        }),
      };

      const response = await generateContent.mutateAsync(request);
      setFormData((prev) => ({ ...prev, content: response.content }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate content';
      setGenerationError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleResourceSelection = (resourceId: string) => {
    setSelectedResourceIds((prev) =>
      prev.includes(resourceId) ? prev.filter((x) => x !== resourceId) : [...prev, resourceId]
    );
  };

  const toggleSkillSelection = (skillId: string) => {
    setSelectedSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((x) => x !== skillId) : [...prev, skillId]
    );
  };

  const toggleAI = () => {
    setAiMode((prev) => {
      if (prev) {
        // Clear AI mode
        setSelectedResourceIds([]);
        setSelectedSkillIds([]);
        setUserInput('');
        setGenerationError('');
        return null;
      }
      return 'base'; // Default to base mode
    });
  };

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
        <Link to={returnUrl}>
          <Button variant="secondary">Back to Skills</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={returnDetailUrl}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
            Edit Skill
          </h1>
          <p className="font-mono text-sm text-gray-500">
            Modify your skill configuration or use AI to generate new content
          </p>
        </div>
      </div>

      {/* Success Messages */}
      {successMessage && (
        <div className="animate-slide-in">
          <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-cyber-primary/30 bg-cyber-primary/10">
            <Check className="w-4 h-4 text-cyber-primary flex-shrink-0" />
            <span className="text-sm font-medium text-cyber-primary">{successMessage}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info Card */}
        <Card>
          <div className="space-y-5">
            <Input
              label="Skill Name"
              value={formData.name}
              disabled
              className="bg-void-800/50 text-gray-500"
            />
            <p className="text-xs text-gray-500 font-mono -mt-3">
              Skill name cannot be modified
            </p>

            <Textarea
              label="Description *"
              placeholder="Describe what this skill does..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              rows={3}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Category"
                placeholder="e.g., data-processing"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              />

              <Input
                label="Version"
                placeholder="1.0.0"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              />
            </div>

            <Input
              label="Tags (comma-separated)"
              placeholder="e.g., python, data, api"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            />
          </div>
        </Card>

        {/* AI Assistant Card */}
        <Card className={cn(
          'border transition-all duration-200',
          aiMode ? 'border-cyber-primary/50 bg-cyber-primary/5' : 'border-void-700'
        )}>
          <div className="space-y-4">
            {/* AI Toggle Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className={cn(
                  'w-5 h-5 transition-colors',
                  aiMode ? 'text-cyber-primary' : 'text-gray-500'
                )} />
                <h3 className="font-display font-semibold text-gray-100">
                  AI Content Generation
                </h3>
              </div>
              <Button
                type="button"
                variant={aiMode ? 'primary' : 'ghost'}
                size="sm"
                onClick={toggleAI}
              >
                {aiMode ? 'Disable AI' : 'Enable AI'}
              </Button>
            </div>

            {aiMode && (
              <div className="space-y-4 pt-4 border-t border-void-700">
                {/* Mode Selection */}
                <div>
                  <label className="text-sm font-mono text-gray-400 uppercase tracking-wider mb-2 block">
                    Generation Mode
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setAiMode('base')}
                      className={cn(
                        'px-4 py-2 rounded-lg font-mono text-sm border transition-all',
                        aiMode === 'base'
                          ? 'bg-cyber-primary/10 border-cyber-primary text-cyber-primary'
                          : 'bg-void-800 border-void-700 text-gray-400 hover:text-gray-200'
                      )}
                    >
                      Base Mode
                      <span className="block text-xs opacity-70 mt-1">
                        Generate from Resources
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setAiMode('sop')}
                      className={cn(
                        'px-4 py-2 rounded-lg font-mono text-sm border transition-all',
                        aiMode === 'sop'
                          ? 'bg-cyber-primary/10 border-cyber-primary text-cyber-primary'
                          : 'bg-void-800 border-void-700 text-gray-400 hover:text-gray-200'
                      )}
                    >
                      SOP Mode
                      <span className="block text-xs opacity-70 mt-1">
                        Generate from Skills
                      </span>
                    </button>
                  </div>
                </div>

                {/* Base Mode - Resource Selection */}
                {aiMode === 'base' && (
                  <div>
                    <label className="text-sm font-mono text-gray-400 uppercase tracking-wider mb-2 block">
                      Select Resources
                    </label>
                    <div className="max-h-48 overflow-auto border border-void-700 rounded-lg p-2 space-y-1">
                      {resources.length === 0 ? (
                        <p className="text-sm text-gray-500 text-center py-4">
                          No resources available.
                        </p>
                      ) : (
                        resources.map((resource) => (
                          <button
                            key={resource.id}
                            type="button"
                            onClick={() => toggleResourceSelection(resource.id)}
                            className={cn(
                              'w-full flex items-center justify-between px-3 py-2 rounded text-left transition-all',
                              selectedResourceIds.includes(resource.id)
                                ? 'bg-cyber-primary/20 border border-cyber-primary/30'
                                : 'hover:bg-void-800 border border-transparent'
                            )}
                          >
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <div className={cn(
                                'w-4 h-4 rounded border flex items-center justify-center',
                                selectedResourceIds.includes(resource.id)
                                  ? 'bg-cyber-primary border-cyber-primary'
                                  : 'border-void-600'
                              )}>
                                {selectedResourceIds.includes(resource.id) && (
                                  <Check className="w-3 h-3 text-void-950" />
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-gray-200 truncate">
                                  {resource.name}
                                </p>
                                <p className="text-xs text-gray-500 truncate">
                                  {resource.type} • {resource.url || 'No URL'}
                                </p>
                              </div>
                              <Badge variant="secondary" className="text-xs">
                                {resource.type}
                              </Badge>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                    {selectedResourceIds.length > 0 && (
                      <p className="text-xs text-gray-500 mt-2">
                        {selectedResourceIds.length} resource(s) selected
                      </p>
                    )}
                  </div>
                )}

                {/* SOP Mode - Skill Selection and User Input */}
                {aiMode === 'sop' && (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-mono text-gray-400 uppercase tracking-wider mb-2 block">
                        Select Skills (excluding current skill)
                      </label>
                      <div className="max-h-48 overflow-auto border border-void-700 rounded-lg p-2 space-y-1">
                        {otherSkills.length === 0 ? (
                          <p className="text-sm text-gray-500 text-center py-4">
                            No other skills available.
                          </p>
                        ) : (
                          otherSkills.map((skillItem) => (
                            <button
                              key={skillItem.id}
                              type="button"
                              onClick={() => toggleSkillSelection(skillItem.id)}
                              className={cn(
                                'w-full flex items-center justify-between px-3 py-2 rounded text-left transition-all',
                                selectedSkillIds.includes(skillItem.id)
                                  ? 'bg-cyber-primary/20 border border-cyber-primary/30'
                                  : 'hover:bg-void-800 border border-transparent'
                              )}
                            >
                              <div className="flex items-center gap-2 flex-1 min-w-0">
                                <div className={cn(
                                  'w-4 h-4 rounded border flex items-center justify-center',
                                  selectedSkillIds.includes(skillItem.id)
                                    ? 'bg-cyber-primary border-cyber-primary'
                                    : 'border-void-600'
                                )}>
                                  {selectedSkillIds.includes(skillItem.id) && (
                                    <Check className="w-3 h-3 text-void-950" />
                                  )}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-medium text-gray-200 truncate">
                                    {skillItem.name}
                                  </p>
                                  <p className="text-xs text-gray-500 truncate">
                                    {skillItem.description}
                                  </p>
                                </div>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                      {selectedSkillIds.length > 0 && (
                        <p className="text-xs text-gray-500 mt-2">
                          {selectedSkillIds.length} skill(s) selected
                        </p>
                      )}
                    </div>

                    <Textarea
                      label="Your Requirements *"
                      placeholder="Describe what kind of skill you want to create. For example: 'Create a customer support workflow that handles ticket escalation and resolves common issues...'"
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      rows={4}
                      required={aiMode === 'sop'}
                    />
                  </div>
                )}

                {/* Generation Error */}
                {generationError && (
                  <Alert variant="danger">
                    <span className="text-sm">{generationError}</span>
                  </Alert>
                )}

                {/* Generate Button */}
                <Button
                  type="button"
                  variant="primary"
                  onClick={handleAIGenerate}
                  disabled={isGenerating || (aiMode === 'base' && selectedResourceIds.length === 0) ||
                    (aiMode === 'sop' && (selectedSkillIds.length === 0 || !userInput.trim()))}
                  className="w-full"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Content with AI
                    </>
                  )}
                </Button>

                {isGenerating && (
                  <p className="text-xs text-gray-500 text-center">
                    AI is analyzing the selected resources/skills and generating skill content...
                  </p>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Content Card */}
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-cyber-primary" />
                <h3 className="font-display font-semibold text-gray-100">
                  Content
                </h3>
              </div>
              {formData.content && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setFormData({ ...formData, content: '' })}
                >
                  <X className="w-4 h-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>
            <Textarea
              placeholder="# Enter your skill content here or use AI to generate...

You can write markdown content, code examples, documentation, etc."
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              rows={15}
              className="font-mono text-sm"
              required
            />
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end">
          <Link to={returnDetailUrl}>
            <Button type="button" variant="ghost">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            variant="primary"
            disabled={updateSkill.isPending}
          >
            {updateSkill.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </form>

      {/* Error Modal */}
      <Modal
        isOpen={errorModal.isOpen}
        onClose={() => setErrorModal({ isOpen: false, message: '' })}
        title="Error"
        size="sm"
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-cyber-accent flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-mono text-sm text-gray-200">{errorModal.message}</p>
          </div>
        </div>
        <div className="flex justify-end mt-6">
          <Button
            variant="primary"
            onClick={() => setErrorModal({ isOpen: false, message: '' })}
          >
            OK
          </Button>
        </div>
      </Modal>
    </div>
  );
};
