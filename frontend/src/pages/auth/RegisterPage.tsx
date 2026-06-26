import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegister } from '@/hooks/useAuth';
import { Button, Input, Alert } from '@/components/ui';
import { Box, Clock, CheckCircle } from 'lucide-react';
import type { AxiosError } from 'axios';

interface ApiError {
  detail?: string;
  message?: string;
}

export const RegisterPage = () => {
  const register = useRegister();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      await register.mutateAsync({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      // Registration successful, navigate to login
      // The useRegister hook handles navigation
    } catch (err: unknown) {
      const axiosError = err as AxiosError<ApiError>;
      const message = axiosError.response?.data?.detail
        || axiosError.response?.data?.message
        || axiosError.message
        || 'Registration failed. Please try again.';
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-void-950 bg-grid flex items-center justify-center p-4 scanlines">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyber-secondary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-scale-in">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center mb-4 shadow-lg shadow-cyber-primary/20">
            <Box className="w-8 h-8 text-void-950" />
          </div>
          <h1 className="font-display text-3xl font-bold text-cyber-primary mb-2">SkillHub</h1>
          <p className="font-mono text-sm text-gray-500 uppercase tracking-widest">
            Request System Access
          </p>
        </div>

        <div className="cyber-card rounded-xl border border-void-700 p-8">
          {register.isSuccess ? (
            <div className="space-y-6 text-center animate-fade-in">
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-full bg-cyber-primary/10 border border-cyber-primary/30 flex items-center justify-center">
                  <CheckCircle className="w-7 h-7 text-cyber-primary" />
                </div>
                <h2 className="font-display text-xl font-semibold text-gray-100">
                  Account Created
                </h2>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg border border-cyber-warning/30 bg-cyber-warning/5 text-left">
                <Clock className="w-5 h-5 text-cyber-warning flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-cyber-warning">Pending Activation</p>
                  <p className="text-xs text-gray-400">
                    Your account has been created but is not yet active. Please contact an administrator to activate your account before logging in.
                  </p>
                </div>
              </div>

              <Link to="/login">
                <Button variant="primary" size="lg" className="w-full">
                  Go to Login
                </Button>
              </Link>
            </div>
          ) : (
            <>
              <h2 className="font-display text-xl font-semibold text-gray-100 mb-6">
                Create Account
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
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />

                <Input
                  label="Email"
                  type="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />

                <Input
                  label="Password"
                  type="password"
                  placeholder="Min 8 characters"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />

                <Input
                  label="Confirm Password"
                  type="password"
                  placeholder="Confirm password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  required
                />

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full"
                  disabled={register.isPending}
                >
                  {register.isPending ? 'Creating Account...' : 'Request Access'}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-gray-500">
                  Already have an account?{' '}
                  <Link
                    to="/login"
                    className="text-cyber-primary hover:text-cyber-secondary transition-colors font-mono"
                  >
                    Login
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
