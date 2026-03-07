import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  roles: Array<{ id: string; name: string; description?: string }>;
  created_at: string;
}

interface Role {
  id: string;
  name: string;
  description?: string;
}

interface UserListResponse {
  items: User[];
  total: number;
  page: number;
  size: number;
}

interface UserFilters {
  page?: number;
  size?: number;
  search?: string;
  role_id?: string;
}

export const useUsers = (filters: UserFilters = {}) => {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: async () => {
      // Backend uses /admin/users/list path
      const params = new URLSearchParams();
      if (filters.page) params.append('page', String(filters.page));
      if (filters.size) params.append('size', String(filters.size));
      if (filters.search) params.append('search', filters.search);
      if (filters.role_id) params.append('role_id', filters.role_id);

      const queryString = params.toString();
      const response = await apiClient.get<UserListResponse>(`/admin/users/list/${queryString ? `?${queryString}` : ''}`);
      return response.data;
    },
  });
};

export const useUser = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await apiClient.get<User>(`/admin/users/${userId}/`);
      return response.data;
    },
    enabled: !!userId,
  });
};

export const useAssignRoles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleIds }: { userId: string; roleIds: string[] }) =>
      apiClient.put<User>(`/admin/users/${userId}/roles/`, { role_ids: roleIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useDeactivateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      apiClient.put<User>(`/admin/users/${userId}/`, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useRoles = () => {
  return useQuery({
    queryKey: ['roles'],
    queryFn: async () => {
      // Backend uses /admin/roles/list path
      const response = await apiClient.get<Role[]>('/admin/roles/list/');
      return response.data;
    },
  });
};
