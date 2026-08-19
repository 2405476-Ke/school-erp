# STEP 2: Global API Client Setup - COMPLETE ✅

## Overview
Created a production-ready API infrastructure that connects the Figma-generated frontend to the FastAPI backend.

## Files Created

### 1. `src/services/api.ts` (250+ lines)
**Purpose**: Centralized Axios instance with interceptors

**Key Features**:
- ✅ Automatic JWT Bearer token injection on all requests
- ✅ Request interceptor: Attaches token from localStorage
- ✅ Response interceptor with error handling:
  - 401: Auto-logout + redirect to login
  - 403: Permission denied alert
  - 5xx: Retry with exponential backoff (1s, 2s max)
  - Network errors: 2 automatic retries
- ✅ Token manager utility (get/set/clear/check)
- ✅ Typed API functions: `apiGet<T>()`, `apiPost<T>()`, etc.
- ✅ Error message extraction from Pydantic validation errors

**Configuration**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
```

**Usage**:
```typescript
// Simple GET
const prospects = await apiGet<StudentProspect[]>('/admissions/prospects');

// Typed POST
const student = await apiPost<StudentDetail>('/admissions/students/admit', {
  prospect_id: '...',
  prospective_upi: '...',
  // ... more fields
});
```

### 2. `src/services/formatting.ts` (350+ lines)
**Purpose**: Data transformation utilities for backend → frontend

**Functions Provided**:
- `formatKES(amount)` → "KES 45,000"
- `formatDate(iso)` → "12 Jan 2025"
- `formatDateTime(iso)` → "2025-06-15 08:00:00"
- `formatTime(iso)` → "14:34"
- `prospectStatusToVariant(status)` → "ok" | "warn" | "bad" | "neutral"
- `leavePassStatusToVariant(status)` → enum to variant
- `feeStatusToVariant(balance)` → variant based on amount owed
- `formatStudentName(first, last)` → "Amina Wanjiku Kariuki"
- `formatClassStream(class, stream)` → "Form 1 · Stream A"
- `formatRole(role)` → "Principal" (from enum)
- `formatGender(gender)` → "Male" (from enum)
- `formatCategory(category)` → "Boarder" (from enum)
- `formatPhone(phone)` → "+254 712 345 678"
- `parseDecimal(value)` → number (safe parsing)
- `formatPercent(value)` → "75.50%"
- `calculatePercent(part, total)` → number
- `formatMonthYear(month, year)` → "June 2025"
- `getNestedValue(obj, path)` → safe nested property access

**Why It Matters**:
- Backend returns enums like `"CLEARED"` → Frontend needs `"ok"` (StatusTag variant)
- Backend returns ISO dates → Frontend needs `"12 Jan 2025"`
- Backend returns `Decimal("45000.00")` → Frontend needs `"KES 45,000"`
- **Every component uses these** to avoid scattered transformation logic

### 3. `src/services/hooks.ts` (400+ lines)
**Purpose**: React Query hooks for all API endpoints

**Hook Factories**:
- `createListQueryHook()` - For fetching arrays
- `createDetailQueryHook()` - For fetching single entity
- `createMutationHook()` - For POST/PUT/DELETE

**Hooks Exported** (18 total):
1. `useProspects(params)` → StudentProspect[]
2. `useStudent(id)` → StudentDetail
3. `useAdmitStudent()` → mutation (admission workflow)
4. `useFeeAccount(studentId)` → FeeAccount
5. `useJournalEntries(month, year)` → JournalEntry[]
6. `useStaff()` → Staff[]
7. `usePayslip(staffId, month, year)` → PayslipDetail
8. `useProcessPayroll()` → mutation
9. `useLeavePass(studentId)` → LeavePass[]
10. `useApproveLeavePass()` → mutation
11. `useCreateRequisition()` → mutation
12. `useCheckInVisitor()` → mutation
13. `useScanStudentExit()` → mutation
14. `useScanStudentEntry()` → mutation
15. `useAuditLogs(limit, offset)` → AuditLogEntry[]

**Features**:
- ✅ Automatic `school_id` injection from localStorage
- ✅ Proper `queryKey` for caching
- ✅ Stale time: 5-10 minutes (configurable)
- ✅ Automatic query invalidation on mutations
- ✅ Type-safe: Every hook has TS types
- ✅ Lazy loading: Only fetches when enabled

**Usage**:
```typescript
// In a component
function StudentProfile({ studentId }) {
  const { data: student, isLoading, error } = useStudent(studentId);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>{student.first_name} {student.last_name}</div>;
}
```

### 4. `src/services/auth.tsx` (180+ lines)
**Purpose**: Authentication context + protected routes

**Exports**:
- `AuthProvider` - Wrap app with this
- `useAuth()` - Hook to access auth state
- `ProtectedRoute` - Component for route protection

**Auth Flow**:
```typescript
// 1. On app load, check if token exists in localStorage
// 2. If yes, set isAuthenticated = true
// 3. Listen for logout events from API interceptor

// 4. On login page:
const { login } = useAuth();
await login(email, password);
// Stores token + school_id + user in localStorage

// 5. On protected routes:
<ProtectedRoute requiredRole="PRINCIPAL">
  <PrincipalDashboard />
