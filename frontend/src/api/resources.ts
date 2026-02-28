import apiClient from './client';
import { Resource, ResourceCreate, ResourceUpdate, ApiResponse, PaginatedResponse } from '@/types';

export const resourcesApi = {
  list: async (params?: { page?: number; pageSize?: number; resource_type?: string }): Promise<ApiResponse<PaginatedResponse<Resource>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Resource>>>('/resources', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.get<ApiResponse<Resource>>(`/resources/${id}`);
    return response.data;
  },

  create: async (data: ResourceCreate): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.post<ApiResponse<Resource>>('/resources', data);
    return response.data;
  },

  update: async (id: string, data: ResourceUpdate): Promise<ApiResponse<Resource>> => {
    const response = await apiClient.put<ApiResponse<Resource>>(`/resources/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/resources/${id}`);
    return response.data;
  },
};
