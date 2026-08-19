# Business Requirements Document (BRD) - Version 2.0
**Project Name:** Kenya Secondary School Enterprise Resource Planning (ERP) Platform
**Document Version:** 2.0 (Enterprise Architecture Upgrade)
**Date:** August 2026

---

## 1. Executive Summary
The Kenya Secondary School Enterprise Resource Planning (ERP) Platform is a strategic, enterprise-grade initiative designed to digitally transform the operations of secondary schools across Kenya. Expanding far beyond basic fee collection or student registries, this platform is architected at the scale of tier-1 global ERPs (e.g., Oracle ERP, SAP S/4HANA, Workday). It serves as the authoritative central operating system for a diverse range of institutions—from National to Sub-County, boarding to day, and public to private. 

By systematically eliminating paper-based processes and disparate systems, the platform establishes an integrated ecosystem supporting comprehensive financial management (full enterprise accounting), complex academic administration (bridging the 8-4-4 system and the Competency-Based Curriculum [CBC]), stringent regulatory compliance (NEMIS/KEMIS), and holistic institutional operations. 

> [!IMPORTANT]
> **Enterprise Document Architecture**
> Due to the massive scale of this implementation (targeting 500-1,000 specific business requirements), this BRD acts as the **Master Document**. Detailed domains, processes, catalogues, and matrices are documented in specialized, linked appendices below to ensure navigability and maintainability.

---

## 2. Document Navigation & Appendices
To navigate the comprehensive scope of this ERP, please refer to the following specialized appendices:

1. **[Stakeholders, Departments & Integrations](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Stakeholders_Departments_v2.md)**
   *   Comprehensive stakeholder analysis, department-by-department needs, and cross-department integration matrices.
2. **[Processes & Capabilities Model](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Processes_Capabilities_v2.md)**
   *   Level-3 Business Capability maps and detailed, step-by-step Business Process Analysis for all school operations.
3. **[Business Rules, Events & Entities](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Rules_Events_Entities_v2.md)**
   *   Business Rules catalogue, Business Events catalogue, and Conceptual Business Information Entities.
4. **[Requirements Catalogue: Academics & Admissions](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Req_Academics_Admissions_v2.md)**
   *   BR-ADM, BR-ACA, BR-EXM domains.
5. **[Requirements Catalogue: Finance & Procurement](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Req_Finance_Procurement_v2.md)**
   *   BR-FIN, BR-PRO, BR-AST domains.
6. **[Requirements Catalogue: HR, Admin & Operations](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Req_HR_Admin_Ops_v2.md)**
   *   BR-HR, BR-BRD, BR-TRN, BR-LIB, BR-INV domains.
