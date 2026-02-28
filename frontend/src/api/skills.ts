import apiClient from './client';
import {
  Skill,
  SkillVersion,
  SkillCreateRequest,
  SkillInvokeRequest,
  SkillInvokeResponse,
  ApiResponse,
  PaginatedResponse,
} from '@/types';

export const skillsApi = {
  list: async (params?: { page?: number; pageSize?: number; type?: string }): Promise<ApiResponse<PaginatedResponse<Skill>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Skill>>>('/skills', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<Skill>> => {
    const response = await apiClient.get<ApiResponse<Skill>>(`/skills/${id}`);
    return response.data;
  },

  create: async (data: SkillCreateRequest): Promise<ApiResponse<Skill>> => {
    const response = await apiClient.post<ApiResponse<Skill>>('/skills', data);
    return response.data;
  },

  update: async (id: string, data: Partial<SkillCreateRequest>): Promise<ApiResponse<Skill>> => {
    const response = await apiClient.put<ApiResponse<Skill>>(`/skills/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/skills/${id}`);
    return response.data;
  },

  build: async (id: string): Promise<ApiResponse<SkillVersion>> => {
    const response = await apiClient.post<ApiResponse<SkillVersion>>(`/skills/${id}/build`);
    return response.data;
  },

  publish: async (id: string, version: string): Promise<ApiResponse<SkillVersion>> => {
    const response = await apiClient.post<ApiResponse<SkillVersion>>(`/skills/${id}/publish`, { version });
    return response.data;
  },

  getVersions: async (id: string): Promise<ApiResponse<SkillVersion[]>> => {
    const response = await apiClient.get<ApiResponse<SkillVersion[]>>(`/skills/${id}/versions`);
    return response.data;
  },

  invoke: async (data: SkillInvokeRequest): Promise<SkillInvokeResponse> => {
    const response = await apiClient.post<SkillInvokeResponse>('/gateway/call', data);
    return response.data;
  },
};
