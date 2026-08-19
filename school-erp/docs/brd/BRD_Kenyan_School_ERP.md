# Business Requirements Document (BRD)
**Project Name:** Kenya Secondary School Enterprise Resource Planning (ERP) Platform
**Document Version:** 1.0
**Date:** August 2026

---

## 1. Executive Summary
The Kenya Secondary School Enterprise Resource Planning (ERP) Platform is a strategic initiative designed to digitally transform the operations of secondary schools across Kenya. Supporting a diverse range of institutions—from National to Sub-County, boarding to day, and public to private—this ERP aims to become the central operating system for all institutional functions. By replacing disparate, paper-based processes with an integrated ecosystem, the platform will enable comprehensive financial management, streamline academic administration during the transition from the 8-4-4 system to the Competency-Based Curriculum (CBC), ensure seamless regulatory compliance with Ministry of Education standards (e.g., NEMIS/KEMIS), and significantly enhance student safety and parent engagement.

## 2. Business Background
The project originated from a grassroots innovation proposed by a student at Nambale Secondary School. The initial observation highlighted a critical operational bottleneck: severe congestion at school gates caused by the manual verification of students during reporting and dismissal periods. The original concept—to digitize student entry and exit—exposed a broader reality. Schools operate using highly fragmented, paper-heavy systems that cause delays, data inaccuracies, and operational inefficiencies across all departments. What began as a targeted solution for gate management has evolved into a strategic vision for a comprehensive School ERP capable of managing the entire institutional ecosystem.

## 3. Problem Statement
Kenyan secondary schools currently face significant administrative, financial, and regulatory challenges due to reliance on manual workflows and disconnected digital tools. Key problems include:
*   **Operational Inefficiencies:** Manual gate verification, paper-based attendance, and physical leave requests lead to massive time wastage.
*   **Financial Leakage and Inaccuracy:** Disconnected fee collection systems and manual reconciliation result in poor debt management, financial leakage, and delayed reporting.
*   **Regulatory Burden:** Managing the dual requirements of the outgoing 8-4-4 curriculum and the incoming CBC, alongside manual data entry into government portals (NEMIS/KEMIS), creates immense strain on school administrators and leads to data discrepancies (e.g., "ghost learners").
*   **Information Silos:** Departments (Finance, Academics, Boarding, Stores) operate in isolation, making it impossible for the Principal and Board of Management to have a real-time, holistic view of the institution.

## 4. Vision
To provide Kenyan secondary schools with a unified, intelligent, and secure central operating system that seamlessly connects every department, empowers educators, ensures strict financial governance, and guarantees regulatory compliance, ultimately fostering an environment focused on educational excellence rather than administrative overhead.

## 5. Objectives
| Objective | Current Problem | Desired Business Outcome | Expected Measurable Value |
| :--- | :--- | :--- | :--- |
| **Improve operational efficiency** | Manual processes cause delays (e.g., gate congestion, manual clearance). | Automated workflows across all departments. | 50% reduction in time spent on administrative processes. |
| **Eliminate paper-based processes** | High cost of printing, physical storage, and risk of document loss. | Fully digitized record-keeping and approval chains. | 80% reduction in paper and printing costs. |
| **Improve accountability & transparency** | Lack of audit trails in finance, procurement, and stores. | Clear, immutable records of all transactions and approvals. | Zero unaccounted financial discrepancies during audits. |
| **Improve student safety** | Manual tracking of student whereabouts (gate, boarding, class). | Real-time tracking of student movement and attendance. | 100% accuracy in real-time student location reporting. |
| **Improve financial management** | Fragmented fee collection and manual bookkeeping. | A comprehensive accounting system integrated with fee collection. | 30% increase in fee collection efficiency; zero reconciliation delays. |
| **Improve regulatory compliance** | Manual reporting to KNEC, TSC, and NEMIS/KEMIS leads to errors. | Automated, accurate data formatting and reporting. | 100% compliance with MOE reporting timelines; elimination of "ghost learner" discrepancies. |
| **Improve academic outcomes** | Difficulties in tracking CBC competencies alongside 8-4-4 metrics. | Holistic academic tracking and formative assessment management. | Teachers spend 40% less time on manual grading/reporting. |
| **Improve parent engagement** | Parents lack real-time visibility into student performance and fee balances. | Proactive communication via SMS/Portals. | 90% of parents receive automated weekly updates. |

## 6. Scope
### 6.1. In Scope
*   End-to-end student lifecycle management (admission to alumni).
*   Comprehensive academic tracking for both CBC and 8-4-4 curricula.
*   Full-suite financial accounting, including fee management, procurement, ledger, and asset management.
*   Human resources and payroll management for teaching and non-teaching staff.
*   Operational management including boarding, transport, library, and inventory/stores.
*   Gate and visitor management.
*   Automated communication (SMS/Email) with stakeholders.
*   Standardized compliance reporting for Kenyan educational bodies.

