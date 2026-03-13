import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/utils/cn';

export const Layout = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-void-950 bg-grid">
      <Sidebar />
      <div
        className={cn(
          'transition-all duration-300',
          sidebarOpen ? 'ml-64 lg:ml-64' : 'ml-20 lg:ml-20'
        )}
      >
        <Header />
        <main className="p-6" style={{ transform: 'scale(0.9)', transformOrigin: 'top left' }}>
          <div style={{ width: '111.11%' }}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
