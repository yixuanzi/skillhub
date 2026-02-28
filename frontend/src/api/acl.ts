import apiClient from './client';
import { ACLRule, AuditLog, ApiResponse, PaginatedResponse } from '@/types';

export const aclApi = {
  listRules: async (params?: { page?: number; pageSize?: number }): Promise<ApiResponse<PaginatedResponse<ACLRule>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<ACLRule>>>('/acl/rules', { params });
    return response.data;
  },

  getRuleById: async (id: string): Promise<ApiResponse<ACLRule>> => {
    const response = await apiClient.get<ApiResponse<ACLRule>>(`/acl/rules/${id}`);
    return response.data;
  },

  createRule: async (data: {
    resourceId: string;
    accessMode: 'any' | 'rbac';
    roles?: string[];
    conditions?: Record<string, unknown>;
  }): Promise<ApiResponse<ACLRule>> => {
    const response = await apiClient.post<ApiResponse<ACLRule>>('/acl/rules', data);
    return response.data;
  },

  updateRule: async (
    id: string,
    data: {
      accessMode?: 'any' | 'rbac';
      roles?: string[];
      conditions?: Record<string, unknown>;
      enabled?: boolean;
    }
  ): Promise<ApiResponse<ACLRule>> => {
    const response = await apiClient.put<ApiResponse<ACLRule>>(`/acl/rules/${id}`, data);
    return response.data;
  },

  deleteRule: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/acl/rules/${id}`);
    return response.data;
  },

  getAuditLogs: async (params?: {
    page?: number;
    pageSize?: number;
    resourceId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<ApiResponse<PaginatedResponse<AuditLog>>> => {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<AuditLog>>>('/acl/audit-logs', { params });
    return response.data;
  },
};
