# Gap Analysis Report: Frontend-Backend Integration
## Kenya Secondary School ERP System
**Date**: August 19, 2025 | **Status**: Pre-Integration Analysis

---

## EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| **Hardcoded Components** | 18 major pages/sections |
| **Mock Data Arrays** | 45+ hardcoded data sets |
| **Estimated Data Shape Mismatches** | 12+ fields |
| **Backend Endpoints Ready** | 60+ endpoints (PHASE 0-8) |
| **Missing Frontend Pages** | 5-7 endpoints without UI |
| **Authentication Required** | Yes (JWT Bearer token) |

---

## SECTION 1: HARDCODED DATA INVENTORY

### 1.1 Student Lifecycle (Admissions Module)

#### ProspectTracker Page
**Hardcoded**: ✓ YES
```javascript
const rows = [
  ["Amina Wanjiku Kariuki", "0712 345 678", "Form 1 · Stream A", <StatusTag />, "12 Jan 2025"],
  ["Brian Otieno Ouma", "0722 987 654", "Form 1 · Stream B", <StatusTag />, "18 Jan 2025"],
  // + 3 more students
];
```

**Backend Endpoint**: `GET /admissions/prospects?school_id={uuid}`
**Data Shape Mismatch**:
- Frontend expects: `["name", "contact", "class_stream", "status", "date"]`
- Backend returns: 
  ```
  {
    "id": "uuid",
    "first_name": "Amina",
    "last_name": "Wanjiku",
    "guardian_phone": "0712345678",
    "applied_class": "FORM_1",
    "applied_stream": "A",
    "prospect_status": "CLEARED",  // Enum, not "ok"/"warn"
    "created_at": "2025-01-12T00:00:00",
    "kcpe_marks": { ... },
    "expected_stream": "A"
  }
  ```

**Actions Required**:
1. Remove hardcoded `rows` array
2. Create `useProspects()` hook with `useQuery()`
3. Map `first_name + last_name` → single display string
4. Map `prospect_status` enum → `StatusTag variant`
5. Format `created_at` → display date

---

#### NewAdmission Page
**Hardcoded**: ✓ YES - UPI validation logic is mocked
```javascript
const handleUpiChange = (v: string) => {
  setUpiState("checking");
  setTimeout(() => {
    setUpiState(v === "123456789" ? "duplicate" : v.length >= 9 ? "valid" : "neutral");
  }, 800);
};
```

**Backend Endpoint**: `POST /admissions/students/admit` (atomic 10-step workflow)
**Payload Mismatch**:
- Frontend submits form data locally
- Backend expects:
  ```
  {
    "school_id": "uuid",
    "prospect_id": "uuid",  // From prospect tracker
    "prospective_upi": "12345678901",
    "first_name": "Amina",
    "last_name": "Wanjiku Kariuki",
    "date_of_birth": "2010-06-15",
    "gender": "FEMALE",
    "category": "BOARDER",  // Not "Boarder"
    "current_class": "FORM_1",
    "current_stream": "A",
    "kcpe_marks": 356,
    "boarding_status": "ACTIVE_BOARDER",
    "home_county": "Kisii",
    "emergency_contact_name": "Joseph Kariuki",
    "emergency_contact_phone": "+254712345678"
  }
  ```

**Actions Required**:
1. Remove mock UPI validation (setTimeout)
2. Wire form inputs to state
3. Create `useAdmitStudent()` mutation
4. Call backend `/admissions/students/admit` on submit
5. Handle 201 response with new student record
6. Redirect to student profile

---

#### StudentProfile Page
**Hardcoded**: ✓ YES - Tabs with mock data
```javascript
const [tab, setTab] = useState("overview");
const tabs = ["overview", "academic", "finance", "disciplinary", "boarding", "documents"];
// Each tab has hardcoded arrays
```

