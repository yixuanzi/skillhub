import { NavLink } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { useUIStore } from '@/store/uiStore';
import {
  LayoutDashboard,
  Box,
  Users,
  Database,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/skills', label: 'Skills', icon: Box },
  { path: '/users', label: 'Users', icon: Users },
  { path: '/resources', label: 'Resources', icon: Database },
  { path: '/acl', label: 'ACL Rules', icon: Shield },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-void-900/95 backdrop-blur-sm border-r border-void-700/50 transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b border-void-700/50 px-4">
        {sidebarOpen && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center">
              <span className="font-display font-bold text-void-950">S</span>
            </div>
            <span className="font-display font-semibold text-cyber-primary">SkillHub</span>
          </div>
        )}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-gray-400 hover:text-gray-200 hover:bg-void-800 rounded-lg transition-all"
        >
          {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 p-3">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                'group hover:bg-void-800',
                isActive
                  ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30'
                  : 'text-gray-400 hover:text-gray-200'
              )
            }
          >
            <item.icon className={cn('w-5 h-5 flex-shrink-0', sidebarOpen && 'group-hover:scale-110 transition-transform')} />
            {sidebarOpen && (
              <span className="font-mono text-sm uppercase tracking-wider whitespace-nowrap">
                {item.label}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-void-700/50">
        <button
          onClick={() => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }}
          className={cn(
            'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200',
            'text-gray-400 hover:text-cyber-accent hover:bg-void-800'
          )}
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {sidebarOpen && (
            <span className="font-mono text-sm uppercase tracking-wider">Logout</span>
          )}
        </button>
      </div>
    </aside>
  );
};
