import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aclApi } from '@/api/acl';

export const useACLRules = (params?: { page?: number; pageSize?: number; access_mode?: string }) => {
  return useQuery({
    queryKey: ['aclRules', params],
    queryFn: () => aclApi.listRules(params),
  });
};

export const useACLRule = (id: string) => {
  return useQuery({
    queryKey: ['aclRule', id],
    queryFn: () => aclApi.getRuleById(id),
    enabled: !!id,
  });
};

export const useACLRuleByResourceId = (resourceId: string) => {
  return useQuery({
    queryKey: ['aclRule', 'resource', resourceId],
    queryFn: () => aclApi.getRuleByResourceId(resourceId),
    enabled: !!resourceId,
  });
};

export const useCreateACLRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
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
    }) => aclApi.createRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useUpdateACLRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
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
      };
    }) => aclApi.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useDeleteACLRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => aclApi.deleteRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useAddRoleBinding = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: string; data: { role_id: string; permissions: string[] } }) =>
      aclApi.addRoleBinding(ruleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useRemoveRoleBinding = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ruleId, roleId }: { ruleId: string; roleId: string }) =>
      aclApi.removeRoleBinding(ruleId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useUpdateRoleBinding = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ruleId, roleId, permissions }: { ruleId: string; roleId: string; permissions: string[] }) =>
      aclApi.updateRoleBinding(ruleId, roleId, permissions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aclRules'] });
    },
  });
};

export const useCheckPermission = () => {
  return useMutation({
    mutationFn: ({ resourceId, data }: { resourceId: string; data: { user_id: string; required_permission: string; context?: Record<string, unknown> } }) =>
      aclApi.checkPermission(resourceId, data),
  });
};

export const useAuditLogs = (params?: {
  page?: number;
  pageSize?: number;
  resourceId?: string;
  startDate?: string;
  endDate?: string;
}) => {
  return useQuery({
    queryKey: ['auditLogs', params],
    queryFn: () => aclApi.getAuditLogs(params),
  });
};
