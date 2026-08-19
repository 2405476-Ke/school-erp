/**
 * Common Data Formatting & Transformation Utilities
 *
 * Used across all components to normalize backend data for display
 */

/**
 * Format amount as Kenyan currency (KES)
 *
 * Input: "45000.00" or 45000
 * Output: "KES 45,000"
 */
export function formatKES(amount: string | number | null | undefined): string {
  if (amount === null || amount === undefined) return "—";

  const num = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(num)) return "—";

  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Format date from ISO string to display format
 *
 * Input: "2025-01-12T00:00:00"
 * Output: "12 Jan 2025"
 */
export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return "—";

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "—";

  return date.toLocaleDateString('en-KE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Format datetime from ISO string to display format
 *
 * Input: "2025-06-15T08:00:00"
 * Output: "2025-06-15 08:00:00"
 */
export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "—";

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

/**
 * Format time only from ISO string
 *
 * Input: "2025-06-15T14:34:00"
 * Output: "14:34"
 */
export function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return "—";

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "—";

  return date.toLocaleTimeString('en-KE', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Map backend prospect status enum to frontend StatusTag variant
 *
 * Backend: "CLEARED" | "INTERVIEW" | "DOCUMENTS_PENDING" | "OFFER_SENT" | "ENQUIRY"
 * Frontend: "ok" | "warn" | "bad" | "neutral"
 */
export function prospectStatusToVariant(status: string): "ok" | "warn" | "bad" | "neutral" {
  const map: Record<string, "ok" | "warn" | "bad" | "neutral"> = {
    CLEARED: "ok",
    INTERVIEW: "warn",
    DOCUMENTS_PENDING: "warn",
    OFFER_SENT: "warn",
    ENQUIRY: "neutral",
  };

  return map[status] || "neutral";
}

/**
 * Map backend leave pass status enum to frontend StatusTag variant
 */
export function leavePassStatusToVariant(status: string): "ok" | "warn" | "bad" | "neutral" {
  const map: Record<string, "ok" | "warn" | "bad" | "neutral"> = {
    APPROVED: "ok",
    REQUESTED: "warn",
    REJECTED: "bad",
    DEPARTED: "neutral",
    RETURNED: "ok",
  };

  return map[status] || "neutral";
}

/**
 * Map backend fee account status to frontend StatusTag variant
 * Status is derived from balance: balance > 0 = "bad", balance === 0 = "ok"
 */
export function feeStatusToVariant(balanceAmount: number | null | undefined): "ok" | "warn" | "bad" | "neutral" {
  if (balanceAmount === null || balanceAmount === undefined) return "neutral";

  if (balanceAmount > 0) return "bad"; // Amount owed = bad
  if (balanceAmount === 0) return "ok"; // Fully paid = ok

  return "neutral"; // Credit = neutral
}

/**
 * Format student name from separate first/last fields
 *
 * Input: { first_name: "Amina", last_name: "Wanjiku Kariuki" }
 * Output: "Amina Wanjiku Kariuki"
 */
export function formatStudentName(firstName?: string, lastName?: string): string {
  const parts = [firstName, lastName].filter(Boolean);
  return parts.length > 0 ? parts.join(' ') : "Unknown Student";
}

/**
 * Format class and stream into display format
 *
 * Input: { current_class: "FORM_1", current_stream: "A" }
 * Output: "Form 1 · Stream A"
 */
export function formatClassStream(classCode: string, stream: string): string {
  const classNames: Record<string, string> = {
    FORM_1: "Form 1",
    FORM_2: "Form 2",
    FORM_3: "Form 3",
    FORM_4: "Form 4",
  };

  const className = classNames[classCode] || classCode;
  return `${className} · Stream ${stream}`;
}

/**
 * Map backend role enum to display name
 */
export function formatRole(role: string): string {
  const map: Record<string, string> = {
    PRINCIPAL: "Principal",
    DEPUTY_PRINCIPAL: "Deputy Principal",
    BURSAR: "Bursar",
    STAFF_TEACHER: "Teacher",
    HOD: "Head of Department",
    BOARDING_MASTER: "Boarding Master",
    REGISTRAR: "Registrar",
    GATEKEEPER: "Gatekeeper",
    ADMIN: "Administrator",
  };

  return map[role] || role;
}

/**
 * Map backend gender enum to display text
 */
export function formatGender(gender: string): string {
  const map: Record<string, string> = {
    MALE: "Male",
    FEMALE: "Female",
    OTHER: "Other",
  };

  return map[gender] || gender;
}

/**
 * Format student category (Boarder/Day Scholar)
 */
export function formatCategory(category: string): string {
  const map: Record<string, string> = {
    BOARDER: "Boarder",
    DAY_SCHOLAR: "Day Scholar",
  };

  return map[category] || category;
}

/**
 * Parse backend Decimal string (comes as string in JSON)
 */
export function parseDecimal(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0;

  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? 0 : num;
}

/**
 * Format percentage with optional decimal places
 */
export function formatPercent(value: number, decimals: number = 2): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Calculate percentage
 */
export function calculatePercent(part: number, total: number): number {
  if (total === 0) return 0;
  return (part / total) * 100;
}

/**
 * Format month and year for display
 * Input: month = 6, year = 2025
 * Output: "June 2025"
 */
export function formatMonthYear(month: number, year: number): string {
  const date = new Date(year, month - 1, 1);
  return date.toLocaleDateString('en-KE', { month: 'long', year: 'numeric' });
}

/**
 * Map backend phone number to displayable format
 * Handles variations: 0712345678, +254712345678, 254712345678
 */
export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return "—";

  // Remove all non-digits
  const digits = phone.replace(/\D/g, '');

  // Convert to +254 format
  let formatted = digits;
  if (formatted.startsWith('254')) {
    formatted = '+' + formatted;
  } else if (formatted.startsWith('0')) {
    formatted = '+254' + formatted.substring(1);
  }

  // Format as +254 712 345 678
  const match = formatted.match(/^(\+\d{3})(\d{3})(\d{3})(\d{3})$/);
  if (match) {
    return `${match[1]} ${match[2]} ${match[3]} ${match[4]}`;
  }

  return phone;
}

/**
 * Safely access nested object properties
 * Input: getNestedValue({ a: { b: { c: 123 } } }, 'a.b.c')
 * Output: 123
 */
export function getNestedValue(obj: any, path: string, defaultValue: any = null): any {
  const keys = path.split('.');
  let value = obj;

  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      return defaultValue;
    }
  }

  return value;
}