**Backend Endpoints**: 
- `GET /admissions/students/{student_id}` → Basic profile
- `GET /academics/assessment-entries?student_id={uuid}` → Academic marks
- `GET /finance/fee-accounts/{student_id}` → Fee balance & history
- `GET /boarding/discipline-cases?student_id={uuid}` → Discipline history
- `GET /boarding/leave-passes?student_id={uuid}` → Leave pass history
- `GET /admissions/documents/{student_id}` → Document status

**Data Shape Mismatch**:
- Frontend shows: `overview: { ...student }`, `academic: { ... }`, etc.
- Backend separates these across multiple routers
- Each router returns different response structure

**Actions Required**:
1. Create `useStudent(student_id)` hook for overview tab
2. Create separate hooks for each module:
   - `useStudentAcademics(student_id)`
   - `useStudentFees(student_id)`
   - `useStudentDiscipline(student_id)`
   - etc.
3. Add loading states per tab
4. Map backend responses to frontend display format

---

### 1.2 Finance Module

#### FeeLedger Page
**Hardcoded**: ✓ YES - Fee structure, balances, transactions
```javascript
const rows = [
  ["Tuition", "KES 45,000", "9,000/month", "KES 9,000", "KES 36,000", "ok"],
  ["Boarding", "KES 32,000", "6,400/month", "KES 6,400", "KES 25,600", "ok"],
  // More fee items...
];
```

**Backend Endpoint**: `GET /finance/fee-accounts/{student_id}`
**Response**:
```
{
  "student_id": "uuid",
  "term_id": "uuid",
  "current_term": "TERM_1",
  "current_year": 2025,
  "fee_account_lines": [
    {
      "fee_line_id": "uuid",
      "fee_item_name": "Tuition",
      "total_amount": Decimal("45000.00"),
      "amount_paid": Decimal("9000.00"),
      "amount_balance": Decimal("36000.00"),
      "invoices": [...]
    },
    // More lines
  ],
  "total_balance": Decimal("...)
}
```

**Actions Required**:
1. Remove hardcoded fee table
2. Create `useFeeAccount(student_id)` hook
3. Map backend `fee_account_lines` to table rows
4. Format `Decimal` → currency display (KES format)
5. Calculate status tag based on `amount_balance > 0`

---

#### GeneralLedger Page
**Hardcoded**: ✓ YES - Journal entries
```javascript
const entries = [
  { date: "2025-06-30", debit: "KES 45,000", credit: "—", account: "1110 · Bank Account" },
  // Hardcoded entries...
];
```

**Backend Endpoint**: `GET /finance/journals?school_id={uuid}&month={month}&year={year}`
**Response**:
```
{
  "entries": [
    {
      "id": "uuid",
      "entry_date": "2025-06-30",
      "journal_number": "JOU-2025-06-0147",
      "debit_account": { "id": "1110", "name": "Bank Account" },
      "credit_account": { "id": "4001", "name": "Tuition Fee Income" },
      "amount": Decimal("45000.00"),
      "description": "Tuition fee received via M-Pesa"
    }
  ]
}
```

**Actions Required**:
1. Create `useJournalEntries(month, year)` hook
2. Map response to table display
3. Add month/year filter controls (currently hardcoded to June 2025)
4. Format date and amount displays

---

### 1.3 HR & Payroll Module

#### PayrollRun Page
**Hardcoded**: ✓ YES - Salary calculations, deductions
```javascript
const months = ["January", "February", ...];
const staffMembers = [
  { name: "Alice Njoroge", role: "Principal", gross: "KES 185,000", ...deductions, net: "KES 145,230" },
  // More staff...
];
```

**Backend Endpoints**:
- `GET /hr/staff?school_id={uuid}` → List staff
- `POST /payroll/payroll-run/{school_id}/process` → Process payroll
- `GET /payroll/payroll-runs?school_id={uuid}&month={month}` → Retrieve runs

