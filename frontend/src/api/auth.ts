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
interface BackendPermissionResponse {
  id: string;
  resource: string;
  action: string;
  description?: string;
}

interface BackendRoleResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  permissions: BackendPermissionResponse[];
}

interface BackendUserResponse {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  roles: BackendRoleResponse[];
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

  updateCurrentUser: async (data: { username?: string; email?: string }): Promise<BackendUserResponse> => {
    const response = await apiClient.put<BackendUserResponse>('/auth/me/', data);
    return response.data;
  },

  changePassword: async (data: { old_password: string; new_password: string }): Promise<void> => {
    await apiClient.post('/auth/change-password/', data);
  },
};
