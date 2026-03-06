import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiKeysApi, APIKey, APIKeyCreate, APIKeyUpdate } from '@/api/api-keys';

export const useAPIKeys = (params?: { skip?: number; limit?: number }) => {
  return useQuery<APIKey[]>({
    queryKey: ['api-keys', params],
    queryFn: () => apiKeysApi.list(params),
  });
};

export const useAPIKey = (id: string) => {
  return useQuery<APIKey>({
    queryKey: ['api-key', id],
    queryFn: () => apiKeysApi.getById(id),
    enabled: !!id,
  });
};

export const useCreateAPIKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: APIKeyCreate) => apiKeysApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useUpdateAPIKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: APIKeyUpdate }) =>
      apiKeysApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useRevokeAPIKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useRotateAPIKey = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.rotate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};
