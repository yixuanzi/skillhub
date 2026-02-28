import apiClient from './client';
import {
  Skill,
  SkillVersion,
  SkillCreateRequest,
  SkillUpdateRequest,
  SkillInvokeRequest,
  SkillInvokeResponse,
} from '@/types';

// Backend returns direct Pydantic models
interface SkillListResponse {
  items: Skill[];
  total: number;
  page: number;
  size: number;
}

export const skillsApi = {
  list: async (params?: { page?: number; pageSize?: number; category?: string; tags?: string; author?: string }): Promise<SkillListResponse> => {
    const response = await apiClient.get<SkillListResponse>('/skills/', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Skill> => {
    const response = await apiClient.get<Skill>(`/skills/${id}/`);
    return response.data;
  },

  create: async (data: SkillCreateRequest): Promise<Skill> => {
    const response = await apiClient.post<Skill>('/skills/', data);
    return response.data;
  },

  update: async (id: string, data: SkillUpdateRequest): Promise<Skill> => {
    const response = await apiClient.put<Skill>(`/skills/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/skills/${id}/`);
  },

  getVersions: async (id: string): Promise<SkillVersion[]> => {
    const response = await apiClient.get<SkillVersion[]>(`/skills/${id}/versions/`);
    return response.data;
  },

  invoke: async (data: SkillInvokeRequest): Promise<SkillInvokeResponse> => {
    const response = await apiClient.post<SkillInvokeResponse>('/gateway/call/', data);
    return response.data;
  },
};
