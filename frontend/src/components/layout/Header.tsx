import { useAuthStore } from '@/store/authStore';
import { useUIStore } from '@/store/uiStore';
import { Menu, Bell, Search } from 'lucide-react';

export const Header = () => {
  const { user } = useAuthStore();
  const { sidebarOpen, setSidebarOpen } = useUIStore();

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
          <div className="flex items-center gap-3 pl-3 border-l border-void-700">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-mono text-gray-200">{user?.username}</p>
              <p className="text-xs text-gray-500">{user?.roles.map((r) => r.name).join(', ')}</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center text-void-950 font-display font-bold">
              {user?.username?.[0]?.toUpperCase()}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