**Actions Required**:
1. Remove hardcoded staff array
2. Create `useStaff()` hook
3. Create `usePayrollRun(month, year)` hook
4. Implement payroll processing form
5. Add loading state during processing
6. Show results/errors on completion

---

### 1.4 Procurement Module

#### PurchaseRequisition Page
**Hardcoded**: ✓ YES - Line items, DOA routing
```javascript
const lineItems = [
  { itemCode: "OFFEXP-001", description: "Office Paper A4", qty: 50, unitCost: "KES 500", total: "KES 25,000" },
  // More items...
];
```

**Backend Endpoint**: `POST /procurement/purchase-requisitions`
**Payload**:
```
{
  "school_id": "uuid",
  "requisition_date": "2025-08-19",
  "requested_by_user_id": "uuid",
  "line_items": [
    {
      "item_description": "Office Paper A4",
      "quantity_requested": 50,
      "unit_of_measure": "REAMS",
      "unit_cost": Decimal("500.00"),
      "total_cost": Decimal("25000.00")
    }
  ]
}
```

**Actions Required**:
1. Remove hardcoded line items
2. Create form with dynamic line item additions
3. Wire form to `useCreateRequisition()` mutation
4. Show DOA approval routing logic based on total
5. Handle success response

---

### 1.5 Gate Security Module (PHASE 8)

#### GateConsole Page
**Hardcoded**: ✓ YES - Visitor check-in, student scanning
**No backend UI representation yet!** (Just built)

**Backend Endpoints**:
- `POST /security/gate/visitor/check-in`
- `POST /security/gate/scan-student-exit`
- `POST /security/gate/scan-student-entry`
- `GET /security/gate/audit-report`

**Actions Required**:
1. **CREATE NEW PAGE** for Gate Security console
2. Wire visitor check-in form to backend
3. Implement student scanner (ID input)
4. Show exit/entry authorization status
5. Display audit dashboard

---

### 1.6 Parent Portal (Mobile)

#### ParentPortal Page
**Hardcoded**: ✓ YES - Multiple tabs with mock data
- **Fees Tab**: Hardcoded balance, payment history
- **Academic Tab**: Hardcoded grades
- **Notifications Tab**: Hardcoded messages
- **Contact Tab**: School contact (mostly static)

**Backend Endpoints**:
- `GET /finance/fee-accounts/{student_id}` → Fee balance
- `GET /academics/assessment-entries?student_id={uuid}` → Grades
- `GET /communication/logs?recipient_id={uuid}` → Notifications

**Actions Required**:
1. Wire each tab to corresponding backend endpoint
2. Create parent authentication flow (separate from staff)
3. Filter data to show only their child's info
4. Add real-time notification display

---

### 1.7 Audit Log Page

#### AuditLog Page
**Hardcoded**: ✓ YES - 5 hard-coded audit entries
```javascript
const entries = [
  { ts: "2025-06-15 08:00:00", user: "System", action: "PAYROLL_RUN_COMMIT", entity: "Payroll:June-2025", before: "draft", after: "committed" },
  // More entries...
];
```

**Backend Endpoint**: `GET /audit/audit-logs?school_id={uuid}&limit=100&offset=0`

**Actions Required**:
1. Create `useAuditLogs()` hook
2. Wire table to backend
3. Add filtering and pagination
4. Format timestamp and action display

---

### 1.8 NEMIS Export Page

#### NemisExport Page
**Hardcoded**: ✓ YES - Validation and flagged records
```javascript
const flaggedRecords = [
  { adm: "ADM-2024-0188", name: "Brian O. Ouma", issue: "UPI format invalid" },
  // More records...
];
```

**Backend Endpoint**: `POST /nemis/validate-export`

**Actions Required**:
1. Create validation form
2. Wire to backend validation endpoint
3. Display flagged records
4. Wire "Fix in Profile" button to student profile edit
5. Show export file download when no errors

---

