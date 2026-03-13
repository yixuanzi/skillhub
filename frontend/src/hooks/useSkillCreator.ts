import { useMutation } from '@tanstack/react-query';
import { skillCreatorApi, SkillCreatorRequest } from '@/api/skillCreator';

export const useSkillCreator = () => {
  return useMutation({
    mutationFn: (request: SkillCreatorRequest) => skillCreatorApi.generate(request),
  });
};
