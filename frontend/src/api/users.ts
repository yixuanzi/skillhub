import apiClient from './client';
import { User, Role, ApiResponse, PaginatedResponse } from '@/types';

export const usersApi = {
  list: async (params?: { page?: number; pageSize?: number }): Promise<ApiResponse<PaginatedResponse<User>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<User>>>('/users', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<User>> => {
    const response = await apiClient.get<ApiResponse<User>>(`/users/${id}`);
    return response.data;
  },

  create: async (data: { username: string; email: string; password: string; roleIds?: string[] }): Promise<ApiResponse<User>> => {
    const response = await apiClient.post<ApiResponse<User>>('/users', data);
    return response.data;
  },

  update: async (id: string, data: { username?: string; email?: string; roleIds?: string[] }): Promise<ApiResponse<User>> => {
    const response = await apiClient.put<ApiResponse<User>>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/users/${id}`);
    return response.data;
  },
};

export const rolesApi = {
  list: async (): Promise<ApiResponse<Role[]>> => {
    const response = await apiClient.get<ApiResponse<Role[]>>('/roles');
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<Role>> => {
    const response = await apiClient.get<ApiResponse<Role>>(`/roles/${id}`);
    return response.data;
  },

  create: async (data: { name: string; permissions?: Array<{ resource: string; action: string }> }): Promise<ApiResponse<Role>> => {
    const response = await apiClient.post<ApiResponse<Role>>('/roles', data);
    return response.data;
  },

  update: async (id: string, data: { name?: string; permissions?: Array<{ resource: string; action: string }> }): Promise<ApiResponse<Role>> => {
    const response = await apiClient.put<ApiResponse<Role>>(`/roles/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/roles/${id}`);
    return response.data;
  },

  assignPermissions: async (id: string, permissions: Array<{ resource: string; action: string }>): Promise<ApiResponse<Role>> => {
    const response = await apiClient.post<ApiResponse<Role>>(`/roles/${id}/permissions`, { permissions });
    return response.data;
  },
};