## SECTION 2: BACKEND ENDPOINTS WITHOUT FRONTEND UI

| Endpoint | Module | Status | Frontend Gap |
|----------|--------|--------|-------------|
| `GET /boarding/leave-passes/{student_id}` | Boarding | Ready | No dedicated UI page |
| `POST /boarding/leave-passes/approve` | Boarding | Ready | No approval UI |
| `GET /boarding/exeat-queue` | Boarding | Ready | No queue display page |
| `GET /boarding/bed-allocations` | Boarding | Ready | No bed allocation UI |
| `GET /security/gate/audit-report` | Gate Security | Ready | No dashboard |
| `POST /inventory/stock-issue` | Inventory | Ready | No stock issuance UI |
| `GET /communication/batches/{id}/report` | Communications | Ready | No report UI |

---

## SECTION 3: DATA SHAPE MISMATCHES & TRANSFORMATIONS

### 3.1 Student Name Handling
**Frontend**: Single field `name: "Amina Wanjiku Kariuki"`
**Backend**: Separate fields `first_name: "Amina"`, `last_name: "Wanjiku Kariuki"`
**Transformation**:
```typescript
const displayName = `${student.first_name} ${student.last_name}`.trim();
```

### 3.2 Status Enums
**Frontend**: `StatusTag variant="ok" | "warn" | "bad" | "neutral"`
**Backend**: Various enum types:
- `ProspectStatus = "CLEARED" | "INTERVIEW" | "DOCUMENTS_PENDING" | "OFFER_SENT" | "ENQUIRY"`
- `LeavePassStatus = "REQUESTED" | "APPROVED" | "REJECTED" | "DEPARTED" | "RETURNED"`

**Transformation Map**:
```typescript
const prospectStatusMap = {
  "CLEARED": "ok",
  "INTERVIEW": "warn",
  "DOCUMENTS_PENDING": "warn",
  "OFFER_SENT": "warn",
  "ENQUIRY": "neutral",
};
```

### 3.3 Decimal Amounts
**Frontend**: String format `"KES 45,000"`
**Backend**: Pydantic `Decimal("45000.00")` via JSON as string

**Transformation**:
```typescript
const formatCurrency = (amount: string | number) => {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    minimumFractionDigits: 0,
  }).format(num);
};
```

### 3.4 Date/Time Formats
**Frontend**: Display `"12 Jan 2025"` or `"2025-06-15 08:00:00"`
**Backend**: ISO 8601 `"2025-01-12T00:00:00"` or `"2025-06-15T08:00:00"`

**Transformation**:
```typescript
const formatDate = (iso: string) => 
  new Date(iso).toLocaleDateString("en-KE", { 
    day: "numeric", month: "short", year: "numeric" 
  });

const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString("en-KE", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
```

### 3.5 Category/Stream Enums
**Frontend**: Display `"Form 1 · Stream A"`
**Backend**: Separate enums `Class = "FORM_1"`, `Stream = "A"`

**Transformation**:
```typescript
const classNames = { "FORM_1": "Form 1", "FORM_2": "Form 2", /* ... */ };
const displayClassStream = `${classNames[student.current_class]} · Stream ${student.current_stream}`;
```

---

## SECTION 4: AUTHENTICATION REQUIREMENTS

### Current Frontend State
- **No authentication flow implemented**
- **No JWT token storage**
- **No protected routes**

### Backend Requirements
**All endpoints require**:
- `Authorization: Bearer {jwt_token}` header
- Valid JWT token in request
- Automatic 401 response if missing/invalid

### Frontend Setup Needed
1. **Login page** (or OAuth integration)
2. **JWT token storage** in localStorage/httpOnly cookie
3. **Request interceptor** to auto-attach Bearer token
4. **Response interceptor** for 401 → logout flow
5. **Protected routes** wrapper

---

## SECTION 5: API CLIENT INFRASTRUCTURE MISSING

