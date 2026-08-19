/**
 * Toast Notification & Error Handling Utilities
 *
 * Simple toast notification system without external library
 * Integrates with API error interceptor
 */

import React from 'react';

// ─── Toast Types ────────────────────────────────────────────────────────────

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// ─── Toast Manager ──────────────────────────────────────────────────────────

let toastListeners: ((toast: Toast) => void)[] = [];
let toastRemoveListeners: ((id: string) => void)[] = [];

/**
 * Register a listener for new toasts (called by ToastContainer)
 */
export function registerToastListener(
  listener: (toast: Toast) => void,
  removeListener: (id: string) => void
) {
  toastListeners.push(listener);
  toastRemoveListeners.push(removeListener);

  return () => {
    toastListeners = toastListeners.filter(l => l !== listener);
    toastRemoveListeners = toastRemoveListeners.filter(l => l !== removeListener);
  };
}

/**
 * Show a toast notification
 */
export function showToast(
  message: string,
  type: ToastType = 'info',
  duration: number = 4000,
  action?: { label: string; onClick: () => void }
) {
  const id = `toast-${Date.now()}-${Math.random()}`;

  const toast: Toast = {
    id,
    message,
    type,
    duration,
    action,
  };

  toastListeners.forEach(listener => listener(toast));

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }

  return id;
}

/**
 * Remove a specific toast
 */
export function removeToast(id: string) {
  toastRemoveListeners.forEach(listener => listener(id));
}

/**
 * Show success toast
 */
export function showSuccess(message: string, duration?: number) {
  return showToast(message, 'success', duration || 3000);
}

/**
 * Show error toast
 */
export function showError(message: string, duration?: number) {
  return showToast(message, 'error', duration || 5000);
}

/**
 * Show warning toast
 */
export function showWarning(message: string, duration?: number) {
  return showToast(message, 'warning', duration || 4000);
}

/**
 * Show info toast
 */
export function showInfo(message: string, duration?: number) {
  return showToast(message, 'info', duration || 3000);
}

// ─── Toast Container Component ──────────────────────────────────────────────

const TOAST_COLORS = {
  success: { bg: 'bg-[#E7F0EA]', border: 'border-[#1F6F4A]', text: 'text-[#1F6F4A]' },
  error: { bg: 'bg-[#F7E6E2]', border: 'border-[#9C3B2E]', text: 'text-[#9C3B2E]' },
  warning: { bg: 'bg-[#F5EAD6]', border: 'border-[#B5751F]', text: 'text-[#B5751F]' },
  info: { bg: 'bg-[#EBE7DC]', border: 'border-[#7A8078]', text: 'text-[#7A8078]' },
};

export function ToastContainer() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  React.useEffect(() => {
    const unregister = registerToastListener(
      (toast) => {
        setToasts(prev => [...prev, toast]);
      },
      (id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }
    );

    return unregister;
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-[9999] space-y-2 pointer-events-none">
      {toasts.map(toast => {
        const colors = TOAST_COLORS[toast.type];

        return (
          <div
            key={toast.id}
            className={`${colors.bg} border-l-4 ${colors.border} rounded-sm px-4 py-3 shadow-lg pointer-events-auto max-w-sm animate-in fade-in slide-in-from-bottom-4 duration-300`}
          >
            <div className={`${colors.text} font-['IBM_Plex_Sans'] text-sm font-medium`}>
              {toast.message}
            </div>
            {toast.action && (
              <button
                onClick={() => {
                  toast.action!.onClick();
                  removeToast(toast.id);
                }}
                className={`${colors.text} text-xs font-semibold mt-1 hover:underline`}
              >
                {toast.action.label}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── API Error Handler ──────────────────────────────────────────────────────

/**
 * Global error handler that listens to API error events
 * Set up in main app
 */
export function useAPIErrorHandler() {
  React.useEffect(() => {
    const handleAPIError = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { message, status } = customEvent.detail;

      showError(message || `Error ${status}: Unable to process request`);
    };

    window.addEventListener('api:error', handleAPIError);

    return () => {
      window.removeEventListener('api:error', handleAPIError);
    };
  }, []);
}

// ─── Async Operations Helper ────────────────────────────────────────────────

/**
 * Helper to show loading/success/error states for async operations
 *
 * Usage:
 *   const handleSubmit = async () => {
 *     try {
 *       await performAsyncAction({
 *         operation: () => submitForm(data),
 *         loadingMessage: "Submitting...",
 *         successMessage: "Form submitted successfully",
 *         errorMessage: "Failed to submit form"
 *       });
 *     } catch (error) {
 *       // Already handled by performAsyncAction
 *     }
 *   };
 */
export async function performAsyncAction<T>({
  operation,
  loadingMessage = 'Processing...',
  successMessage = 'Success',
  errorMessage = 'An error occurred',
}: {
  operation: () => Promise<T>;
  loadingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
}): Promise<T> {
  try {
    const toastId = showInfo(loadingMessage);

    const result = await operation();

    removeToast(toastId);
    showSuccess(successMessage);

    return result;
  } catch (error) {
    const message = error instanceof Error ? error.message : errorMessage;
    showError(message);
    throw error;
  }
}
