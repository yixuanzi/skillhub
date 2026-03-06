import { useSearchParams } from 'react-router-dom';
import { Settings, Key, FileText } from 'lucide-react';
import { cn } from '@/utils/cn';
import { APIKeysPage } from './APIKeysPage';
import { AuditLogsPage } from './AuditLogsPage';

interface TabType {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const tabs: TabType[] = [
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'audit-logs', label: 'Audit Logs', icon: FileText },
];

export const SettingsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get('tab') || 'api-keys';

  const setTab = (tabId: string) => {
    setSearchParams({ tab: tabId });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <Settings className="w-8 h-8 text-cyber-primary" />
          <h1 className="font-display text-3xl font-bold text-gray-100">Settings</h1>
        </div>
        <p className="font-mono text-sm text-gray-500">
          Manage your API keys and view audit logs
        </p>
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
      {currentTab === 'api-keys' && <APIKeysPage />}
      {currentTab === 'audit-logs' && <AuditLogsPage />}
    </div>
  );
};

// Export components for sub-pages
export const SettingsPageHeader: React.FC<{title: string; description: string}> = ({ title, description }) => (
  <div className="space-y-2">
    <h1 className="font-display text-3xl font-bold text-gray-100">{title}</h1>
    <p className="font-mono text-sm text-gray-500">{description}</p>
  </div>
);

export const SettingsTabs: React.FC<{
  tabs: Array<{id: string; label: string; icon: React.ComponentType<{className?: string}>}>;
  activeTab: string;
  onChange: (tabId: string) => void;
}> = ({ tabs, activeTab, onChange }) => (
  <div className="flex gap-2 border-b border-void-700 overflow-x-auto">
    {tabs.map((tab) => {
      const Icon = tab.icon;
      const isActive = activeTab === tab.id;
      return (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
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
);

