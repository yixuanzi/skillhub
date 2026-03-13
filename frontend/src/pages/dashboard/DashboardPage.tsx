import { useSkillStatistics } from '@/hooks/useSkills';
import { Card, Loading } from '@/components/ui';
import { InstallGuideCard } from '@/components/install-guide/InstallGuideCard';
import { Package, TrendingUp, Users, Activity, Calendar } from 'lucide-react';

export const DashboardPage = () => {
  const { data: stats, isLoading } = useSkillStatistics();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loading size="lg" />
      </div>
    );
  }

  const statsCards = [
    {
      label: 'Total Skills',
      value: stats?.total_skills ?? 0,
      icon: Package,
      color: 'text-cyber-primary',
      bgColor: 'bg-cyber-primary/10',
    },
    {
      label: 'Published',
      value: stats?.published_skills ?? 0,
      icon: TrendingUp,
      color: 'text-cyber-secondary',
      bgColor: 'bg-cyber-secondary/10',
    },
    {
      label: 'Drafts',
      value: stats?.draft_skills ?? 0,
      icon: Activity,
      color: 'text-cyber-warning',
      bgColor: 'bg-cyber-warning/10',
    },
    {
      label: 'Active Users',
      value: stats?.active_users ?? 0,
      icon: Users,
      color: 'text-cyber-accent',
      bgColor: 'bg-cyber-accent/10',
    },
    {
      label: 'New (7 days)',
      value: stats?.new_skills_last_7days ?? 0,
      icon: Calendar,
      color: 'text-cyber-primary',
      bgColor: 'bg-cyber-primary/10',
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {statsCards.map((stat, index) => (
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

      {/* Install Guide */}
      <InstallGuideCard />
    </div>
  );
};
