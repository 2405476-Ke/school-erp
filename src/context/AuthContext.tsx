/**
 * Authentication Context & State Management
 *
 * Provides:
 * - AuthContext with isAuthenticated, user, login(), logout()
 * - useAuth hook for accessing auth state in components
 * - Automatic token refresh on app load
 * - Listeners for 401 unauthorized responses
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiPost } from '@/services/api';
import { tokenManager } from '@/services/api';
import type { User, LoginRequest, LoginResponse } from '@/types/api';

// ─── Type Definitions ───────────────────────────────────────────────────────

export interface AuthContextType {
  /**
   * Whether user is currently authenticated
   */
  isAuthenticated: boolean;

  /**
   * Loading state (checking auth on app load)
   */
  isLoading: boolean;

  /**
   * Current logged-in user
   */
  user: User | null;

  /**
   * Login with email and password
   * Stores token and user in localStorage
   */
  login: (email: string, password: string) => Promise<void>;

  /**
   * Logout and clear auth data
   */
  logout: () => void;
}

// ─── Context Creation ───────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Provider Component ─────────────────────────────────────────────────────

export interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider component - wrap your entire app with this
 *
 * Usage:
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // ─── Initialize auth on app load ───────────────────────────────────────

  useEffect(() => {
    const initializeAuth = () => {
      try {
        const token = tokenManager.getToken();
        const storedUser = localStorage.getItem('user');

        if (token && storedUser) {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // ─── Listen for 401 unauthorized events ────────────────────────────────

    const handleUnauthorized = () => {
      handleLogout();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  // ─── Login function ────────────────────────────────────────────────────

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);

      const payload: LoginRequest = { email, password };
      const response = await apiPost<LoginResponse>('/auth/login', payload);

      const { access_token, user: userData } = response;

      // Store token and user in localStorage
      tokenManager.setToken(access_token);
      localStorage.setItem('school_id', userData.school_id);
      localStorage.setItem('user', JSON.stringify(userData));

      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // ─── Logout function ───────────────────────────────────────────────────

  const handleLogout = () => {
    tokenManager.clear();
    setIsAuthenticated(false);
    setUser(null);
  };

  const logout = () => {
    handleLogout();
    // Redirect to login page
    window.location.href = '/login';
  };

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ─── useAuth Hook ──────────────────────────────────────────────────────────

/**
 * Hook to access auth context in any component
 *
 * Usage:
 *   const { isAuthenticated, user, logout } = useAuth();
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
