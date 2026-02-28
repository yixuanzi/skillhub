import apiClient from './client';
import { Resource, ResourceCreate, ResourceUpdate } from '@/types';

// Backend returns direct Pydantic models, not wrapped in ApiResponse
interface ResourceListResponse {
  items: Resource[];
  total: number;
  page: number;
  size: number;
}

export const resourcesApi = {
  list: async (params?: { page?: number; pageSize?: number; resource_type?: string }): Promise<ResourceListResponse> => {
    const response = await apiClient.get<ResourceListResponse>('/resources/', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Resource> => {
    const response = await apiClient.get<Resource>(`/resources/${id}/`);
    return response.data;
  },

  create: async (data: ResourceCreate): Promise<Resource> => {
    const response = await apiClient.post<Resource>('/resources/', data);
    return response.data;
  },

  update: async (id: string, data: ResourceUpdate): Promise<Resource> => {
    const response = await apiClient.put<Resource>(`/resources/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/resources/${id}/`);
  },
};
