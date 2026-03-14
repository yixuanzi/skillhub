import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLogin } from '@/hooks/useAuth';
import { Button, Input, Alert } from '@/components/ui';
import { Box } from 'lucide-react';
import type { AxiosError } from 'axios';

interface ApiError {
  detail?: string;
  message?: string;
}

export const LoginPage = () => {
  const login = useLogin();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login.mutateAsync(formData);
    } catch (err: unknown) {
      const axiosError = err as AxiosError<ApiError>;
      const message = axiosError.response?.data?.detail
        || axiosError.response?.data?.message
        || axiosError.message
        || 'Login failed. Please check your credentials.';
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-void-950 bg-grid flex items-center justify-center p-4 scanlines">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyber-secondary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-scale-in">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center mb-4 shadow-lg shadow-cyber-primary/20">
            <Box className="w-8 h-8 text-void-950" />
          </div>
          <h1 className="font-display text-3xl font-bold text-cyber-primary mb-2">SkillHub</h1>
          <p className="font-mono text-sm text-gray-500 uppercase tracking-widest">
            Enterprise Skill Ecosystem
          </p>
        </div>

        {/* Login Card */}
        <div className="cyber-card rounded-xl border border-void-700 p-8">
          <h2 className="font-display text-xl font-semibold text-gray-100 mb-6">
            System Access
          </h2>

          {error && (
            <Alert variant="danger" className="mb-6">
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Username"
              type="text"
              placeholder="Enter your username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              disabled={login.isPending}
            >
              {login.isPending ? 'Authenticating...' : 'Access System'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-cyber-primary hover:text-cyber-secondary transition-colors font-mono"
              >
                Request Access
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-600 font-mono">
            v1.3.0 | Start with 2026.02.28 | Build 2026.03.14
          </p>
        </div>
      </div>
    </div>
  );
};
