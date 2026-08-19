# Appendix 3: Business Rules, Events & Information Entities
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Business Rules Catalogue
Business rules define the constraints and operational policies that the ERP must enforce. These are independent of software implementation and reflect Kenyan school governance.

### 1.1. Admissions & Enrollment Rules
*   **RULE-ADM-001:** A student must possess a valid, non-duplicated Unique Personal Identifier (UPI) from NEMIS to be classified as "Enrolled".
*   **RULE-ADM-002:** A student transferring from another secondary school must present a digital clearance certificate before admission is finalized.
*   **RULE-ADM-003:** Total enrollment per stream/class cannot exceed 50 students without explicit approval from the Principal.

### 1.2. Financial Rules
*   **RULE-FIN-001:** No student with a fee balance exceeding 20% of the current term's billing can be marked as "Cleared for Reporting" on Opening Day, unless an explicit waiver is granted by the Principal.
*   **RULE-FIN-002:** All incoming payments must clear historical arrears before being applied to current term balances.
*   **RULE-FIN-003:** Ministry Capitation funds must be strictly allocated to their designated MOE Vote Heads (e.g., Tuition, RMI) and cannot be re-appropriated to unrelated Vote Heads (e.g., Boarding).
*   **RULE-FIN-004:** Any financial journal entry modification after period-end closing requires a logged override by the BOM Finance Chair.

### 1.3. Procurement & Supply Chain Rules
*   **RULE-PRO-001:** A Purchase Requisition cannot be converted to a Local Purchase Order (LPO) if it exceeds the remaining budget for the selected Vote Head.
*   **RULE-PRO-002:** 3-Way Matching (LPO + Goods Received Note + Invoice) is mandatory for all supplier payments exceeding KES 5,000.
*   **RULE-PRO-003:** Kitchen stores cannot be issued without an approved daily requisition matched to the student population present on that day.

### 1.4. Academic & Assessment Rules
*   **RULE-ACA-001:** CBC assessments must strictly use the standardized 1-4 scale (1: Below, 2: Approaching, 3: Meeting, 4: Exceeding).
*   **RULE-ACA-002:** 8-4-4 summative assessments must map numeric marks (0-100) to the standard 12-point KNEC grading system (A to E).
*   **RULE-ACA-003:** A teacher cannot finalize a subject's termly assessment if any active student assigned to that class has a blank score (must be explicitly marked "Absent" if missed).

### 1.5. Disciplinary & Security Rules
*   **RULE-SEC-001:** Only the Principal or Deputy Principal can authorize a formal suspension.
*   **RULE-SEC-002:** A student on active suspension is automatically barred from gate exit (if caught trying to leave again) and gate entry (until suspension duration is complete and parent is present).
*   **RULE-SEC-003:** No student may exit the gate during term-time without a digital leave pass that has been approved within the last 12 hours.

---

## 2. Business Events Catalogue
Business events represent significant state changes within the school's operational lifecycle that trigger specific downstream actions.

| Event ID | Event Name | Trigger Condition | Consequent Actions / Outcomes |
| :--- | :--- | :--- | :--- |
| **EVT-01** | **Term Commencement** | System date reaches Term Start Date. | Fee structures applied to student accounts; Gate transitions to "Reporting Mode"; Attendance registers reset. |
| **EVT-02** | **Student Admission** | Admission data entry completed and UPI validated. | Initial fee invoice generated; Student added to class roster; Welcome SMS sent to parent. |
| **EVT-03** | **Fee Payment Received** | M-Pesa API payload received or Bank File uploaded. | Payment allocated to arrears/current balance; Receipt generated; SMS sent to parent; General Ledger updated. |
| **EVT-04** | **Leave Pass Approved** | Deputy Principal approves leave request. | Gate exit authorized; Boarding roster updated; SMS queued for dispatch upon physical exit. |
| **EVT-05** | **Goods Received** | Storekeeper logs physical delivery of LPO items. | GRN generated; Inventory levels increased; Accounts Payable liability created. |
| **EVT-06** | **Disciplinary Escalation** | Student receives 3 minor infractions within a term. | Automatic alert sent to Deputy Principal; Parent summoned via SMS. |
| **EVT-07** | **End of Financial Year** | System date reaches December 31st. | Financial ledgers locked; Depreciation calculated on fixed assets; Retained earnings carried forward. |

---

## 3. Business Information Requirements (Entities)
To avoid defining database schemas (tables/columns), this section defines the *Conceptual Business Entities*—the core objects the school must track and manage.

*   **Student Entity:** Represents a learner. Must hold UPI, biographical data, medical flags, and links to parents.
*   **Parent/Guardian Entity:** Represents the financial sponsor and emergency contact. Must hold verifiable phone numbers for SMS.
*   **Staff Entity:** Represents teaching (TSC/BOM) and non-teaching personnel. Must hold TPAD numbers (for teachers), KRA PINs, and payroll details.
*   **Class/Stream Entity:** Represents a grouping of students. Linked to a Class Teacher and a specific academic year.
*   **Subject/Strand Entity:** Represents a unit of learning (e.g., Mathematics [8-4-4] or Environmental Activities [CBC]).
*   **Financial Account Entity:** Represents a node in the Chart of Accounts (e.g., Asset, Liability, Revenue, Expense).
*   **Fee Vote Head Entity:** Represents a specific fee category mandated by the MOE (e.g., Tuition, Activity, RMI).
*   **LPO Entity:** Represents a legal commitment to purchase goods from a Supplier.
*   **Asset Entity:** Represents a physical fixed asset (e.g., School Bus, Laboratory Equipment) requiring tracking and depreciation.
*   **Leave Pass Entity:** Represents a time-bound authorization for a student or staff member to be absent.
