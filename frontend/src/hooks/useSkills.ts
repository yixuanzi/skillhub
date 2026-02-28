import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { skillsApi } from '@/api/skills';
import { SkillCreateRequest, SkillUpdateRequest, SkillInvokeRequest } from '@/types';

export const useSkills = (params?: { page?: number; pageSize?: number; category?: string; tags?: string; author?: string }) => {
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
    mutationFn: ({ id, data }: { id: string; data: SkillUpdateRequest }) =>
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

export const useInvokeSkill = () => {
  return useMutation({
    mutationFn: (data: SkillInvokeRequest) => skillsApi.invoke(data),
  });
};
