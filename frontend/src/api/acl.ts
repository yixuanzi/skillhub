import apiClient from './client';
import { ACLRule, AuditLog } from '@/types';

// Backend returns direct Pydantic models, not wrapped in ApiResponse
interface ACLRuleListResponse {
  items: ACLRule[];
  total: number;
  page: number;
  size: number;
}

interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  size: number;
}

export const aclApi = {
  listRules: async (params?: { page?: number; pageSize?: number; access_mode?: string }): Promise<ACLRuleListResponse> => {
    const response = await apiClient.get<ACLRuleListResponse>('/acl/resources/', { params });
    return response.data;
  },

  getRuleById: async (id: string): Promise<ACLRule> => {
    const response = await apiClient.get<ACLRule>(`/acl/resources/${id}/`);
    return response.data;
  },

  getRuleByResourceId: async (resourceId: string): Promise<ACLRule> => {
    const response = await apiClient.get<ACLRule>(`/acl/resources/resource/${resourceId}/`);
    return response.data;
  },

  createRule: async (data: {
    resource_id: string;
    resource_name: string;
    access_mode: 'any' | 'rbac';
    role_bindings?: Array<{ role_id: string; permissions: string[] }>;
    conditions?: {
      users?: string[];
      roles?: string[];
      ip_whitelist?: string[];
      rate_limit?: { requests: number; window: number };
      time_windows?: Array<{ start: string; end: string }>;
      metadata?: Record<string, unknown>;
    };
  }): Promise<ACLRule> => {
    const response = await apiClient.post<ACLRule>('/acl/resources/', data);
    return response.data;
  },

  updateRule: async (
    id: string,
    data: {
      access_mode?: 'any' | 'rbac';
      conditions?: {
        users?: string[];
        roles?: string[];
        ip_whitelist?: string[];
        rate_limit?: { requests: number; window: number };
        time_windows?: Array<{ start: string; end: string }>;
        metadata?: Record<string, unknown>;
      };
    }
  ): Promise<ACLRule> => {
    const response = await apiClient.put<ACLRule>(`/acl/resources/${id}/`, data);
    return response.data;
  },

  deleteRule: async (id: string): Promise<void> => {
    await apiClient.delete(`/acl/resources/${id}/`);
  },

  // Role binding operations
  addRoleBinding: async (ruleId: string, data: { role_id: string; permissions: string[] }) => {
    const response = await apiClient.post(`/acl/resources/${ruleId}/role-bindings/`, data);
    return response.data;
  },

  removeRoleBinding: async (ruleId: string, roleId: string): Promise<void> => {
    await apiClient.delete(`/acl/resources/${ruleId}/role-bindings/${roleId}/`);
  },

  updateRoleBinding: async (ruleId: string, roleId: string, permissions: string[]) => {
    const response = await apiClient.put(`/acl/resources/${ruleId}/role-bindings/${roleId}/`, permissions);
    return response.data;
  },

  // Permission check
  checkPermission: async (resourceId: string, data: { user_id: string; required_permission: string; context?: Record<string, unknown> }) => {
    const response = await apiClient.post(`/acl/resources/check-permission/${resourceId}/`, data);
    return response.data;
  },

  getAuditLogs: async (params?: {
    page?: number;
    pageSize?: number;
    resourceId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<AuditLogListResponse> => {
    const response = await apiClient.get<AuditLogListResponse>('/acl/audit-logs/', { params });
    return response.data;
  },
};