### Current State
- **No centralized API client**
- **No HTTP interceptors**
- **No error handling**
- **No retry logic**

### Required Setup
1. **`services/api.ts`** - Axios or Fetch-based client
2. **Request interceptor** - Auto-attach Bearer token
3. **Response interceptor** - Handle 401, 403, 500 errors
4. **Error boundary** - Catch and display API errors
5. **React Query** - State management for API calls

---

## SECTION 6: MISSING ENVIRONMENT CONFIGURATION

### Frontend `.env` needed
```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME="Nambale ERP"
VITE_SCHOOL_ID=<uuid-will-come-from-login>
```

### Backend CORS configuration
- Allow requests from `http://localhost:5173`
- Allow `Authorization` header
- Allow credentials

---

## SECTION 7: IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Step 2)
- [ ] Create `services/api.ts` with Axios client
- [ ] Implement JWT token storage & retrieval
- [ ] Add request/response interceptors
- [ ] Create error handling utilities

### Phase 2: Authentication (Step 3a)
- [ ] Create login page
- [ ] Implement auth flow
- [ ] Protect routes
- [ ] Add logout functionality

### Phase 3: Core Wiring (Step 3b onwards)
**Tier 1 (Highest Priority)**:
1. Principal/Bursar Dashboard → KPI cards
2. ProspectTracker → Backend list & search
3. NewAdmission → Atomic admission flow
4. StudentProfile → Multi-tab data loading

**Tier 2 (High Priority)**:
5. FeeLedger → Fee account display
6. PayrollRun → Staff list & processing
7. PurchaseRequisition → Line items & submission

**Tier 3 (Medium Priority)**:
8. GeneralLedger → Journal entry display
9. GateConsole → Visitor & student scanning
10. AuditLog → Filtering & pagination

**Tier 4 (Lower Priority)**:
11. ParentPortal → Mobile view
12. NemisExport → Validation flow
13. TransfersClearance → Approval workflow
14. HODMarkReview → Mark locking

---

## SUMMARY TABLE

| Component | Has Hardcoded Data | Backend Ready | Data Mismatch | Priority |
|-----------|-------------------|---------------|---------------|----------|
| ProspectTracker | ✓ YES | ✓ YES | Minor (name, status) | P0 |
| NewAdmission | ✓ YES | ✓ YES | Moderate (form payload) | P0 |
| StudentProfile | ✓ YES | ✓ YES (multi-endpoint) | Major (cross-module) | P0 |
| FeeLedger | ✓ YES | ✓ YES | Minor (currency format) | P1 |
| GeneralLedger | ✓ YES | ✓ YES | Minor (date format) | P2 |
| PayrollRun | ✓ YES | ✓ YES | Moderate (form) | P1 |
| PurchaseRequisition | ✓ YES | ✓ YES | Moderate (line items) | P1 |
| HODMarkReview | ✓ YES | ✓ YES | Minor (lock action) | P2 |
| TransfersClearance | ✓ YES | ✓ YES | Minor (workflow display) | P2 |
| AuditLog | ✓ YES | ✓ YES | Minor (timestamp) | P2 |
| NemisExport | ✓ YES | ✓ YES | Moderate (validation) | P3 |
| ParentPortal | ✓ YES | ✓ YES (multi-tab) | Moderate (access control) | P2 |
| **GateConsole** | ✗ NO | ✓ YES | N/A - NEW | P1 |
| **LeavePassApproval** | ✗ NO | ✓ YES | N/A - NEW | P1 |
| **BedAllocation** | ✗ NO | ✓ YES | N/A - NEW | P2 |

---

## NEXT STEPS

1. **User Confirmation**: Review this gap analysis
2. **Step 2 Execution**: Build centralized API client + auth setup
3. **Step 3 Execution**: Wire Prospect Tracker + NewAdmission + StudentProfile
4. **Iterate**: Proceed module by module per Tier priorities

