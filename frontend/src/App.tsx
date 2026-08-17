import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { LoginPage, RegisterPage, SsoCallbackPage } from './pages/auth';
import { DashboardPage } from './pages/dashboard';
import { SkillsPage, SkillDetailPage, SkillCreatePage, SkillEditPage } from './pages/skills';
import { UsersPage } from './pages/users';
import { ResourcesPage } from './pages/resources';
import { TokensPage } from './pages/tokens';
import { ACLPage } from './pages/acl';
import { SettingsPage } from './pages/settings/SettingsPage';
import { UserManualPage } from './pages/settings/UserManualPage';
import { useAuthStore } from './store/authStore';
import { ApiConfigDebug } from './components/debug/ApiConfigDebug';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const token = localStorage.getItem('access_token');
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const organizationId = params.get('organization_id');
  const clientId = params.get('client_id');

  if (location.pathname === '/' && organizationId && clientId) {
    return <PortalLaunchRedirect organizationId={organizationId} clientId={clientId} />;
  }

  if (!isAuthenticated && !token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const PortalLaunchRedirect = ({ organizationId, clientId }: { organizationId: string; clientId: string }) => {
  const launchQuery = new URLSearchParams({ organization_id: organizationId, client_id: clientId }).toString();

  useEffect(() => {
    window.location.replace(`/api/v1/sso/start?${launchQuery}`);
  }, [launchQuery]);

  return (
    <div className="min-h-screen bg-void-950 bg-grid flex items-center justify-center p-4">
      <p className="font-mono text-sm text-gray-400">正在跳转到 Aegis Portal…</p>
    </div>
  );
};

const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const token = localStorage.getItem('access_token');

  if (!isAuthenticated && !token) {
    return <Navigate to="/login" replace />;
  }

  // Check if user has admin or super_admin role
  const isAdmin = user?.roles?.some(role => role.name === 'admin' || role.name === 'super_admin') ?? false;

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const token = localStorage.getItem('access_token');

  if (isAuthenticated || token) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Debug component - shows API configuration in console */}
      <ApiConfigDebug />

      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />
          <Route path="/sso/callback" element={<SsoCallbackPage />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="skills/new" element={<SkillCreatePage />} />
            <Route path="skills/:id/edit" element={<SkillEditPage />} />
            <Route path="skills/:id" element={<SkillDetailPage />} />
            <Route
              path="users"
              element={
                <AdminRoute>
                  <UsersPage />
                </AdminRoute>
              }
            />
            <Route path="resources" element={<ResourcesPage />} />
            <Route path="tokens" element={<TokensPage />} />
            <Route path="acl" element={<ACLPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="user-manual" element={<UserManualPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
