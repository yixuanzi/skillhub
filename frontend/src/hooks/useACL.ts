import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aclApi } from '@/api/acl';

export const useACLRules = (params?: { page?: number; pageSize?: number }) => {
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

export const useCreateACLRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      resourceId: string;
      accessMode: 'any' | 'rbac';
      roles?: string[];
      conditions?: Record<string, unknown>;
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
        accessMode?: 'any' | 'rbac';
        roles?: string[];
        conditions?: Record<string, unknown>;
        enabled?: boolean;
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