### 6.2. Out of Scope
*   Provision of e-learning content or Learning Management System (LMS) instructional delivery.
*   Hardware procurement (biometric scanners, servers, network infrastructure) is outside the software requirements scope.
*   Direct management of bank accounts (the system will reconcile, but not execute wire transfers directly from the bank).

### 6.3. Future Scope
*   Integration with smart school buses for GPS tracking.
*   Alumni networking and fundraising portals.
*   Predictive analytics for student dropout risks.

## 7. Stakeholder Analysis

| Stakeholder | Responsibilities | Pain Points | Business Goals | Interactions |
| :--- | :--- | :--- | :--- | :--- |
| **Board of Management (BOM)** | Strategic oversight, financial approval, governance. | Lack of real-time visibility into school finances and operations. | Ensure financial sustainability and regulatory compliance. | Principal, Finance Office, Auditors. |
| **Principal** | Overall institutional leadership, accountability to MOE. | Overwhelmed by administrative sign-offs and fragmented data. | Centralized control, real-time reporting, improved school ranking. | All departments, BOM, MOE. |
| **Finance Office / Bursar** | Budgeting, fee collection, payroll, financial reporting. | Manual bank reconciliations, handling physical cash, debt tracking. | Accurate, real-time ledgers, seamless M-Pesa/Bank integration. | Parents, Students, Principal, Stores, Procurement. |
| **Director of Studies / Academic Master** | Curriculum implementation, timetable management, exams. | Merging 8-4-4 marks and CBC competency tracking; timetable clashes. | Streamlined academic reporting, optimized resource allocation. | Teachers, Principal, KNEC. |
| **Teachers** | Lesson delivery, student assessment, discipline tracking. | Time-consuming manual roll calls and report card generation. | Maximize teaching time, easy entry of assessments. | Students, Academic Master, Parents. |
| **Gate Officers / Security** | Managing entry/exit, visitor logging. | Congestion during opening/closing days; manual logbooks. | Fast, verifiable processing of student movement; secure visitor logs. | Students, Visitors, Boarding Master. |
| **Boarding Master/Mistress** | Dormitory allocation, student welfare out of hours. | Tracking who is present, on leave, or in the hospital. | Real-time visibility of student whereabouts; streamlined bed allocation. | Students, Security, Nurse, Parents. |
| **Stores / Procurement** | Managing inventory, LPOs, supplier relations. | Stock shrinkage, manual requisition processes. | Automated reorder levels, transparent procurement trails. | Finance, Kitchen, Suppliers. |
| **Parents/Guardians** | Paying fees, supporting student academic progression. | Surprised by fee balances; unaware of disciplinary issues. | Transparency in billing, real-time academic/discipline updates. | Finance, Teachers, Administration. |
| **Ministry of Education (MOE) / County Office** | Policy enforcement, capitation disbursement. | Inaccurate school enrollment data (NEMIS issues). | Accurate data for capitation and policy planning. | Principal. |

## 8. Business Processes
*(Note: A subset of critical processes is detailed below to illustrate the depth required.)*

### 8.1. Gate Management & Student Reporting
*   **Purpose:** To securely and efficiently manage the entry and exit of students, eliminating gate congestion.
*   **Trigger:** A student arrives at the gate at the start of a term or leaves for mid-term/medical leave.
*   **Inputs:** Student identification (e.g., Smart ID), authorized leave chits.
*   **Activities:** Verify student identity -> Check fee clearance status -> Check disciplinary status -> Log entry/exit timestamp -> Notify parent via SMS -> Update boarding register.
*   **Business Rules:** No student may exit without an approved digital leave pass. Entry during reporting days requires a minimum fee threshold to be met, unless waived by the Principal.
*   **Outputs:** Digital gate log, SMS notification, updated attendance dashboard.
*   **Success Criteria:** Gate processing time reduced to <10 seconds per student.

### 8.2. Fee Collection and Reconciliation
*   **Purpose:** To capture, allocate, and reconcile all incoming school fees.
*   **Trigger:** Parent makes a payment via M-Pesa or Bank Deposit.
*   **Inputs:** Payment reference, amount, student ID.
*   **Activities:** Receive payment data -> Validate against student account -> Allocate to specific fee votes (e.g., Tuition, Boarding) based on priority rules -> Generate digital receipt -> Update general ledger -> Notify parent.
*   **Business Rules:** Payments must first clear arrears before applying to current balances. Capitation funds must be strictly allocated to MOE-approved vote heads.
*   **Outputs:** Receipt, updated statement, updated trial balance.
*   **Success Criteria:** Zero manual data entry for digital payments; real-time bank reconciliation.

