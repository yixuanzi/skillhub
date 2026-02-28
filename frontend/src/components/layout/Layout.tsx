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
          sidebarOpen ? 'lg:ml-64' : 'lg:ml-20'
        )}
      >
        <Header />
        <main className="p-6 scanlines">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
