# Appendix 2: Processes & Capabilities
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Business Capability Model (Level-3 Decomposition)
The capability model outlines *what* the enterprise must do, independent of *how* it does it. This hierarchical map ensures every business requirement maps to a core capability.

### 1.1. Core Academic & Student Capabilities
*   **1.0 Academic Management**
    *   1.1 Curriculum Management
        *   1.1.1 CBC Pathway Modeling
        *   1.1.2 8-4-4 Subject Combinations
    *   1.2 Timetable Optimization
        *   1.2.1 Resource Allocation (Rooms, Teachers)
        *   1.2.2 Clash Detection & Resolution
    *   1.3 Assessment & Grading
        *   1.3.1 Formative Assessment Tracking (CBC)
        *   1.3.2 Summative Grading (8-4-4)
        *   1.3.3 National Exam Registration (KNEC)
    *   1.4 Attendance Tracking
        *   1.4.1 Daily Roll Call
        *   1.4.2 Lesson-by-Lesson Attendance
*   **2.0 Student Lifecycle Management**
    *   2.1 Admissions Management
        *   2.1.1 Prospect Tracking
        *   2.1.2 Interview & Selection
        *   2.1.3 Enrollment & UPI Allocation
    *   2.2 Progression & Promotion
        *   2.2.1 Automated Class Transitions
        *   2.2.2 Retention/Repeating Logic
    *   2.3 Disciplinary & Pastoral Care
        *   2.3.1 Incident Logging
        *   2.3.2 Guidance & Counselling Records
        *   2.3.3 Suspension/Expulsion Processing
    *   2.4 Alumni Management
        *   2.4.1 Clearance & Graduation
        *   2.4.2 Alumni Tracking

### 1.2. Corporate & Administrative Capabilities
*   **3.0 Enterprise Financial Management**
    *   3.1 Student Billing & Receivables
        *   3.1.1 Fee Structure Generation
        *   3.1.2 Receipting & M-Pesa Integration
        *   3.1.3 Bursary & Scholarship Allocation
    *   3.2 General Ledger & Accounting
        *   3.2.1 Chart of Accounts Management
        *   3.2.2 Journal Entry & Reconciliation
        *   3.2.3 Period Closing (Month/Year-End)
    *   3.3 Procurement & Payables
        *   3.3.1 Requisition Processing
        *   3.3.2 Purchase Order (LPO) Generation
        *   3.3.3 Supplier Payment Processing
    *   3.4 Budgeting & Capitation
        *   3.4.1 Vote Head Management
        *   3.4.2 Capitation Tracking (NEMIS)
*   **4.0 Human Capital Management**
    *   4.1 Core HR
        *   4.1.1 Staff Records (TSC & BOM Staff)
        *   4.1.2 Contract Management
    *   4.2 Leave & Attendance
        *   4.2.1 Staff Biometric Clock-in
        *   4.2.2 Leave Request Workflow
    *   4.3 Payroll Management
        *   4.3.1 Salary Processing
        *   4.3.2 Statutory Deductions (KRA, NSSF, NHIF)
*   **5.0 Campus Operations & Security**
    *   5.1 Boarding Management
        *   5.1.1 Dormitory & Bed Allocation
        *   5.1.2 Evening Muster Roll
    *   5.2 Inventory & Asset Management
        *   5.2.1 Central Stores Requisitions
        *   5.2.2 Fixed Asset Depreciation
    *   5.3 Gate & Access Control
        *   5.3.1 Digital Leave Pass Verification
        *   5.3.2 Visitor Logging

---

## 2. Expanded Business Process Analysis
Documenting the step-by-step business flows. *(Note: Selected critical processes shown below as representative examples of the 40+ mapped processes).*

### 2.1. Process: End-to-End Student Admission (P-ADM-01)
*   **Purpose:** To systematically register a new student, allocate them to a class, and generate their initial fee invoice.
*   **Trigger:** Parent accepts admission offer and provides NEMIS UPI.
*   **Inputs:** Birth Certificate, KCPE results, previous school leaving certificate, NEMIS UPI.
*   **Activities:**
    1.  Data Entry Clerk creates a digital profile using the UPI.
    2.  System validates UPI format to prevent duplicates.
    3.  Deputy Principal allocates student to a Stream/Class.
    4.  System automatically generates the Term 1 Fee Invoice based on the assigned class and boarding status.
    5.  Bursar confirms receipt of admission fees.
    6.  System updates global active student count.
