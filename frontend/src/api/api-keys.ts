import apiClient from './client';

// API Key Types
export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  expires_at: string | null;
  last_used_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface APIKeyCreate {
  name: string;
  scopes: string[];
  expires_at?: string;
}

export interface APIKeyCreateResponse {
  key: string;
  api_key: APIKey;
}

export interface APIKeyUpdate {
  name?: string;
  scopes?: string[];
  expires_at?: string;
  is_active?: boolean;
}

export const apiKeysApi = {
  list: async (params?: { skip?: number; limit?: number }): Promise<APIKey[]> => {
    const response = await apiClient.get<APIKey[]>('/api-keys/', { params });
    return response.data;
  },

  getById: async (id: string): Promise<APIKey> => {
    const response = await apiClient.get<APIKey>(`/api-keys/${id}/`);
    return response.data;
  },

  create: async (data: APIKeyCreate): Promise<APIKeyCreateResponse> => {
    const response = await apiClient.post<APIKeyCreateResponse>('/api-keys/', data);
    return response.data;
  },

  update: async (id: string, data: APIKeyUpdate): Promise<APIKey> => {
    const response = await apiClient.put<APIKey>(`/api-keys/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete<void>(`/api-keys/${id}/`);
  },

  rotate: async (id: string): Promise<APIKeyCreateResponse> => {
    const response = await apiClient.post<APIKeyCreateResponse>(`/api-keys/${id}/rotate/`);
    return response.data;
  },
};
