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
      const params = new URLSearchParams();
      if (filters.page) params.append('page', String(filters.page));
      if (filters.size) params.append('size', String(filters.size));
      if (filters.search) params.append('search', filters.search);
      if (filters.role_id) params.append('role_id', filters.role_id);

      const response = await apiClient.get<UserListResponse>(`/users/?${params.toString()}`);
      return response.data;
    },
  });
};

export const useUser = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await apiClient.get<User>(`/users/${userId}/`);
      return response.data;
    },
    enabled: !!userId,
  });
};

export const useAssignRoles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, roleIds }: { userId: string; roleIds: string[] }) =>
      apiClient.put<User>(`/users/${userId}/roles/`, { role_ids: roleIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useDeactivateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.put<User>(`/users/${userId}/deactivate/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useRoles = () => {
  return useQuery({
    queryKey: ['roles'],
    queryFn: async () => {
      const response = await apiClient.get<Role[]>('/users/roles/');
      return response.data;
    },
  });
};
