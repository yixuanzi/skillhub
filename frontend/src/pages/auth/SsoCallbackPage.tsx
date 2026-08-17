import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { AxiosError } from 'axios';
import { Alert, Loading } from '@/components/ui';
import { authApi } from '@/api/auth';
import { mapBackendUser } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';

interface ApiError {
  detail?: string;
}

export const SsoCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [error, setError] = useState('');

  useEffect(() => {
    const providerError = searchParams.get('error');
    const providerDescription = searchParams.get('error_description');
    if (providerError) {
      setError(providerDescription || `Portal OIDC 登录失败：${providerError}`);
      return;
    }

    let cancelled = false;
    const completeLogin = async () => {
      try {
        const tokens = await authApi.exchangeSsoTicket();
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        const response = await authApi.getCurrentUser();
        if (cancelled) return;
        setAuth(
          mapBackendUser(response),
          tokens.access_token,
          tokens.refresh_token
        );
        navigate('/dashboard', { replace: true });
      } catch (err: unknown) {
        if (cancelled) return;
        const axiosError = err as AxiosError<ApiError>;
        setError(
          axiosError.response?.data?.detail
            || axiosError.message
            || 'SkillHub OIDC 登录票据无效或已过期。'
        );
      }
    };

    void completeLogin();
    return () => {
      cancelled = true;
    };
  }, [navigate, searchParams, setAuth]);

  return (
    <div className="min-h-screen bg-void-950 bg-grid flex items-center justify-center p-4">
      <div className="cyber-card rounded-xl border border-void-700 p-8 w-full max-w-md text-center">
        {error ? (
          <Alert variant="danger" className="text-left">
            {error}
          </Alert>
        ) : (
          <>
            <Loading size="lg" />
            <p className="mt-4 font-mono text-sm text-gray-400">
              正在完成 Aegis Portal OIDC 登录…
            </p>
          </>
        )}
        {error && (
          <button
            type="button"
            className="mt-6 font-mono text-sm text-cyber-primary hover:text-cyber-secondary"
            onClick={() => navigate('/login', { replace: true })}
          >
            返回 SkillHub 登录页
          </button>
        )}
      </div>
    </div>
  );
};
