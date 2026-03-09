import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { MarketTab } from './components/MarketTab';
import { ProfileTab } from './components/ProfileTab';

export const SkillsPage = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('market');

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
      <Tabs defaultValue="market" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-fit">
          <TabsTrigger value="market">
            Market
          </TabsTrigger>
          <TabsTrigger value="profile">
            Profile
          </TabsTrigger>
        </TabsList>

        <TabsContent value="market" className="mt-6">
          <MarketTab />
        </TabsContent>

        <TabsContent value="profile" className="mt-6">
          {user && <ProfileTab userId={user.id} username={user.username} />}
        </TabsContent>
      </Tabs>
    </div>
  );
};
