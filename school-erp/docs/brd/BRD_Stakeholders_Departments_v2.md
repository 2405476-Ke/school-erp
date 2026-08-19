# Appendix 1: Stakeholders, Departments, and Integrations
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Expanded Stakeholder Analysis
To ensure enterprise-wide adoption, every stakeholder's needs, pain points, and required business decisions must be mapped.

### 1.1. Internal Stakeholders
| Stakeholder | Responsibilities | Objectives & Business Goals | Pain Points | Information Needs / Decisions Supported | Interactions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Board of Management (BOM)** | Strategic oversight, financial approval, capital expenditure authorization. | Ensure financial sustainability, compliance, and academic excellence. | Lack of real-time, consolidated financial reporting; delayed awareness of critical risks. | Executive dashboards, Trial Balance, Audit Reports. Decisions on budget approval and fee structures. | Principal, Auditors, Finance Office. |
| **Principal** | Overall institutional leadership, accountability to MOE, final disciplinary authority. | Centralize control, improve school ranking, ensure zero compliance gaps. | Overwhelmed by administrative bottlenecks (signing paper passes, cheques) and fragmented data. | Aggregated attendance, financial health, staff performance metrics. Decisions on staff deployment and suspensions. | All departments, BOM, MOE, TSC, Parents. |
| **Deputy Principal (Administration)** | Day-to-day operations, discipline, boarding oversight, staff leave approval. | Maintain order, ensure smooth operational logistics. | Tracking student whereabouts; managing manual staff leave requests. | Disciplinary logs, duty rosters, daily absentee lists. Decisions on minor disciplinary actions and staff cover. | Principal, Teachers, Boarding Master, Security. |
| **Deputy Principal (Academics)** | Curriculum implementation, timetable optimization. | Maximize contact hours, ensure syllabus coverage (CBC/8-4-4). | Timetable clashes; merging distinct grading systems. | Teacher attendance, syllabus coverage reports, aggregate performance. Decisions on subject combinations. | Principal, HODs, Teachers, KNEC. |
| **Finance Officer / Bursar** | Budget execution, fee collection, payroll, statutory reporting. | Eliminate cash leakages, automate bank reconciliations. | Manual reconciliations take weeks; tracing M-Pesa payments to specific students. | Bank statements, Accounts Payable aging, Fee Arrears. Decisions on supplier payments. | Principal, Parents, Stores, Banks. |
| **Heads of Department (HODs)** | Subject coordination, departmental budgeting, teacher supervision. | Improve subject mean score; ensure adequate teaching materials. | Lack of data to analyze historical subject performance trends. | Subject-specific performance analytics, departmental budget utilization. | Deputy (Academics), Teachers, Stores. |
| **Teachers / Class Teachers** | Lesson delivery, continuous assessment, roll call, initial pastoral care. | Maximize teaching time; fast entry of competency rubrics. | Time-consuming manual roll calls, manual generation of termly report cards. | Student profiles, medical flags, previous academic records. Decisions on formative assessment ratings. | Students, HODs, Parents. |
| **Boarding Master/Mistress** | Dorm allocation, evening supervision, student welfare. | Maximize bed utilization, ensure safety outside class hours. | Knowing exactly who is authorized to be absent from the dorm. | Real-time leave pass data, medical excusals. Decisions on dorm transfers. | Students, Security, Nurse. |
| **Procurement / Stores Officer** | Inventory control, LPO generation, receiving goods. | Prevent stockouts of critical items (e.g., food, chemicals); prevent shrinkage. | Manual tracking of stock levels; unauthorized requisitions. | Reorder level alerts, approved budgets. Decisions on raising LPOs. | Finance, Suppliers, Kitchen, HODs. |
| **Gate Officers / Security** | Managing physical entry/exit, visitor logging. | Secure the perimeter; process students rapidly to avoid congestion. | Verifying physical leave chits (easily forged); manual logbooks. | Real-time list of authorized leave/suspensions. Decisions on granting physical access. | Students, Visitors, Administration. |
| **School Nurse / Clinic** | Managing student health, dispensing medication, authorizing medical leave. | Rapid response to health issues; maintaining confidential health records. | Lack of medical history access; manual communication with boarding. | Allergies, past treatments, emergency contacts. Decisions on medical leave. | Students, Boarding, Principal, Parents. |

