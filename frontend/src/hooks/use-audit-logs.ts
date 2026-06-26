import { useQuery } from '@tanstack/react-query';
import { auditLogsApi, AuditLogsFilters } from '@/api/audit-logs';

export const useAuditLogs = (filters: AuditLogsFilters = {}) => {
  return useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: () => auditLogsApi.list(filters),
  });
};

export const useAuditLog = (id: string) => {
  return useQuery({
    queryKey: ['audit-log', id],
    queryFn: () => auditLogsApi.getById(id),
    enabled: !!id,
  });
};

export const useAuditLogResourceTypes = () => {
  return useQuery({
    queryKey: ['audit-log-resource-types'],
    queryFn: () => auditLogsApi.listResourceTypes(),
    staleTime: 5 * 60 * 1000,
  });
};
