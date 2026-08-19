/**
 * Login Page
 *
 * Authentication entry point for all ERP users
 * - Principal, Deputy, Bursar, Teachers, Gatekeepers, Parents, etc.
 * - Uses design tokens from Figma (PRIMARY #1F6F4A, INK #16241D)
 * - Wired to POST /auth/login backend endpoint
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { getErrorMessage } from '@/types/api';
import axios from 'axios';

interface LoginFormState {
  email: string;
  password: string;
  isLoading: boolean;
  error: string | null;
}

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  const [form, setForm] = useState<LoginFormState>({
    email: '',
    password: '',
    isLoading: false,
    error: null,
  });

  // ─── Redirect if already authenticated ───────────────────────────────

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // ─── Form field handlers ────────────────────────────────────────────

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({
      ...prev,
      email: e.target.value,
      error: null,
    }));
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({
      ...prev,
      password: e.target.value,
      error: null,
    }));
  };

  // ─── Form submission ────────────────────────────────────────────────

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Validation
    if (!form.email || !form.password) {
      setForm(prev => ({
        ...prev,
        error: 'Email and password are required',
      }));
      return;
    }

    try {
      setForm(prev => ({ ...prev, isLoading: true, error: null }));

      await login(form.email, form.password);

      // Navigate to dashboard on success
      navigate('/');
    } catch (error) {
      const errorMessage = axios.isAxiosError(error)
        ? getErrorMessage(error.response?.data)
        : error instanceof Error
        ? error.message
        : 'Login failed. Please try again.';

      setForm(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false,
      }));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F3EFE4] px-4">
      {/* Card Container */}
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg border border-[#DCD6C4]">
        {/* Header */}
        <div className="px-8 py-6 border-b border-[#DCD6C4] bg-gradient-to-r from-[#1F6F4A]/5 to-transparent">
          <h1 className="text-2xl font-bold font-['Fraunces'] text-[#16241D]">
            {import.meta.env.VITE_APP_NAME || 'Nambale ERP'}
          </h1>
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078] mt-1">
            School Management System
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-8 py-8 space-y-6">
          {/* Error Alert */}
          {form.error && (
            <div className="p-4 bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm">
              <p className="text-sm font-medium font-['IBM_Plex_Sans'] text-[#9C3B2E]">
                {form.error}
              </p>
            </div>
          )}

          {/* Email Field */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium font-['IBM_Plex_Sans'] text-[#16241D] mb-2"
            >
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={handleEmailChange}
              disabled={form.isLoading}
              placeholder="principal@school.ac.ke"
              className="w-full px-4 py-2 border border-[#DCD6C4] rounded-sm font-['IBM_Plex_Sans'] text-[#16241D] placeholder-[#7A8078] focus:outline-none focus:border-[#1F6F4A] focus:ring-1 focus:ring-[#1F6F4A]/50 disabled:bg-[#F3EFE4] disabled:cursor-not-allowed"
            />
          </div>

          {/* Password Field */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium font-['IBM_Plex_Sans'] text-[#16241D] mb-2"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={form.password}
              onChange={handlePasswordChange}
              disabled={form.isLoading}
              placeholder="••••••••"
              className="w-full px-4 py-2 border border-[#DCD6C4] rounded-sm font-['IBM_Plex_Sans'] text-[#16241D] placeholder-[#7A8078] focus:outline-none focus:border-[#1F6F4A] focus:ring-1 focus:ring-[#1F6F4A]/50 disabled:bg-[#F3EFE4] disabled:cursor-not-allowed"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={form.isLoading}
            className="w-full py-2.5 px-4 bg-[#1F6F4A] hover:bg-[#1a5a3e] disabled:bg-[#7A8078] disabled:cursor-not-allowed text-white font-medium font-['IBM_Plex_Sans'] rounded-sm transition-colors duration-200"
          >
            {form.isLoading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="px-8 py-4 border-t border-[#DCD6C4] bg-[#F3EFE4]/30">
          <p className="text-xs font-['IBM_Plex_Sans'] text-[#7A8078] text-center">
            For support, contact the school administrator
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
