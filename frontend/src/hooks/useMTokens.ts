import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mtokensApi } from '@/api/mtokens';

export const useMTokens = (params?: { page?: number; size?: number; app_name?: string }) => {
  return useQuery({
    queryKey: ['mtokens', params],
    queryFn: () => mtokensApi.listTokens(params),
  });
};

export const useMToken = (id: string) => {
  return useQuery({
    queryKey: ['mtoken', id],
    queryFn: () => mtokensApi.getTokenById(id),
    enabled: !!id,
  });
};

export const useCreateMToken = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      app_name: string;
      key_name: string;
      value: string;
      desc?: string;
    }) => mtokensApi.createToken(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mtokens'] });
    },
  });
};

export const useUpdateMToken = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: {
        app_name?: string;
        key_name?: string;
        value?: string;
        desc?: string;
      };
    }) => mtokensApi.updateToken(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mtokens'] });
    },
  });
};

export const useDeleteMToken = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => mtokensApi.deleteToken(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mtokens'] });
    },
  });
};
