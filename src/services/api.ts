/**
 * Global API Client Configuration
 *
 * Centralized Axios instance with:
 * - Automatic JWT Bearer token injection
 * - Request/response interceptors
 * - Error handling and retry logic
 * - Baseurl from environment
 *
 * Usage:
 *   import { apiClient } from '@/services/api';
 *   const { data } = await apiClient.get('/endpoint');
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// ─── Environment Configuration ──────────────────────────────────────────────────

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// ─── Token Management ──────────────────────────────────────────────────────────

/**
 * Token storage layer - abstracts localStorage usage
 */
export const tokenManager = {
  /**
   * Get JWT token from localStorage
   */
  getToken: (): string | null => {
    return localStorage.getItem('auth_token');
  },

  /**
   * Store JWT token in localStorage
   */
  setToken: (token: string): void => {
    localStorage.setItem('auth_token', token);
  },

  /**
   * Remove JWT token from localStorage
   */
  removeToken: (): void => {
    localStorage.removeItem('auth_token');
  },

  /**
   * Check if token exists
   */
  hasToken: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },

  /**
   * Get school_id from localStorage (set during login)
   */
  getSchoolId: (): string | null => {
    return localStorage.getItem('school_id');
  },

  /**
   * Store school_id in localStorage
   */
  setSchoolId: (schoolId: string): void => {
    localStorage.setItem('school_id', schoolId);
  },

  /**
   * Clear all auth data
   */
  clear: (): void => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('school_id');
    localStorage.removeItem('user_role');
  },
};

// ─── Axios Instance ───────────────────────────────────────────────────────────

/**
 * Create and configure Axios instance
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ─── Request Interceptor ──────────────────────────────────────────────────────

/**
 * Request interceptor: Automatically attach JWT Bearer token to all requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ─── Response Interceptor ─────────────────────────────────────────────────────

/**
 * Response interceptor: Handle errors globally
 *
 * - 401 Unauthorized: Token expired/invalid → logout
 * - 403 Forbidden: User lacks permissions
 * - 500+ Server Error: Show error toast
 * - Network Error: Retry logic
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: number };

    // Handle 401: Unauthorized - redirect to login
    if (error.response?.status === 401) {
      tokenManager.clear();

      // Dispatch logout event that auth guard listens to
      window.dispatchEvent(new CustomEvent('auth:logout', {
        detail: { reason: 'Token expired or invalid' },
      }));

      // Redirect to login page (assuming you have a router)
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }

    // Handle 403: Forbidden
    if (error.response?.status === 403) {
      const errorData = error.response.data as any;
      const errorMessage = errorData?.detail || 'You do not have permission to access this resource';

      // Dispatch permission error event
      window.dispatchEvent(new CustomEvent('api:error', {
        detail: { message: errorMessage, status: 403 },
      }));

      return Promise.reject(error);
    }

    // Retry logic for network errors and 5xx errors
    if (!config._retry) {
      config._retry = 0;
    }

    const isNetworkError = !error.response;
    const isServerError = error.response?.status && error.response.status >= 500;
    const shouldRetry = (isNetworkError || isServerError) && config._retry < 2;

    if (shouldRetry) {
      config._retry += 1;
      const delay = 1000 * Math.pow(2, config._retry - 1); // Exponential backoff: 1s, 2s

      await new Promise(resolve => setTimeout(resolve, delay));

      return apiClient(config);
    }

    // If all retries exhausted or non-retryable error, reject
    return Promise.reject(error);
  }
);

// ─── Error Utilities ──────────────────────────────────────────────────────────

/**
 * Extract error message from API response
 *
 * Backend returns:
 *   {
 *     "detail": "Error message" | [{ "loc": [...], "msg": "..." }]
 *   }
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as any;

    // Handle Pydantic validation errors (list of field errors)
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((err: any) => `${err.loc?.join('.')}: ${err.msg}`)
        .join('\n');
    }

    // Handle single error message
    if (typeof data?.detail === 'string') {
      return data.detail;
    }

    // Handle HTTP status text
    return error.message || `Error ${error.response?.status}`;
  }

  // Handle non-Axios errors
  return error instanceof Error ? error.message : 'An unknown error occurred';
}

/**
 * Type-safe API response wrapper
 *
 * Backend returns:
 *   {
 *     "data": {...},
 *     "message": "...",
 *     "status_code": 200
 *   }
 */
export interface APIResponse<T = any> {
  data: T;
  message: string;
  status_code: number;
}

/**
 * Make a typed GET request
 */
export async function apiGet<T = any>(
  url: string,
  options?: any
): Promise<T> {
  const response = await apiClient.get<APIResponse<T>>(url, options);
  return response.data.data;
}

/**
 * Make a typed POST request
 */
export async function apiPost<T = any>(
  url: string,
  data?: any,
  options?: any
): Promise<T> {
  const response = await apiClient.post<APIResponse<T>>(url, data, options);
  return response.data.data;
}

/**
 * Make a typed PUT request
 */
export async function apiPut<T = any>(
  url: string,
  data?: any,
  options?: any
): Promise<T> {
  const response = await apiClient.put<APIResponse<T>>(url, data, options);
  return response.data.data;
}

/**
 * Make a typed DELETE request
 */
export async function apiDelete<T = any>(
  url: string,
  options?: any
): Promise<T> {
  const response = await apiClient.delete<APIResponse<T>>(url, options);
  return response.data.data;
}

export default apiClient;
