/**
 * Services Index
 *
 * Central export point for all service utilities
 */

// API Client
export { apiClient, tokenManager, apiGet, apiPost, apiPut, apiDelete, getErrorMessage } from './api';
export type { APIResponse } from './api';

// Formatting & Transformation
export {
  formatKES,
  formatDate,
  formatDateTime,
  formatTime,
  prospectStatusToVariant,
  leavePassStatusToVariant,
  feeStatusToVariant,
  formatStudentName,
  formatClassStream,
  formatRole,
  formatGender,
  formatCategory,
  parseDecimal,
  formatPercent,
  calculatePercent,
  formatMonthYear,
  formatPhone,
  getNestedValue,
} from './formatting';

// React Query Hooks
export {
  useProspects,
  useStudent,
  useAdmitStudent,
  useFeeAccount,
  useJournalEntries,
  useStaff,
  usePayslip,
  useProcessPayroll,
  useLeavePass,
  useApproveLeavePass,
  useCreateRequisition,
  useCheckInVisitor,
  useScanStudentExit,
  useScanStudentEntry,
  useAuditLogs,
} from './hooks';

export type {
  StudentProspect,
  StudentDetail,
  AdmitStudentPayload,
  FeeAccountLine,
  FeeAccount,
  JournalEntry,
  Staff,
  PayslipItem,
  PayslipDetail,
  ProcessPayrollPayload,
  LeavePass,
  ApproveLeavePassPayload,
  LineItem,
  CreateRequisitionPayload,
  VisitorCheckInPayload,
  ScanStudentExitPayload,
  ScanStudentEntryPayload,
  AuditLogEntry,
} from './hooks';

// Auth
export { AuthProvider, useAuth, ProtectedRoute } from './auth';
export type { AuthContextType, ProtectedRouteProps } from './auth';

// Notifications
export {
  showToast,
  removeToast,
  showSuccess,
  showError,
  showWarning,
  showInfo,
  ToastContainer,
  useAPIErrorHandler,
  performAsyncAction,
  registerToastListener,
} from './notifications';

export type { Toast, ToastType } from './notifications';
