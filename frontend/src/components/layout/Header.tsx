import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useUIStore } from '@/store/uiStore';
import { useCurrentUser } from '@/hooks/useAuth';
import { Menu, Bell, Search, Loader2 } from 'lucide-react';
import { UserProfileModal } from './UserProfileModal';

export const Header = () => {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const [isUserProfileOpen, setIsUserProfileOpen] = useState(false);

  // Fetch current user data from API
  const { data: currentUser, isLoading } = useCurrentUser();
  // Use fresh data from API if available, otherwise fall back to store data
  const displayUser = currentUser || user;

  const handleLogout = () => {
    logout();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-void-950/80 backdrop-blur-md border-b border-void-700/50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-gray-400 hover:text-gray-200 hover:bg-void-800 rounded-lg transition-all lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search */}
          <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-void-900/50 border border-void-700 rounded-lg">
            <Search className="w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search skills..."
              className="bg-transparent border-none outline-none text-sm text-gray-200 placeholder:text-gray-600 w-64 font-mono"
            />
          </div>
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-200 hover:bg-void-800 rounded-lg transition-all">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyber-accent rounded-full animate-pulse" />
          </button>

          {/* User */}
          <button
            onClick={() => setIsUserProfileOpen(true)}
            className="flex items-center gap-3 pl-3 border-l border-void-700 hover:bg-void-800/50 rounded-lg px-3 py-2 transition-all cursor-pointer"
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
              </div>
            ) : (
              <>
                <div className="hidden sm:block text-right">
                  <p className="text-sm font-mono text-gray-200">{displayUser?.username}</p>
                  <p className="text-xs text-gray-500">
                    {displayUser?.roles && displayUser.roles.length > 0
                      ? displayUser.roles.map((r) => r.name).join(', ')
                      : 'No roles'}
                  </p>
                </div>
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold">
                  {displayUser?.username?.[0]?.toUpperCase() || '?'}
                </div>
              </>
            )}
          </button>
        </div>
      </div>

      {/* User Profile Modal */}
      <UserProfileModal
        isOpen={isUserProfileOpen}
        onClose={() => setIsUserProfileOpen(false)}
        user={displayUser}
        onLogout={handleLogout}
      />
    </header>
  );
};
