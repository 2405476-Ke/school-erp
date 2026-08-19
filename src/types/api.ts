/**
 * API Type Definitions
 *
 * Shared TypeScript interfaces for all API communication
 */

// ─── Authentication Types ──────────────────────────────────────────────────

/**
 * User object returned by backend
 */
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  school_id: string;
  school_name?: string;
  created_at: string;
  is_active: boolean;
}

/**
 * User roles in the system
 */
export type UserRole =
  | 'PRINCIPAL'
  | 'DEPUTY_PRINCIPAL'
  | 'BURSAR'
  | 'STAFF_TEACHER'
  | 'HOD'
  | 'BOARDING_MASTER'
  | 'REGISTRAR'
  | 'GATEKEEPER'
  | 'ADMIN'
  | 'PARENT';

/**
 * Login request payload
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Login response from backend
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * Logout response
 */
export interface LogoutResponse {
  message: string;
}

// ─── Error Types ──────────────────────────────────────────────────────────

/**
 * Pydantic validation error field
 */
export interface ValidationErrorField {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * Backend error response (Pydantic validation)
 */
export interface ValidationErrorResponse {
  detail: ValidationErrorField[];
}

/**
 * Backend error response (single message)
 */
export interface ErrorMessageResponse {
  detail: string;
}

/**
 * HTTP error with details
 */
export interface HTTPError {
  status_code: number;
  detail: string | ValidationErrorField[];
  message?: string;
}

// ─── API Response Wrapper ──────────────────────────────────────────────────

/**
 * Standard API response wrapper
 *
 * All backend endpoints return this structure:
 * {
 *   "data": {...},
 *   "message": "Success",
 *   "status_code": 200
 * }
 */
export interface APIResponse<T = any> {
  data: T;
  message: string;
  status_code: number;
}

// ─── Common Data Types ────────────────────────────────────────────────────

/**
 * Prospect status enum
 */
export type ProspectStatus =
  | 'CLEARED'
  | 'INTERVIEW'
  | 'DOCUMENTS_PENDING'
  | 'OFFER_SENT'
  | 'ENQUIRY';

/**
 * Student prospect for admission tracking
 */
export interface StudentProspect {
  id: string;
  school_id: string;
  first_name: string;
  last_name: string;
  guardian_phone: string;
  applied_class: string;
  applied_stream: string;
  prospect_status: ProspectStatus;
  created_at: string;
  kcpe_marks?: number;
}

/**
 * Student active status
 */
export type StudentActiveStatus =
  | 'ACTIVE'
  | 'TRANSFERRED'
  | 'EXPELLED'
  | 'GRADUATED'
  | 'WITHDRAWN';

/**
 * Student boarding status
 */
export type BoardingStatus =
  | 'ACTIVE_BOARDER'
  | 'ACTIVE_DAY_SCHOLAR'
  | 'INACTIVE'
  | 'TRANSFERRED';

/**
 * Student category
 */
export type StudentCategory = 'BOARDER' | 'DAY_SCHOLAR';

/**
 * Gender enum
 */
export type Gender = 'MALE' | 'FEMALE' | 'OTHER';

/**
 * Class enum
 */
export type Class =
  | 'FORM_1'
  | 'FORM_2'
  | 'FORM_3'
  | 'FORM_4';

/**
 * Student detail (full profile)
 */
export interface Student {
  id: string;
  school_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  national_id?: string;
  prospective_upi: string;
  current_class: Class;
  current_stream: string;
  boarding_status: BoardingStatus;
  active_status: StudentActiveStatus;
  category: StudentCategory;
  kcpe_marks?: number;
  home_county?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Admit student payload
 */
export interface AdmitStudentPayload {
  prospect_id: string;
  prospective_upi: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  category: StudentCategory;
  current_class: Class;
  current_stream: string;
  kcpe_marks: number;
  boarding_status: BoardingStatus;
  home_county?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
}

// ─── Fee Types ────────────────────────────────────────────────────────────

/**
 * Fee account line item
 */
export interface FeeAccountLine {
  fee_line_id: string;
  fee_item_name: string;
  total_amount: string;
  amount_paid: string;
  amount_balance: string;
}

/**
 * Complete fee account
 */
export interface FeeAccount {
  student_id: string;
  term_id: string;
  current_term: string;
  current_year: number;
  fee_account_lines: FeeAccountLine[];
  total_balance: string;
}

// ─── Leave Pass Types ──────────────────────────────────────────────────────

/**
 * Leave pass status
 */
export type LeavePassStatus =
  | 'REQUESTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'DEPARTED'
  | 'RETURNED';

/**
 * Leave pass exeat type
 */
export type ExeatType = 'WEEKEND' | 'HOLIDAY' | 'EMERGENCY' | 'MEDICAL';

/**
 * Leave pass
 */
export interface LeavePass {
  id: string;
  student_id: string;
  exeat_type: ExeatType;
  status: LeavePassStatus;
  requested_date: string;
  approved_date?: string;
  expected_return_time: string;
  actual_return_time?: string;
  reason: string;
}

// ─── Academic Assessment Types ────────────────────────────────────────────

/**
 * Assessment entry (grades)
 */
export interface AssessmentEntry {
  id: string;
  student_id: string;
  subject_name: string;
  score: number;
  grade: string;
  assessment_term: string;
  assessment_year: number;
  created_at: string;
}

// ─── Boarding Discipline Types ────────────────────────────────────────────

/**
 * Discipline case
 */
export interface DisciplineCase {
  id: string;
  student_id: string;
  incident_date: string;
  incident_description: string;
  case_status: 'OPEN' | 'CLOSED' | 'PENDING';
  action_taken?: string;
  created_at: string;
}

// ─── Gate Security Types ──────────────────────────────────────────────────

/**
 * Visitor check-in payload
 */
export interface VisitorCheckInPayload {
  visitor_name: string;
  visitor_phone: string;
  purpose: string;
  student_name: string;
  expected_duration_minutes: number;
}

/**
 * Visitor check-in response
 */
export interface VisitorCheckInResponse {
  id: string;
  check_in_time: string;
  check_in_reference: string;
}

/**
 * Student scan payload (entry or exit)
 */
export interface StudentScanPayload {
  student_id: string;
  action: 'ENTRY' | 'EXIT';
  scan_timestamp: string;
}

/**
 * Student scan response (success or error)
 */
export interface StudentScanResponse {
  id: string;
  student_id: string;
  student_name: string;
  action: 'ENTRY' | 'EXIT';
  timestamp: string;
  status: 'ALLOWED' | 'BLOCKED';
  message: string;
}

// ─── Boarding Leave Pass Types ────────────────────────────────────────────

/**
 * Leave pass (exeat) record
 */
export interface LeavePassRecord {
  id: string;
  student_id: string;
  student_name: string;
  exeat_type: 'WEEKEND' | 'HOLIDAY' | 'EMERGENCY' | 'MEDICAL';
  status: 'REQUESTED' | 'APPROVED' | 'REJECTED' | 'DEPARTED' | 'RETURNED';
  requested_date: string;
  approved_date?: string;
  expected_return_time: string;
  actual_return_time?: string;
  reason: string;
}

/**
 * Leave pass approval payload
 */
export interface LeavePassApprovalPayload {
  leave_pass_id: string;
  action: 'APPROVE' | 'REJECT';
  notes?: string;
}

/**
 * Exeat queue entry
 */
export interface ExeatQueueEntry {
  id: string;
  student_id: string;
  student_name: string;
  class: string;
  stream: string;
  departure_time: string;
  expected_return_time: string;
  status: 'DEPARTED' | 'OVERDUE' | 'RETURNED';
  remarks?: string;
}

/**
 * Bed allocation record
 */
export interface BedAllocation {
  id: string;
  student_id: string;
  student_name: string;
  dorm_name: string;
  bed_number: string;
  room_number: string;
  allocation_date: string;
  status: 'ACTIVE' | 'VACANT' | 'MAINTENANCE';
}

// ─── Gate Security Audit Types ────────────────────────────────────────────

/**
 * Gate audit log entry
 */
export interface GateAuditEntry {
  id: string;
  timestamp: string;
  entry_type: 'STUDENT_ENTRY' | 'STUDENT_EXIT' | 'VISITOR_CHECKIN' | 'VISITOR_CHECKOUT';
  person_id: string;
  person_name: string;
  person_type: 'STUDENT' | 'VISITOR' | 'STAFF';
  action_status: 'ALLOWED' | 'BLOCKED';
  reason?: string;
  officer_name: string;
}

// ─── Inventory Stock Types ────────────────────────────────────────────────

/**
 * Stock item
 */
export interface StockItem {
  id: string;
  item_name: string;
  current_quantity: number;
  unit: string;
  reorder_level: number;
  unit_cost: string;
}

/**
 * Stock issue payload
 */
export interface StockIssuePayload {
  item_id: string;
  quantity_issued: number;
  issued_to: string;
  department: string;
  purpose: string;
  issue_date: string;
}

/**
 * Stock issue response
 */
export interface StockIssueResponse {
  id: string;
  item_name: string;
  quantity_issued: number;
  issue_reference: string;
  timestamp: string;
}

// ─── Communications Batch Types ────────────────────────────────────────────

/**
 * Batch communication report
 */
export interface BatchCommunicationReport {
  id: string;
  batch_type: 'SMS' | 'EMAIL' | 'WHATSAPP';
  recipient_count: number;
  subject: string;
  sent_date: string;
  sent_by: string;
  delivery_status: {
    total_sent: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  recipients?: Array<{
    recipient_id: string;
    recipient_name: string;
    recipient_contact: string;
    delivery_status: 'DELIVERED' | 'FAILED' | 'PENDING';
    timestamp: string;
  }>;
}

// ─── Type Guards ──────────────────────────────────────────────────────────

/**
 * Check if error response has validation errors
 */
export function isValidationError(error: any): error is ValidationErrorResponse {
  return Array.isArray(error?.detail);
}

/**
 * Check if error response has a single message
 */
export function isErrorMessage(error: any): error is ErrorMessageResponse {
  return typeof error?.detail === 'string';
}

/**
 * Safe error extraction
 */
export function getErrorMessage(error: any): string {
  if (isValidationError(error)) {
    return error.detail
      .map(err => `${err.loc?.join('.')}: ${err.msg}`)
      .join('\n');
  }

  if (isErrorMessage(error)) {
    return error.detail;
  }

  if (error?.message) {
    return error.message;
  }

  return 'An unknown error occurred';
}
