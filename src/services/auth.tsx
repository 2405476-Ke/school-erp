/**
 * Authentication Context & Protected Routes
 *
 * Provides:
 * - AuthContext with login/logout functions
 * - useAuth hook to access auth state
 * - Protected route component
 * - Token refresh on app load
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { tokenManager, apiClient } from './api';

// ─── Types ──────────────────────────────────────────────────────────────────

export interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
    school_id: string;
  } | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// ─── Context ────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Provider Component ─────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<AuthContextType['user']>(null);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = () => {
      const token = tokenManager.getToken();

      if (token) {
        // Token exists - assume still valid
        // In production, you might call /auth/me to verify
        setIsAuthenticated(true);

        // Try to get user info from localStorage (set during login)
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      }

      setIsLoading(false);
    };

    initializeAuth();

    // Listen for logout events (from API interceptor on 401)
    const handleLogout = () => {
      handleLogoutInternal();
    };

    window.addEventListener('auth:logout', handleLogout);

    return () => {
      window.removeEventListener('auth:logout', handleLogout);
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);

      // Call backend login endpoint
      const response = await apiClient.post('/auth/login', {
        email,
        password,
      });

      const { access_token, user: userData } = response.data.data;

      // Store token and user
      tokenManager.setToken(access_token);
      tokenManager.setSchoolId(userData.school_id);
      localStorage.setItem('user', JSON.stringify(userData));

      setIsAuthenticated(true);
      setUser(userData);
    } catch (error) {
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogoutInternal = () => {
    tokenManager.clear();
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  const logout = () => {
    handleLogoutInternal();
    // Redirect to login (handled by router)
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── useAuth Hook ───────────────────────────────────────────────────────────

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}

// ─── Protected Route Component ───────────────────────────────────────────────

export interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requiredRole,
  fallback,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return fallback || <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return fallback || <div>Access Denied: Insufficient permissions</div>;
  }

  return <>{children}</>;
}
