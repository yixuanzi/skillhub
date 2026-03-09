import apiClient from './client';

// Skill Creator Types
export type SkillCreatorType = 'base' | 'sop';

export interface SkillCreatorRequest {
  type: SkillCreatorType;
  resource_id_list?: string[];
  skill_id_list?: string[];
  userinput?: string;
}

export interface SkillCreatorResponse {
  content: string;
}

export const skillCreatorApi = {
  generate: async (request: SkillCreatorRequest): Promise<SkillCreatorResponse> => {
    const response = await apiClient.post<SkillCreatorResponse>('/skill-creator/', request);
    return response.data;
  },
};
