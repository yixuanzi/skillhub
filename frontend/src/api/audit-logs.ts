import apiClient from './client';
import { ApiResponse } from '@/types';

// Audit Log Types
export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface AuditLogsFilters {
  page?: number;
  size?: number;
  action?: string;
  resource_type?: string;
  user_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface AuditLogsResponse {
  items: AuditLog[];
  total: number;
  page: number;
  size: number;
}

export const auditLogsApi = {
  list: async (filters: AuditLogsFilters = {}): Promise<AuditLogsResponse> => {
    const params = {
      page: filters.page || 1,
      size: filters.size || 20,
      ...(filters.action && { action: filters.action }),
      ...(filters.resource_type && { resource_type: filters.resource_type }),
      ...(filters.user_id && { user_id: filters.user_id }),
      ...(filters.start_date && { start_date: filters.start_date }),
      ...(filters.end_date && { end_date: filters.end_date }),
    };
    const response = await apiClient.get<AuditLogsResponse>('/audit-logs', { params });
    return response.data;
  },

  getById: async (id: string): Promise<ApiResponse<AuditLog>> => {
    const response = await apiClient.get<ApiResponse<AuditLog>>(`/audit-logs/${id}`);
    return response.data;
  },
};
