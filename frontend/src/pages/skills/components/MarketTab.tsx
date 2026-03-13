import { useState } from 'react';
import { useSkills } from '@/hooks/useSkills';
import { Button, Card, Badge, Loading } from '@/components/ui';
import { Search, ExternalLink, Package } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils/cn';

export const MarketTab = () => {
  const { data, isLoading, error } = useSkills({ tags: 'published' });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const skills = data?.items || [];

  // Filter skills by search query and category
  const filteredSkills = skills.filter((skill) => {
    const matchesSearch =
      !searchQuery ||
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory =
      !selectedCategory || skill.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = Array.from(new Set(skills.map((s) => s.category).filter((c): c is string => Boolean(c))));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="text-center py-16">
        <p className="text-cyber-accent font-mono">Failed to load skills</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 font-mono text-sm bg-void-900/50 border border-void-700 rounded-lg text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-cyber-primary"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory(null)}
              className={cn(
                'px-3 py-1.5 text-xs font-mono rounded-lg border transition-all',
                selectedCategory === null
                  ? 'bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary'
                  : 'bg-void-800 border-void-700 text-gray-400 hover:text-gray-200'
              )}
            >
              All
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={cn(
                  'px-3 py-1.5 text-xs font-mono rounded-lg border transition-all',
                  selectedCategory === category
                    ? 'bg-cyber-primary/10 border-cyber-primary/30 text-cyber-primary'
                    : 'bg-void-800 border-void-700 text-gray-400 hover:text-gray-200'
                )}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Results Info */}
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm text-gray-500">
          {skills.length} total • {filteredSkills.length} shown
        </p>
      </div>

      {/* Skills Grid */}
      {filteredSkills.length === 0 ? (
        <Card className="text-center py-16">
          <Package className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h3 className="font-display text-xl font-semibold text-gray-300 mb-2">
            No Skills Found
          </h3>
          <p className="text-gray-500 font-mono">
            {skills.length === 0
              ? 'No skills available in the market yet'
              : 'Try adjusting your search or filters'}
          </p>
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
                    By {skill.created_by}
                  </div>
                  <Link to={`/skills/${skill.id}`}>
                    <Button
                      variant="primary"
                      size="sm"
                      className="gap-1.5"
                    >
                      View Details
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