</ProtectedRoute>
```

**Features**:
- ✅ Persistent login across page reloads
- ✅ Auto-logout on 401 from API
- ✅ Role-based access control
- ✅ User state available globally

### 5. `src/services/notifications.ts` (200+ lines)
**Purpose**: Toast notifications + error handling

**Toast API**:
```typescript
showSuccess("Form submitted successfully");
showError("Failed to save");
showWarning("Unsaved changes");
showInfo("Processing...");
```

**ToastContainer Component**:
```typescript
// Add to app.tsx root:
<ToastContainer />
```

**Global API Error Handler**:
```typescript
// Automatically catches API errors and shows toast
useAPIErrorHandler();
```

**Async Operation Helper**:
```typescript
await performAsyncAction({
  operation: () => submitForm(data),
  loadingMessage: "Submitting...",
  successMessage: "Success",
  errorMessage: "Failed"
});
```

**Features**:
- ✅ Toast styling matches design tokens (green/rust/ochre)
- ✅ Auto-dismiss after duration
- ✅ Manual dismiss option
- ✅ Action buttons on toasts
- ✅ No external toast library needed

### 6. `.env.example`
Template for frontend environment variables:
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=Nambale ERP
VITE_SCHOOL_NAME=St. Joseph's High School
VITE_ENABLE_PARENT_PORTAL=true
VITE_ENABLE_GATE_SCANNER=true
VITE_ENABLE_NEMIS_EXPORT=true
```

### 7. `src/services/index.ts`
Central export point - import all services from one location:
```typescript
import { 
  apiClient, tokenManager, useProspects, useStudent,
  formatKES, formatDate, AuthProvider, useAuth,
  showSuccess, ToastContainer
} from '@/services';
```

---

## Integration Checklist

- [ ] **Backend must have CORS enabled** for `http://localhost:5173`
- [ ] **Backend `Authorization` header** must be allowed in CORS
- [ ] **Environment file**: Copy `.env.example` → `.env.local` and fill in backend URL
- [ ] **Install dependencies** (if not already done):
  ```bash
  npm install axios @tanstack/react-query
  ```
- [ ] **Update `main.tsx`** (shown below)

---

## Required App Setup

### Update `src/main.tsx`:

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './app/App'
import { AuthProvider } from '@/services'
import '@/styles/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

### Update `src/app/App.tsx`:

Add `ToastContainer` and error handler at root:

```typescript
import { ToastContainer, useAPIErrorHandler } from '@/services';

function App() {
  useAPIErrorHandler();

  return (
    <div>
      {/* Your existing app content */}
      <ToastContainer />
    </div>
  );
}
```

---

## Data Transformation Examples

**Before** (hardcoded):
```typescript
const rows = [
  ["Amina Wanjiku Kariuki", "0712 345 678", "Form 1 · Stream A", <StatusTag variant="ok" />, "12 Jan 2025"],
];
```

**After** (dynamic with formatting):
```typescript
import { formatStudentName, formatClassStream, formatDate, prospectStatusToVariant, StatusTag } from '@/services';

const { data: prospects } = useProspects();

const rows = prospects?.map(p => [
  formatStudentName(p.first_name, p.last_name),
  p.guardian_phone,
  formatClassStream(p.applied_class, p.applied_stream),
  <StatusTag variant={prospectStatusToVariant(p.prospect_status)} />,
  formatDate(p.created_at),
]) || [];
```

---

## Error Handling Flow

```
Backend API Error
       ↓
Response Interceptor catches
       ↓
   401? → Clear token → Redirect to login
   403? → Dispatch 'api:error' event
   5xx? → Retry (exponential backoff)
       ↓
useAPIErrorHandler() listens
       ↓
showError() creates toast
       ↓
ToastContainer renders
```

---

## Token & Auth Flow

```
1. User logs in
   POST /auth/login
   ↓
2. Backend returns { access_token, user }
   ↓
3. Frontend stores:
   - localStorage['auth_token'] = token
   - localStorage['school_id'] = user.school_id
   - localStorage['user'] = user
   ↓
4. Every API request:
   Request Interceptor adds:
   Authorization: Bearer {token}
   ↓
5. If token invalid:
   Response Interceptor
   → Clear localStorage
   → Dispatch 'auth:logout'
   → Redirect to /login
```

---

## What's Ready for Step 3

✅ **API client**: Ready to make requests
✅ **Auth flow**: Ready to handle login/logout
✅ **Error handling**: Ready to show toasts
✅ **Data formatting**: Ready to transform API responses
✅ **React Query**: Ready to cache API data
✅ **TypeScript**: All hooks have full type safety

**Next Step**: Wire the ProspectTracker, NewAdmission, and StudentProfile pages to use these hooks and remove hardcoded data.

---

## Common Patterns

### Pattern 1: Load and Display Data
```typescript
const { data: prospects, isLoading, error } = useProspects();

if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage message={error.message} />;
if (!prospects || prospects.length === 0) return <EmptyState />;

return prospects.map(p => <ProspectRow key={p.id} prospect={p} />);
```

### Pattern 2: Submit Form with Optimistic Update
```typescript
const { mutate: submitForm, isPending } = useAdmitStudent();

const handleSubmit = async (formData) => {
  await performAsyncAction({
    operation: () => submitForm(formData),
    loadingMessage: "Admitting student...",
    successMessage: "Student admitted successfully",
    errorMessage: getErrorMessage
  });
};
```

### Pattern 3: Multi-Step Workflow
```typescript
const { data: student } = useStudent(studentId);
const { mutate: approveLeavr } = useApproveLeavePass();

// Each mutation uses React Query invalidation
// Automatically re-fetches related data on success
```

---

## STEP 2 Complete ✅

All infrastructure is in place. Ready for **STEP 3: Authentication & Dashboard Wiring**.

