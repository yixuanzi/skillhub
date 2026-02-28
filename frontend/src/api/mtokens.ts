import apiClient from './client';

// MToken Types
export interface MToken {
  id: string;
  app_name: string;
  key_name: string;
  value: string;
  desc?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface MTokenCreate {
  app_name: string;
  key_name: string;
  value: string;
  desc?: string;
}

export interface MTokenUpdate {
  app_name?: string;
  key_name?: string;
  value?: string;
  desc?: string;
}

export interface MTokenListResponse {
  items: MToken[];
  total: number;
  page: number;
  size: number;
}

export const mtokensApi = {
  listTokens: async (params?: {
    page?: number;
    size?: number;
    app_name?: string;
  }): Promise<MTokenListResponse> => {
    const response = await apiClient.get<MTokenListResponse>('/mtokens/', { params });
    return response.data;
  },

  getTokenById: async (id: string): Promise<MToken> => {
    const response = await apiClient.get<MToken>(`/mtokens/${id}/`);
    return response.data;
  },

  createToken: async (data: MTokenCreate): Promise<MToken> => {
    const response = await apiClient.post<MToken>('/mtokens/', data);
    return response.data;
  },

  updateToken: async (id: string, data: MTokenUpdate): Promise<MToken> => {
    const response = await apiClient.put<MToken>(`/mtokens/${id}/`, data);
    return response.data;
  },

  deleteToken: async (id: string): Promise<void> => {
    await apiClient.delete(`/mtokens/${id}/`);
  },
};
