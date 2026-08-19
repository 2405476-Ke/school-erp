/**
 * React Query Hooks for Common API Patterns
 *
 * Provides strongly-typed hooks for fetching backend data
 * Handles loading, error, and success states automatically
 *
 * Usage:
 *   const { data: prospects, isLoading, error } = useProspects(schoolId);
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPut, apiDelete, getErrorMessage } from './api';
import { tokenManager } from './api';

// ─── Utility Hook Factories ──────────────────────────────────────────────────

/**
 * Factory function to create a list query hook
 */
function createListQueryHook<T>(
  queryKey: string,
  endpoint: string,
  defaultParams = {}
) {
  return (params = {}) => {
    const schoolId = tokenManager.getSchoolId();

    return useQuery({
      queryKey: [queryKey, { ...defaultParams, ...params }],
      queryFn: async () => {
        const query = new URLSearchParams({
          school_id: schoolId || '',
          ...defaultParams,
          ...params,
        }).toString();

        return apiGet<T[]>(`${endpoint}?${query}`);
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
      enabled: !!schoolId, // Only fetch if school_id is set
    });
  };
}

/**
 * Factory function to create a detail query hook
 */
function createDetailQueryHook<T>(queryKey: string, endpoint: (id: string) => string) {
  return (id: string | undefined) => {
    return useQuery({
      queryKey: [queryKey, id],
      queryFn: () => apiGet<T>(endpoint(id!)),
      enabled: !!id,
      staleTime: 5 * 60 * 1000,
    });
  };
}

/**
 * Factory function to create a mutation hook
 */
function createMutationHook<TData, TVariables>(
  endpoint: string,
  method: 'post' | 'put' | 'delete' = 'post'
) {
  return () => {
    const queryClient = useQueryClient();

    return useMutation({
      mutationFn: async (variables: TVariables) => {
        if (method === 'post') {
          return apiPost<TData>(endpoint, variables);
        } else if (method === 'put') {
          return apiPut<TData>(endpoint, variables);
        } else if (method === 'delete') {
          return apiDelete<TData>(endpoint);
        }
      },
      onSuccess: () => {
        queryClient.invalidateQueries();
      },
    });
  };
}

// ─── Admissions Hooks ──────────────────────────────────────────────────────────

export interface StudentProspect {
  id: string;
  first_name: string;
  last_name: string;
  guardian_phone: string;
  applied_class: string;
  applied_stream: string;
  prospect_status: string;
  created_at: string;
}

export const useProspects = createListQueryHook<StudentProspect>(
  'prospects',
  '/admissions/prospects'
);

export interface StudentDetail {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  current_class: string;
  current_stream: string;
  boarding_status: string;
  active_status: string;
  kcpe_marks: number;
  prospective_upi: string;
  created_at: string;
}

export const useStudent = createDetailQueryHook<StudentDetail>(
  'student',
  (id) => `/admissions/students/${id}`
);

export interface AdmitStudentPayload {
  prospect_id: string;
  prospective_upi: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  category: string;
  current_class: string;
  current_stream: string;
  kcpe_marks: number;
  boarding_status: string;
  home_county: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
}

export const useAdmitStudent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AdmitStudentPayload) =>
      apiPost('/admissions/students/admit', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prospects'] });
      queryClient.invalidateQueries({ queryKey: ['students'] });
    },
  });
};

// ─── Finance Hooks ────────────────────────────────────────────────────────────

export interface FeeAccountLine {
  fee_line_id: string;
  fee_item_name: string;
  total_amount: string;
  amount_paid: string;
  amount_balance: string;
}

export interface FeeAccount {
  student_id: string;
  term_id: string;
  current_term: string;
  current_year: number;
  fee_account_lines: FeeAccountLine[];
  total_balance: string;
}

export const useFeeAccount = (studentId: string | undefined) => {
  return useQuery({
    queryKey: ['fee_account', studentId],
    queryFn: () => apiGet<FeeAccount>(`/finance/fee-accounts/${studentId}`),
    enabled: !!studentId,
    staleTime: 5 * 60 * 1000,
  });
};

export interface JournalEntry {
  id: string;
  entry_date: string;
  journal_number: string;
  debit_account: { id: string; name: string };
  credit_account: { id: string; name: string };
  amount: string;
  description: string;
}

export const useJournalEntries = (month?: number, year?: number) => {
  const schoolId = tokenManager.getSchoolId();

  return useQuery({
    queryKey: ['journal_entries', { month, year }],
    queryFn: async () => {
      const query = new URLSearchParams({
        school_id: schoolId || '',
        ...(month && { month: String(month) }),
        ...(year && { year: String(year) }),
      }).toString();

      return apiGet<JournalEntry[]>(`/finance/journals?${query}`);
    },
    staleTime: 10 * 60 * 1000,
    enabled: !!schoolId,
  });
};

// ─── HR & Payroll Hooks ────────────────────────────────────────────────────────

