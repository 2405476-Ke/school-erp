/**
 * Global API Client Configuration
 *
 * Centralized Axios instance with:
 * - Automatic JWT Bearer token injection via Request Interceptor
 * - Response error handling (401, 403, 500+)
 * - Exponential backoff retry for network errors
 *
 * Usage:
 *   import { apiClient, apiGet, apiPost } from '@/services/api';
 *   const data = await apiGet('/endpoint');
 *   const result = await apiPost('/endpoint', { payload });
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { APIResponse } from '@/types/api';

// ─── Configuration ──────────────────────────────────────────────────────────

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// ─── Token Manager ──────────────────────────────────────────────────────────

/**
 * Manage JWT token storage in localStorage
 */
export const tokenManager = {
  getToken: (): string | null => localStorage.getItem('auth_token'),
  setToken: (token: string): void => localStorage.setItem('auth_token', token),
  removeToken: (): void => localStorage.removeItem('auth_token'),
  hasToken: (): boolean => !!localStorage.getItem('auth_token'),
  clear: (): void => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('school_id');
    localStorage.removeItem('user');
  },
};

// ─── Axios Instance ──────────────────────────────────────────────────────────

/**
 * Create and configure Axios instance
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ─── REQUEST INTERCEPTOR ────────────────────────────────────────────────────

/**
 * Automatically attach JWT Bearer token to all requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ─── RESPONSE INTERCEPTOR ───────────────────────────────────────────────────

/**
 * Handle API errors globally:
 * - 401: Clear token and redirect to /login
 * - 403: Dispatch permission error event
 * - 5xx + Network: Retry with exponential backoff
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: number };

    // ─── 401 Unauthorized: Token invalid/expired ────────────────────────────

    if (error.response?.status === 401) {
      tokenManager.clear();

      // Dispatch event for auth context to listen
      window.dispatchEvent(
        new CustomEvent('auth:unauthorized', {
          detail: { reason: 'Token expired or invalid' },
        })
      );

      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }

    // ─── 403 Forbidden: Permission denied ────────────────────────────────────

    if (error.response?.status === 403) {
      const errorData = error.response.data as any;
      const message = errorData?.detail || 'You do not have permission for this action';

      window.dispatchEvent(
        new CustomEvent('api:forbidden', {
          detail: { message, status: 403 },
        })
      );

      return Promise.reject(error);
    }

    // ─── Retry logic for 5xx and network errors ────────────────────────────

    if (!config._retry) {
      config._retry = 0;
    }

    const isNetworkError = !error.response;
    const isServerError = error.response?.status && error.response.status >= 500;
    const shouldRetry = (isNetworkError || isServerError) && config._retry < 2;

    if (shouldRetry) {
      config._retry += 1;
      const delayMs = 1000 * Math.pow(2, config._retry - 1); // 1s, 2s

      await new Promise(resolve => setTimeout(resolve, delayMs));
      return apiClient(config);
    }

    return Promise.reject(error);
  }
);

// ─── TYPE-SAFE API FUNCTIONS ────────────────────────────────────────────────

/**
 * Type-safe GET request
 */
export async function apiGet<T = any>(url: string, options?: any): Promise<T> {
  const response = await apiClient.get<APIResponse<T>>(url, options);
  return response.data.data;
}

/**
 * Type-safe POST request
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
 * Type-safe PUT request
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
 * Type-safe DELETE request
 */
export async function apiDelete<T = any>(url: string, options?: any): Promise<T> {
  const response = await apiClient.delete<APIResponse<T>>(url, options);
  return response.data.data;
}

export default apiClient;
