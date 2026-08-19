/**
 * Protected Route Component
 *
 * Wraps routes to require authentication
 * - Checks if user is logged in
 * - Redirects to login if not authenticated
 * - Can enforce role-based access control
 *
 * Usage:
 *   <ProtectedRoute>
 *     <DashboardPage />
 *   </ProtectedRoute>
 *
 *   <ProtectedRoute requiredRole="PRINCIPAL">
 *     <PrincipalOnlyPage />
 *   </ProtectedRoute>
 */

import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import type { UserRole } from '@/types/api';

export interface ProtectedRouteProps {
  /**
   * Component(s) to render if authenticated
   */
  children: ReactNode;

  /**
   * Optional role requirement
   * If specified, only users with this role can access
   */
  requiredRole?: UserRole;

  /**
   * Component to show while loading
   * Defaults to "Loading..."
   */
  fallback?: ReactNode;
}

/**
 * ProtectedRoute Component
 *
 * Checks authentication state and optionally enforces role-based access
 */
export function ProtectedRoute({
  children,
  requiredRole,
  fallback,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // ─── Loading state ──────────────────────────────────────────────────

  if (isLoading) {
    return fallback || <LoadingFallback />;
  }

  // ─── Not authenticated: redirect to login ──────────────────────────

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // ─── Role-based access control ─────────────────────────────────────

  if (requiredRole && user?.role !== requiredRole) {
    return <AccessDeniedFallback userRole={user?.role} />;
  }

  // ─── Authenticated and authorized: render children ─────────────────

  return <>{children}</>;
}

// ─── Fallback Components ────────────────────────────────────────────────────

/**
 * Default loading fallback
 */
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[#F3EFE4]">
      <div className="text-center">
        <div className="inline-block animate-spin">
          <svg
            className="h-8 w-8 text-[#1F6F4A]"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <p className="mt-4 font-['IBM_Plex_Sans'] text-[#16241D]">
          Loading...
        </p>
      </div>
    </div>
  );
}

/**
 * Access denied fallback
 */
interface AccessDeniedFallbackProps {
  userRole?: string;
}

function AccessDeniedFallback({ userRole }: AccessDeniedFallbackProps) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[#F3EFE4]">
      <div className="bg-white rounded-lg border border-[#DCD6C4] p-8 text-center max-w-md">
        <h1 className="text-2xl font-bold font-['Fraunces'] text-[#9C3B2E] mb-4">
          Access Denied
        </h1>
        <p className="font-['IBM_Plex_Sans'] text-[#16241D] mb-2">
          You do not have permission to access this page.
        </p>
        {userRole && (
          <p className="font-['IBM_Plex_Sans'] text-[#7A8078] text-sm">
            Your current role: <strong>{userRole}</strong>
          </p>
        )}
        <p className="font-['IBM_Plex_Sans'] text-[#7A8078] text-sm mt-4">
          Contact the school administrator if you believe this is a mistake.
        </p>
      </div>
    </div>
  );
}

export default ProtectedRoute;