7. **[Requirements Catalogue: Security & Compliance](file:///C:/Users/le/.gemini/antigravity/brain/f205628e-78a3-49f8-b96d-82a8a2242599/BRD_Req_Security_Compliance_v2.md)**
   *   BR-SEC, BR-COM, BR-GOV domains.

---

## 3. Business Background & Problem Statement
The project originated from a grassroots innovation at Nambale Secondary School aimed at digitizing student entry and exit to alleviate severe gate congestion. This pinpointed symptom exposed a broader, systemic reality: Kenyan schools operate using highly fragmented, paper-heavy systems that cause extensive delays, pervasive data inaccuracies, and significant operational inefficiencies across every department.

**Key Enterprise Problems:**
*   **Operational Inefficiencies:** Manual gate verification, paper-based attendance, and physical leave requests lead to massive time wastage.
*   **Financial Leakage and Inaccuracy:** Disconnected fee collection systems and manual reconciliation result in poor debt management, financial leakage, and delayed reporting. The absence of a true double-entry ledger prevents accurate auditability.
*   **Regulatory Burden:** Managing the dual requirements of the outgoing 8-4-4 curriculum and the incoming CBC, alongside manual data entry into government portals (NEMIS/KEMIS), creates immense strain on school administrators and leads to costly data discrepancies (e.g., "ghost learners").
*   **Information Silos:** Departments (Finance, Academics, Boarding, Stores) operate in total isolation, making it impossible for the Principal and Board of Management to achieve a real-time, holistic view of the institution.

## 4. Vision
To provide Kenyan secondary schools with a unified, intelligent, and secure central operating system that seamlessly connects every department, empowers educators, ensures strict financial governance comparable to corporate enterprise standards, and guarantees regulatory compliance, ultimately fostering an environment focused on educational excellence rather than administrative overhead.

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
*   **End-to-End Student Lifecycle:** Prospect, Admission, Registration, Progression, Graduation, Alumni.
*   **Academic Management:** Comprehensive tracking for CBC and 8-4-4 curricula, timetabling, examinations, and reporting.
*   **Enterprise Financial Management:** General Ledger, Accounts Payable, Accounts Receivable, Cash Management, Treasury, Assets, Budgeting, and statutory reporting.
*   **Human Capital Management:** Staff records, Payroll processing, Leave management, Performance appraisal tracking (TSC alignment).
*   **Supply Chain Management:** End-to-end Procurement, Inventory/Stores management, Supplier management.
*   **Campus Operations:** Boarding allocation, Transport management, Library services, Health/Clinic management.
*   **Security & Access:** Gate management, Visitor management, Leave pass issuance.
*   **Governance & Compliance:** Automated MOE/NEMIS reporting, KRA reporting, robust audit trails.

### 6.2. Out of Scope
*   Provision of e-learning content or Learning Management System (LMS) instructional delivery (e.g., course videos, interactive quizzes).
*   Hardware procurement and physical network installation.
*   Direct execution of wire transfers from bank interfaces (the system will generate payment files and reconcile statements, but will not directly move funds via API without bank-side authorization).

### 6.3. Future Scope
*   Integration with smart school buses for live GPS tracking.
*   Alumni fundraising portals and endowment management.
*   Predictive AI analytics for student dropout risks and academic intervention.

---

## 7. Organizational Structure & Governance Model

### 7.1. Governance Model
The ERP is governed by strict, hierarchical decision authorities reflecting Kenyan public and private school governance structures.
*   **Strategic Tier:** Board of Management (BOM) / Board of Directors. Responsible for budget approval, major capital expenditure sign-offs, and strategic policy.
*   **Executive Tier:** Principal / School Director. Final authority on all school operations, suspension/expulsion approvals, and NEMIS data certification.
*   **Operational Management Tier:** Deputy Principals (Administration & Academics), Bursar/Finance Officer. Responsible for day-to-day workflow approvals (e.g., procurement requisitions, leave approvals, timetable publication).
*   **Execution Tier:** Heads of Departments (HODs), Class Teachers, Storekeepers. Responsible for primary data entry and initial reviews.

### 7.2. Delegation of Authority (DOA) & Approval Hierarchies
*   **Financial DOA:** 
    *   Tier 1 (Up to KES 10,000): Approved by Bursar.
    *   Tier 2 (KES 10,001 - KES 50,000): Approved by Principal.
    *   Tier 3 (KES 50,001+): Requires BOM Finance Committee approval.
*   **Academic DOA:**
    *   Grade Changes: Initiated by Subject Teacher -> Approved by HOD -> Certified by Deputy Principal (Academics).
*   **Disciplinary DOA:**
    *   Minor Infractions: Handled by Class Teacher/Duty Teacher.
    *   Major Infractions (Suspension): Initiated by Deputy Principal -> Approved by Principal.

---

## 8. Business Personas
Understanding the primary users is critical to ensuring the requirements meet real-world needs.

*   **Persona 1: "The Overwhelmed Principal" (Mr. Omondi)**
    *   *Needs:* Real-time visibility into enrollment, fee collection, and critical disciplinary issues without digging through paper files. Wants peace of mind regarding NEMIS compliance.
*   **Persona 2: "The Stressed Bursar" (Ms. Wanjiku)**
    *   *Needs:* Elimination of manual bank reconciliations. Needs the system to automatically flag M-Pesa payments to the correct student account and generate accurate trial balances for the BOM.
*   **Persona 3: "The CBC Pioneer Teacher" (Mrs. Kemboi)**
    *   *Needs:* A fast, intuitive way to enter qualitative competency rubrics (1-4 scale) without spending hours manually collating data for report cards.
*   **Persona 4: "The Vigilant Gate Officer" (Mr. Juma)**
    *   *Needs:* Instant verification if a student has permission to leave the compound, and immediate processing on opening days to prevent massive queues at the gate.
*   **Persona 5: "The Anxious Parent" (Baba Kevin)**
    *   *Needs:* Transparent, real-time updates on fee balances (via SMS) and immediate alerts if Kevin does not report to class or is involved in a disciplinary issue.

---

## 9. Comprehensive Business Glossary
| Term / Acronym | Definition |
| :--- | :--- |
| **8-4-4** | The legacy Kenyan education system (8 years primary, 4 years secondary, 4 years university). |
| **BOM** | Board of Management; the governing body of a Kenyan public secondary school. |
| **CBC** | Competency-Based Curriculum; the new Kenyan education system emphasizing skills over rote memorization. |
| **Capitation** | Government funds disbursed per student enrolled in a public school. |
| **KEMIS** | Kenya Education Management Information System; the successor to NEMIS. |
| **KNEC** | Kenya National Examinations Council; the body responsible for national exams. |
| **LPO** | Local Purchase Order; a commercial document issued by a buyer to a seller. |
| **Maker-Checker** | A control mechanism requiring one individual to create a transaction and another to approve it. |
| **NEMIS** | National Education Management Information System. |
| **TPAD** | Teacher Performance Appraisal and Development; a TSC requirement. |
| **TSC** | Teachers Service Commission; the employer of teachers in Kenyan public schools. |
| **UPI** | Unique Personal Identifier; the national student ID number assigned via NEMIS. |
| **Vote Head** | A specific budget line item or category for allocating school funds (e.g., Tuition, Boarding, RMI). |

---

*This concludes the Master Document. Please proceed to the linked Appendices for detailed enterprise requirements, capability models, and matrices.*