### 8.3. Academic Assessment (CBC & 8-4-4)
*   **Purpose:** To record and analyze student academic performance.
*   **Trigger:** End of assessment period.
*   **Inputs:** Raw marks (8-4-4) or competency rubrics (CBC).
*   **Activities:** Teacher inputs data -> System calculates aggregates/grades or aggregates competency levels -> Class teacher reviews -> Principal approves -> Publish to parent portal.
*   **Business Rules:** CBC assessments must use the standardized 1-4 scale (Exceeding, Meeting, Approaching, Below). 8-4-4 uses the standard 12-point grading system.
*   **Outputs:** Report cards, KNEC upload files, academic performance analytics.
*   **Success Criteria:** Report cards generated within 24 hours of final data entry.

## 9. Business Capability Model
The platform must support the following capability domains:
1.  **Academic Management:** Assessment, Timetabling, Curriculum Tracking (CBC/8-4-4), Attendance.
2.  **Student Lifecycle:** Admissions, Transfers, Clearances, Alumni tracking, Disciplinary records.
3.  **Finance & Accounting:** Billing, Fee Collection, General Ledger, Accounts Payable/Receivable, Budgeting, Capitation tracking.
4.  **Human Resource:** Staff records, Payroll processing, Leave management, TSC appraisal tracking.
5.  **Administration & Operations:** Boarding management, Transport, Communications (SMS/Email), Calendar events.
6.  **Supply Chain & Assets:** Procurement, Inventory/Stores management, Fixed asset depreciation.
7.  **Security & Gate Management:** Access control, Visitor management, Leave pass issuance.
8.  **Governance & Compliance:** MOE/NEMIS reporting, Audit trails, Role-based controls.

## 10. Department Analysis
### 10.1. Finance Department
*   **Responsibilities:** Ensuring financial health, collecting fees, paying suppliers, managing payroll, producing statutory accounts.
*   **Objectives:** Eliminate cash leakages, automate reconciliations, provide accurate financial statements.
*   **Current Challenges:** Manual reconciliation of bank statements takes weeks; M-Pesa payments are hard to trace to specific students without manual intervention.
*   **Business Needs:** A fully integrated double-entry accounting system, automated M-Pesa/Bank integrations, strict budgetary controls.
*   **Dependencies:** Admissions (for billing new students), Procurement (for accounts payable), MOE (for capitation funds).

### 10.2. Boarding Department
*   **Responsibilities:** Overseeing student accommodation, tracking boarding attendance, managing dorm inventory.
*   **Objectives:** Maximize bed utilization, ensure student safety out of class hours.
*   **Current Challenges:** Knowing exactly who is in the dorm vs. who went home sick or is in class.
*   **Business Needs:** Digital bed allocation, real-time integration with Gate and Clinic data.

## 11. Business Rules
*   **Admission Policies:** A student must possess a valid Unique Personal Identifier (UPI) to be fully registered.
*   **Fee Policies:** Students with fee balances exceeding 20% of the term's fees are flagged for administrative review before term reporting.
*   **Procurement Policies:** Any purchase requisition exceeding KES 50,000 requires tertiary approval (Principal & BOM Finance Chair).
*   **Suspension Workflow:** Only the Principal or Deputy Principal can authorize a formal suspension; the system must automatically block gate exit until the suspension protocol is completed.
*   **Inventory Controls:** Kitchen stores cannot be issued without an approved daily requisition matched to the student population present.

## 12. Regulatory and Compliance Requirements
*   **Ministry of Education (MOE):** The system must generate data formats compatible with the transition from NEMIS to KEMIS, ensuring accurate reporting of enrollment to receive capitation.
*   **Kenya National Examinations Council (KNEC):** The system must support the export of candidate registration details and continuous assessment scores in KNEC-mandated formats.
*   **Teachers Service Commission (TSC):** Must support tracking of teacher attendance and provide data outputs to assist in Teacher Performance Appraisal and Development (TPAD) processes.
*   **Kenya Data Protection Act, 2019:** Student data, medical records, and financial information must be stored securely, with clear data ownership residing with the school, and explicit consent workflows for parents.
*   **Public Finance Management (PFM) Act:** For public schools, financial modules must support PFM reporting standards, including strict adherence to government-mandated chart of accounts and vote heads.
*   **Kenya Revenue Authority (KRA):** Payroll capability must automatically compute and generate reports for PAYE, NSSF, NHIF, and Housing Levy.

