import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Zap, User } from 'lucide-react';
import { cn } from '@/utils/cn';
import { MarketTab } from './components/MarketTab';
import { ProfileTab } from './components/ProfileTab';

interface TabType {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const tabs: TabType[] = [
  { id: 'market', label: 'Market', icon: Zap },
  { id: 'profile', label: 'Profile', icon: User },
];

export const SkillsPage = () => {
  const { user } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get('tab') || 'market';

  const setTab = (tabId: string) => {
    setSearchParams({ tab: tabId });
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
            Browse and manage AI agent skills
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-void-700 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              className={cn(
                'px-4 py-2.5 font-mono text-sm transition-all border-b-2 -mb-px whitespace-nowrap flex items-center gap-2',
                isActive
                  ? 'text-cyber-primary border-cyber-primary bg-cyber-primary/5'
                  : 'text-gray-500 border-transparent hover:text-gray-300'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {currentTab === 'market' && <MarketTab />}
      {currentTab === 'profile' && user && <ProfileTab userId={user.id} username={user.username} />}
    </div>
  );
};
