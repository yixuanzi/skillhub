import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { skillsApi } from '@/api/skills';
import { SkillCreateRequest, SkillInvokeRequest } from '@/types';

export const useSkills = (params?: { page?: number; pageSize?: number; type?: string }) => {
  return useQuery({
    queryKey: ['skills', params],
    queryFn: () => skillsApi.list(params),
  });
};

export const useSkill = (id: string) => {
  return useQuery({
    queryKey: ['skill', id],
    queryFn: () => skillsApi.getById(id),
    enabled: !!id,
  });
};

export const useSkillVersions = (id: string) => {
  return useQuery({
    queryKey: ['skillVersions', id],
    queryFn: () => skillsApi.getVersions(id),
    enabled: !!id,
  });
};

export const useCreateSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SkillCreateRequest) => skillsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
};

export const useUpdateSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SkillCreateRequest> }) =>
      skillsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['skill', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
};

export const useDeleteSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => skillsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
};

export const useBuildSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => skillsApi.build(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['skillVersions', variables] });
      queryClient.invalidateQueries({ queryKey: ['skill', variables] });
    },
  });
};

export const usePublishSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, version }: { id: string; version: string }) =>
      skillsApi.publish(id, version),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['skillVersions', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['skill', variables.id] });
    },
  });
};

export const useInvokeSkill = () => {
  return useMutation({
    mutationFn: (data: SkillInvokeRequest) => skillsApi.invoke(data),
  });
};