*   **Business Rules:** A student cannot be assigned an "Active" status until the minimum admission fee threshold is met. Duplication of NEMIS UPIs is strictly blocked.
*   **Outputs:** Active Student Profile, Class Roster Update, Initial Fee Invoice, Automated Welcome SMS to Parent.
*   **Exceptions:** If UPI is already registered to another active school in KEMIS, admission is placed in a "Pending Transfer" state.
*   **KPIs:** Processing time per admission < 5 minutes.
*   **Success Criteria:** 100% of newly admitted students appear on the billing run and class register immediately.

### 2.2. Process: Procure-to-Pay (P-PRO-01)
*   **Purpose:** To manage the secure acquisition of goods from requisition to supplier payment.
*   **Trigger:** Department head identifies a need (e.g., Science HOD needs lab chemicals).
*   **Inputs:** Supplier Quotes, Budget Availability.
*   **Activities:**
    1.  HOD creates a Purchase Requisition.
    2.  System checks against the remaining budget for that specific Vote Head.
    3.  Bursar reviews and forwards to Principal for Tier-2 approval.
    4.  System generates a digitally signed Local Purchase Order (LPO).
    5.  Storekeeper receives goods and generates a Goods Received Note (GRN) in the system.
    6.  Supplier Invoice is matched against LPO and GRN (3-Way Match) by Accounts Clerk.
    7.  Bursar authorizes payment.
*   **Business Rules:** 3-Way matching is mandatory for any payment exceeding KES 5,000. Requisitions exceeding available budget are hard-stopped unless a budget reallocation is approved by the BOM.
*   **Outputs:** Approved LPO, GRN, Payment Remittance, updated General Ledger.
*   **Exceptions:** Goods delivered do not match LPO -> GRN is rejected, payment is halted.
*   **KPIs:** Requisition-to-LPO approval time < 24 hours.
*   **Success Criteria:** Zero payments made without a corresponding authorized LPO and GRN.

### 2.3. Process: CBC Formative Assessment (P-ACA-02)
*   **Purpose:** To capture and report on student competencies in alignment with MOE CBC guidelines.
*   **Trigger:** Completion of a learning strand/topic.
*   **Inputs:** Teacher's observational notes, practical exam results.
*   **Activities:**
    1.  Teacher selects the Class, Subject, and specific Competency Strand.
    2.  System displays class roster.
    3.  Teacher inputs rating (1-4) for each student.
    4.  System aggregates ratings across multiple strands for the term.
    5.  Class Teacher reviews the aggregated rubric.
    6.  Deputy Principal approves for publishing.
*   **Business Rules:** Ratings must strictly follow the 1 (Below Expectation) to 4 (Exceeding Expectation) scale. A strand cannot be finalized if any active student has a blank rating.
*   **Outputs:** Strand Competency Report, Aggregated Termly CBC Report Card.
*   **Exceptions:** Student was absent for the entire strand -> Marked as "Not Assessed".
*   **KPIs:** 100% of strands rated before the end-of-term deadline.
*   **Success Criteria:** Report cards generated perfectly match the KNEC CBC portal upload requirements.

### 2.4. Process: Student Leave & Gate Exit (P-SEC-01)
*   **Purpose:** To securely process a student leaving the school compound during term time.
*   **Trigger:** Medical emergency or parent request for absence.
*   **Inputs:** Medical note or Parent SMS request.
*   **Activities:**
    1.  Class Teacher or Nurse initiates a Leave Request in the system.
    2.  Deputy Principal approves the request.
    3.  System generates a Digital Leave Pass (QR Code / System Alert).
    4.  Student arrives at Gate.
    5.  Gate Officer scans student ID or enters Admission Number.
    6.  System displays "Authorized to Leave".
    7.  Gate Officer clicks "Process Exit".
    8.  System instantly sends SMS to parent: "Your child has left the school premises."
*   **Business Rules:** Gate exit is hard-stopped unless an active Digital Leave Pass exists. 
*   **Outputs:** Gate Log Entry, SMS to Parent, updated Boarding Roster (Marked Absent).
*   **Exceptions:** System offline -> Gate officer uses a pre-printed emergency override log which must be entered into the system within 2 hours of power restoration.
*   **KPIs:** Gate processing time < 10 seconds.
*   **Success Criteria:** Zero unauthorized student exits.
