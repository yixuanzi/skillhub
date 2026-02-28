import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourcesApi } from '@/api/resources';
import { ResourceCreate, ResourceUpdate } from '@/types';

export const useResources = (params?: { page?: number; pageSize?: number; resource_type?: string }) => {
  return useQuery({
    queryKey: ['resources', params],
    queryFn: () => resourcesApi.list(params),
  });
};

export const useResource = (id: string) => {
  return useQuery({
    queryKey: ['resource', id],
    queryFn: () => resourcesApi.getById(id),
    enabled: !!id,
  });
};

export const useCreateResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ResourceCreate) => resourcesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};

export const useUpdateResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ResourceUpdate }) =>
      resourcesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};

export const useDeleteResource = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => resourcesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
};
