import { useMutation, useQuery } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import { LoginRequest, RegisterRequest, User } from '@/types';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';

export const useLogin = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (tokens) => {
      // Backend returns: { access_token, refresh_token, token_type, expires_in }
      const { access_token, refresh_token } = tokens;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Set minimal auth state, will fetch full user info
      setAuth(
        { id: '', username: '', email: '', roles: [], createdAt: '', updatedAt: '' },
        access_token,
        refresh_token
      );
      navigate('/dashboard');
    },
  });
};

export const useRegister = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: () => {
      // Backend returns user info, but no tokens
      // Navigate to login with success message
      navigate('/login');
    },
  });
};

export const useLogout = () => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  return useMutation({
    mutationFn: () => {
      const refreshToken = localStorage.getItem('refresh_token') || '';
      return authApi.logout(refreshToken);
    },
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      logout();
      navigate('/login');
    },
  });
};

export const useCurrentUser = () => {
  const setUser = useAuthStore((state) => state.setUser);

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await authApi.getCurrentUser();
      // Backend returns: { id, username, email, is_active, created_at }
      const user: User = {
        id: response.id,
        username: response.username,
        email: response.email,
        roles: [], // Will be populated when we implement roles
        createdAt: response.created_at,
        updatedAt: response.created_at,
      };
      setUser(user);
      return user;
    },
    retry: false,
  });
};
