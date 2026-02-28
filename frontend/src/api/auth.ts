import apiClient from './client';
import { LoginRequest, RegisterRequest } from '@/types';

// Backend token response format (no wrapper)
interface BackendTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Backend refresh response format
interface BackendRefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Backend user response format
interface BackendUserResponse {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<BackendTokenResponse> => {
    const response = await apiClient.post<BackendTokenResponse>('/auth/login/', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<BackendUserResponse> => {
    const response = await apiClient.post<BackendUserResponse>('/auth/register/', data);
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout/', { refresh_token: refreshToken });
  },

  refresh: async (refreshToken: string): Promise<BackendRefreshResponse> => {
    const response = await apiClient.post<BackendRefreshResponse>('/auth/refresh/', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<BackendUserResponse> => {
    const response = await apiClient.get<BackendUserResponse>('/auth/me/');
    return response.data;
  },
};
