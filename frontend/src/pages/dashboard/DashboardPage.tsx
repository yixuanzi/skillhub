import { useSkills } from '@/hooks/useSkills';
import { Card, Badge, Loading } from '@/components/ui';
import { Package, TrendingUp, Users, Activity } from 'lucide-react';

export const DashboardPage = () => {
  const { data: skillsData, isLoading } = useSkills({ pageSize: 10 });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  const skills = skillsData?.items || [];
  const totalSkills = skills.length;
  const publishedSkills = skills.length; // All skills are published in the current model
  const draftSkills = 0; // No draft status in the current model

  const stats = [
    {
      label: 'Total Skills',
      value: totalSkills,
      icon: Package,
      color: 'text-cyber-primary',
      bgColor: 'bg-cyber-primary/10',
    },
    {
      label: 'Published',
      value: publishedSkills,
      icon: TrendingUp,
      color: 'text-cyber-secondary',
      bgColor: 'bg-cyber-secondary/10',
    },
    {
      label: 'Drafts',
      value: draftSkills,
      icon: Activity,
      color: 'text-cyber-warning',
      bgColor: 'bg-cyber-warning/10',
    },
    {
      label: 'Active Users',
      value: '---',
      icon: Users,
      color: 'text-cyber-accent',
      bgColor: 'bg-cyber-accent/10',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-gray-100 mb-2">
          Dashboard
        </h1>
        <p className="font-mono text-sm text-gray-500">
          System Overview • {new Date().toLocaleDateString()}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card
            key={stat.label}
            className="animate-slide-in"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-2">
                  {stat.label}
                </p>
                <p className="font-display text-3xl font-bold text-gray-100">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Skills */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display text-lg font-semibold text-gray-100">
            Recent Skills
          </h2>
          <Badge variant="info">Latest</Badge>
        </div>

        {skills.length === 0 ? (
          <div className="text-center py-12">
            <Package className="w-12 h-12 text-gray-700 mx-auto mb-4" />
            <p className="text-gray-500 font-mono">No skills yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {skills.slice(0, 5).map((skill, index) => (
              <div
                key={skill.id}
                className="flex items-center justify-between p-4 rounded-lg bg-void-900/50 border border-void-800 hover:border-void-700 transition-all animate-slide-in"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-primary/20 to-cyber-secondary/20 flex items-center justify-center">
                    <Package className="w-5 h-5 text-cyber-primary" />
                  </div>
                  <div>
                    <p className="font-mono text-sm font-medium text-gray-200">
                      {skill.name}
                    </p>
                    <p className="text-xs text-gray-500 font-mono">
                      v{skill.version} {skill.category && `• ${skill.category}`}
                    </p>
                  </div>
                </div>
                <Badge variant="info">
                  {skill.created_by}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