## 13. Finance Requirements (Enterprise Accounting)
The system must transcend basic fee collection and act as a comprehensive accounting ERP.
*   **General Ledger & Chart of Accounts:** Support a fully customizable chart of accounts aligned with MOE guidelines.
*   **Billing & Receipts:** Automated generation of termly fee structures, handling of bursaries (e.g., CDF, Ministry scholarships), and digital receipting.
*   **Banking & Reconciliations:** Multi-bank support, direct API integration with M-Pesa Paybill/Till numbers, and automated bank reconciliation matching.
*   **Accounts Payable/Receivable:** End-to-end procurement (Requisition -> LPO -> Goods Received Note -> Invoice -> Payment), and robust debtor aging reports.
*   **Financial Reporting:** Automated generation of Trial Balance, Balance Sheet, Income Statement, Cash Flow statements, and Budget vs. Actual monitoring reports.
*   **Audit & Controls:** Immutable audit trails for every journal entry, strict separation of duties (maker-checker workflows), and secure financial year-end closing procedures.

## 14. Security Business Requirements
*   **Role-Based Access Control (RBAC):** Access to modules and data must be strictly governed by the user's role (e.g., a Teacher cannot view the General Ledger; a Gate Officer cannot view academic grades).
*   **Segregation of Duties:** Financial transactions must require a maker (e.g., Accounts Clerk) and a checker (e.g., Bursar/Principal).
*   **Auditability:** Every action (data entry, deletion, modification) must be logged with a timestamp and user ID.
*   **Data Privacy:** Sensitive records (e.g., Guidance & Counselling notes, Medical records) require elevated, restricted access.
*   **Business Continuity:** The system must guarantee high availability and automated off-site backups to prevent data loss in the event of local hardware failure.

## 15. Reporting Requirements
*   **Operational Reports:** Daily gate logs, daily absentee lists, low stock alerts (Frequency: Daily; User: Operations staff).
*   **Management Reports:** Fee collection vs. arrears, budget consumption, aggregate academic performance (Frequency: Weekly/Termly; User: Principal, HODs).
*   **Executive Dashboards:** Real-time visual dashboards showing overall school health (Financial liquidity, total population, critical incidents) (Frequency: Real-time; User: Principal, BOM).
*   **Regulatory Reports:** Enrollment data for capitation, statutory deduction reports (PAYE/NSSF) (Frequency: Monthly/Termly; User: MOE, KRA).

## 16. Success Metrics (KPIs)
*   **Gate Congestion:** 90% reduction in queue time during opening/closing days.
*   **Financial Health:** 100% reduction in untraceable direct bank deposits within 6 months of rollout.
*   **Administrative Load:** 50% reduction in time spent by class teachers compiling end-of-term reports.
*   **Compliance:** Zero delays in submitting accurate NEMIS/KEMIS data.
*   **Communication:** 100% of fee invoices and receipts delivered electronically to parents.

## 17. Risks, Assumptions, Constraints, and Dependencies
### 17.1. Risks
*   **Technology Adoption:** Resistance from older staff members accustomed to paper-based systems.
*   **Infrastructure:** Unreliable internet connectivity and power outages in remote school locations.
*   **Data Integrity:** Garbage-in, garbage-out during the initial data migration phase.

### 17.2. Assumptions
*   Schools possess basic ICT infrastructure (computers, internet connection) to access a cloud-based system.
*   Parents have access to basic mobile phones to receive SMS notifications and M-Pesa prompts.

### 17.3. Constraints
*   The solution must adhere strictly to the budget limitations typical of Kenyan public schools.
*   The system must run smoothly on low-bandwidth connections.

### 17.4. Dependencies
*   Integration with Safaricom's Daraja API for M-Pesa services.
*   Cooperation from the Ministry of Education for potential future KEMIS API integrations.

## 18. Traceability Matrix
*(Placeholder for linking Business Requirements to Future Functional Requirements)*
| Business Requirement ID | Business Requirement Description | Target Functional Requirement ID |
| :--- | :--- | :--- |
| BR-001 | Digitize gate entry/exit verification | *To be defined in FRD* |
| BR-002 | Automate M-Pesa fee reconciliation | *To be defined in FRD* |
| BR-003 | Generate CBC compliance report cards | *To be defined in FRD* |
| BR-004 | Maintain double-entry general ledger | *To be defined in FRD* |
| BR-005 | Enforce maker-checker for LPOs | *To be defined in FRD* |

## 19. Glossary
*   **BOM:** Board of Management
*   **CBC:** Competency-Based Curriculum
*   **KEMIS:** Kenya Education Management Information System
*   **KNEC:** Kenya National Examinations Council
*   **LPO:** Local Purchase Order
*   **NEMIS:** National Education Management Information System
*   **TSC:** Teachers Service Commission
*   **UPI:** Unique Personal Identifier