### 1.2. External Stakeholders
| Stakeholder | Responsibilities | Objectives & Business Goals | Pain Points | Information Needs / Decisions Supported | Interactions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Parents / Guardians** | Paying fees, supporting academic progression, attending meetings. | Transparency in billing; real-time updates on student welfare. | Surprised by fee balances at term end; unaware of disciplinary issues. | Digital fee statements, automated academic and disciplinary SMS alerts. | Finance, Teachers, Administration. |
| **Ministry of Education (MOE)** | Policy enforcement, Capitation disbursement. | Accurate national enrollment data; proper utilization of public funds. | "Ghost learners" inflating capitation requests; delayed NEMIS updates. | Verified UPI enrollment counts, categorized by gender and class. | Principal, BOM. |
| **Teachers Service Commission (TSC)** | Teacher employment, deployment, and appraisal. | Monitor teacher attendance and professional development. | Lack of localized, verified attendance data for TPAD. | TPAD data, daily teacher clock-in logs. | Principal, Teachers. |
| **Kenya National Examinations Council (KNEC)** | Administering national assessments (KPSEA, KCSE). | Secure, accurate registration of candidates and continuous assessment marks. | Errors in manual data upload of candidate details. | Formatted candidate data exports, continuous assessment files. | Deputy (Academics). |
| **Suppliers / Vendors** | Providing goods and services (food, stationery, transport). | Timely payment, clear procurement requirements. | Lost physical invoices; opaque payment timelines. | Digital Purchase Orders (LPOs), payment remittance advice. | Procurement, Finance. |
| **Auditors (Internal/External)** | Ensuring financial compliance and statutory adherence. | Transparent, immutable financial trails. | Digging through disorganized physical vouchers and receipts. | System-generated Trial Balance, General Ledger transaction logs. | BOM, Finance Office. |

---

## 2. Department Analysis
This section analyzes the distinct business needs of operational units within the school ecosystem.

### 2.1. Academics Department
*   **Responsibilities:** Curriculum delivery, timetabling, examinations, student performance tracking.
*   **Business Needs:** A robust scheduling engine that handles both 8-4-4 subject blocking and CBC pathway requirements. An assessment engine capable of calculating standard mean grades (A to E) alongside competency scales (Exceeding, Meeting, Approaching, Below).
*   **Success Measures:** 100% automated report card generation within 24 hours of deadline. Zero timetable clashes.

### 2.2. Finance & Accounting
*   **Responsibilities:** Full cycle accounting, fee collection, payroll, treasury management.
*   **Business Needs:** Enterprise-grade double-entry accounting. Automated matching of M-Pesa/Bank feeds to student IDs via APIs. Strict Maker-Checker workflows for all expenditure.
*   **Success Measures:** Zero unallocated deposits. End-of-month financial closing completed within 3 business days.

### 2.3. Administration & Boarding
*   **Responsibilities:** Daily logistics, student accommodation, discipline, leave management.
*   **Business Needs:** A digital leave management workflow integrated with the gate. A visual, real-time dashboard of bed occupancy.
*   **Success Measures:** 100% accuracy in real-time student location tracking (In Class, In Dorm, On Leave).

### 2.4. Supply Chain (Procurement & Stores)
*   **Responsibilities:** Sourcing, purchasing, inventory management, asset tagging.
*   **Business Needs:** Automated reorder level triggers. Strict budgetary controls linking LPOs to approved Vote Heads. Fixed asset registers calculating automated depreciation.
*   **Success Measures:** Zero stockouts of critical supplies. 100% traceability from Requisition to Invoice to Payment.

---

## 3. Cross-Department Integration Matrices
To achieve a true Enterprise Resource Planning environment, departments cannot operate in silos. The matrix below defines the critical business information flows between departments.

| Source Department | Target Department | Information Flow / Business Event | Business Value / Outcome |
| :--- | :--- | :--- | :--- |
| **Admissions** | **Finance** | New student registration data (Name, UPI, Grade). | Triggers automated generation of the first fee invoice based on fee structure. |
| **Finance** | **Gate/Security** | Fee clearance status / Arrears flags. | Gate officer immediately knows if a returning student meets the reporting threshold. |
| **Administration** | **Gate/Security** | Approved Digital Leave Pass. | Validates student exit at the gate; updates global attendance status. |
| **Clinic/Nurse** | **Boarding** | Student admitted to sickbay / Medical leave granted. | Informs the Boarding Master why a student is absent during evening roll call. |
| **Academics** | **Administration** | Disciplinary referral (e.g., cheating, absenteeism). | Triggers formal disciplinary workflow (Summons, Suspension process). |
| **Stores/Inventory** | **Finance** | Goods Received Note (GRN) generated upon delivery. | Triggers Accounts Payable liability creation; allows Finance to match Invoice to PO and GRN (3-way match). |
| **Academics** | **Parents (via Comm Portal)** | End of Term Assessment finalization. | Automatically publishes results to parent portal and sends SMS summary. |
| **Finance** | **Parents (via Comm Portal)** | Payment Receipt generated / Termly Invoice created. | Instant SMS notification of payment applied; proactive arrears reminders. |
