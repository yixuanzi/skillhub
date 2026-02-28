import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// API base URL - should be a relative path to use Vite proxy in development
// In production, this can be overridden via environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Helper function to add trailing slash to prevent FastAPI 307 redirects
// FastAPI redirects /path -> /path/ with absolute URL, breaking Vite proxy
const ensureTrailingSlash = (url: string): string => {
  // Don't modify if there are query parameters
  if (url.includes('?')) {
    return url;
  }
  // Don't modify if it already has trailing slash
  if (url.endsWith('/')) {
    return url;
  }
  // Add trailing slash for collection endpoints (common REST pattern)
  // These are the endpoints that typically cause FastAPI redirects
  const collectionPatterns = [
    /\/resources$/,
    /\/acl\/resources$/,
    /\/acl\/rules$/,
    /\/users$/,
    /\/roles$/,
    /\/permissions$/,
    /\/gateways$/,
    /\/mtokens$/,
  ];

  for (const pattern of collectionPatterns) {
    if (pattern.test(url)) {
      return url + '/';
    }
  }

  return url;
};

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate axios instance for token refresh
// This ensures refresh requests also go through the proxy
const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token and handle trailing slashes
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Auto-add trailing slash to prevent FastAPI 307 redirects
    if (config.url) {
      config.url = ensureTrailingSlash(config.url);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Use refreshClient instead of axios to ensure proxy is used
          const response = await refreshClient.post('/auth/refresh', {
            refresh_token: refreshToken,
          });

          // Backend returns access_token (snake_case)
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }

          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Also apply trailing slash logic to refresh client
refreshClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Auto-add trailing slash to prevent FastAPI 307 redirects
    if (config.url) {
      config.url = ensureTrailingSlash(config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default apiClient;
