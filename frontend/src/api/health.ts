/**
 * Health Check API
 *
 * Provides access to system health information including SKILLHUB_URL.
 */

import apiClient from './client';

export interface HealthResponse {
  status: string;
  version: string;
  message: string;
  SKILLHUB_URL: string;
}

/**
 * Get system health information
 *
 * Returns the current health status and configuration including the SKILLHUB_URL.
 */
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/script/health/');
  return data;
};
