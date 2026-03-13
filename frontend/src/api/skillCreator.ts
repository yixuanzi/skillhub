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
  context_conf?: string;
}

export const skillCreatorApi = {
  generate: async (request: SkillCreatorRequest): Promise<SkillCreatorResponse> => {
    // AI skill generation may take longer (up to 5 minutes)
    const response = await apiClient.post<SkillCreatorResponse>('/skill-creator/', request, {
      timeout: 300000, // 5 minutes for AI generation
    });
    return response.data;
  },
};