export interface Staff {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  staff_number: string;
  role: string;
  employment_type: string;
  date_of_birth: string;
  date_employed: string;
}

export const useStaff = () => {
  const schoolId = tokenManager.getSchoolId();

  return useQuery({
    queryKey: ['staff', schoolId],
    queryFn: () =>
      apiGet<Staff[]>(`/hr/staff?school_id=${schoolId}`),
    staleTime: 10 * 60 * 1000,
    enabled: !!schoolId,
  });
};

export interface PayslipItem {
  description: string;
  amount: string;
  category: 'earnings' | 'deduction' | 'statutory';
}

export interface PayslipDetail {
  staff_id: string;
  staff_name: string;
  month: number;
  year: number;
  gross_pay: string;
  basic_salary: string;
  house_allowance: string;
  transport_allowance: string;
  medical_insurance: string;
  paye_tax: string;
  nssf_contribution: string;
  net_pay: string;
  bank_account: string;
  items: PayslipItem[];
}

export const usePayslip = (staffId: string, month: number, year: number) => {
  return useQuery({
    queryKey: ['payslip', staffId, month, year],
    queryFn: () =>
      apiGet<PayslipDetail>(
        `/payroll/payslips/${staffId}?month=${month}&year=${year}`
      ),
    enabled: !!staffId,
    staleTime: 10 * 60 * 1000,
  });
};

export interface ProcessPayrollPayload {
  month: number;
  year: number;
  description?: string;
}

export const useProcessPayroll = () => {
  const queryClient = useQueryClient();
  const schoolId = tokenManager.getSchoolId();

  return useMutation({
    mutationFn: (data: ProcessPayrollPayload) =>
      apiPost(
        `/payroll/payroll-run/${schoolId}/process`,
        {
          ...data,
        }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payslip'] });
      queryClient.invalidateQueries({ queryKey: ['payroll_run'] });
    },
  });
};

// ─── Boarding Hooks ──────────────────────────────────────────────────────────

export interface LeavePass {
  id: string;
  student_id: string;
  exeat_type: string;
  status: string;
  requested_date: string;
  approved_date?: string;
  expected_return_time: string;
  actual_return_time?: string;
  reason: string;
}

export const useLeavePass = (studentId: string | undefined) => {
  return useQuery({
    queryKey: ['leave_pass', studentId],
    queryFn: () =>
      apiGet<LeavePass[]>(
        `/boarding/leave-passes?student_id=${studentId}`
      ),
    enabled: !!studentId,
    staleTime: 5 * 60 * 1000,
  });
};

export interface ApproveLeavePassPayload {
  leave_pass_id: string;
  approved: boolean;
}

export const useApproveLeavePass = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ApproveLeavePassPayload) =>
      apiPost('/boarding/leave-passes/approve', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave_pass'] });
    },
  });
};

// ─── Procurement Hooks ────────────────────────────────────────────────────────

export interface LineItem {
  item_description: string;
  quantity_requested: number;
  unit_of_measure: string;
  unit_cost: string;
}

export interface CreateRequisitionPayload {
  requisition_date: string;
  line_items: LineItem[];
  description?: string;
}

export const useCreateRequisition = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateRequisitionPayload) =>
      apiPost('/procurement/purchase-requisitions', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requisitions'] });
    },
  });
};

// ─── Gate Security Hooks ──────────────────────────────────────────────────────

export interface VisitorCheckInPayload {
  first_name: string;
  last_name: string;
  national_id: string;
  phone: string;
  email?: string;
  visitor_type: string;
  purpose: string;
  host_staff_id?: string;
  vehicle_registration?: string;
  vehicle_description?: string;
}

export const useCheckInVisitor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VisitorCheckInPayload) =>
      apiPost('/security/gate/visitor/check-in', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['visitor_logs'] });
    },
  });
};

export interface ScanStudentExitPayload {
  student_id: string;
  guard_user_id: string;
}

export const useScanStudentExit = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScanStudentExitPayload) =>
      apiPost('/security/gate/scan-student-exit', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gate_events'] });
    },
  });
};

export interface ScanStudentEntryPayload {
  student_id: string;
  guard_user_id: string;
}

export const useScanStudentEntry = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScanStudentEntryPayload) =>
      apiPost('/security/gate/scan-student-entry', {
        school_id: tokenManager.getSchoolId(),
        ...data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gate_events'] });
    },
  });
};

// ─── Audit Log Hooks ──────────────────────────────────────────────────────────

export interface AuditLogEntry {
  timestamp: string;
  user_id: string;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  changes: Record<string, any>;
}

export const useAuditLogs = (limit = 100, offset = 0) => {
  const schoolId = tokenManager.getSchoolId();

  return useQuery({
    queryKey: ['audit_logs', { limit, offset }],
    queryFn: () =>
      apiGet<AuditLogEntry[]>(
        `/audit/audit-logs?school_id=${schoolId}&limit=${limit}&offset=${offset}`
      ),
    staleTime: 10 * 60 * 1000,
    enabled: !!schoolId,
  });
};
