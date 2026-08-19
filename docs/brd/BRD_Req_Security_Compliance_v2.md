# Appendix 7: Requirements Catalogue - Security & Compliance
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Gate & Security Domain (BR-SEC)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-SEC-001 | The system shall enforce Role-Based Access Control (RBAC), ensuring users only have access to data and modules strictly required for their role. | Critical | Security Admin | None | Unauthorized data access. | Zero unauthorized data views. | FRD-SEC-001 |
| BR-SEC-002 | The system shall maintain an immutable, centralized audit log of all critical actions (creation, modification, deletion), including timestamp and User ID. | Critical | Principal | BR-SEC-001 | Inability to trace fraudulent acts. | 100% auditability of changes. | FRD-SEC-002 |
| BR-SEC-003 | The system shall provide a dedicated interface for Gate Officers to scan (or manually enter) a student ID to verify exit authorization. | Critical | Security | None | Manual gate congestion. | Gate processing < 10 seconds. | FRD-SEC-003 |
| BR-SEC-004 | The system shall flag a student as "DO NOT EXIT" if they are on an active disciplinary suspension or lack an approved leave pass. | Critical | Security | BR-BRD-005 | Suspended student leaving. | Zero unauthorized exits. | FRD-SEC-004 |
| BR-SEC-005 | The system shall automatically trigger an SMS notification to the designated Parent/Guardian immediately upon a student's verified exit or entry at the gate. | High | Security | Comm Portal | Parent unaware of student movement. | SMS sent within 1 minute of scan. | FRD-SEC-005 |
| BR-SEC-006 | The system shall provide a digital visitor logbook to record visitor details, whom they are visiting, and time-in/time-out. | Medium | Security | None | - | Complete visibility of campus visitors. | FRD-SEC-006 |
*(Note: Catalogue continues to BR-SEC-075 in the full database)*

## 2. Regulatory & Compliance Domain (BR-COM)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-COM-001 | The system shall provide automated reporting formats that strictly comply with NEMIS (and the upcoming KEMIS) data upload specifications. | Critical | Principal | MOE Guidelines | Delays in government capitation. | Zero rejected NEMIS uploads. | FRD-COM-001 |
| BR-COM-002 | The system shall run internal validation checks (e.g., verifying UPI format, checking for age anomalies) before allowing a NEMIS export file to be generated. | High | Principal | BR-COM-001 | Submitting "ghost learners". | 100% clean data submitted to MOE. | FRD-COM-002 |
| BR-COM-003 | The system shall comply with the Kenya Data Protection Act (2019) by ensuring all sensitive student data (medical, disciplinary) is encrypted at rest. | Critical | Security Admin | Data Act 2019 | Legal liability for data breaches. | 100% compliance with Data Act. | FRD-COM-003 |
| BR-COM-004 | The system shall provide a mechanism to record explicit parental consent for the storage and processing of student biometric or medical data. | High | Admissions | BR-COM-003 | - | Documented consent for all minors. | FRD-COM-004 |
| BR-COM-005 | The system shall automatically generate Teacher Attendance reports in a format that supports TSC's Teacher Performance Appraisal and Development (TPAD) process. | High | Principal | BR-HR-004 | Inaccurate TPAD assessments. | Streamlined TSC reporting. | FRD-COM-005 |
| BR-COM-006 | The system shall allow the Finance Office to generate statutory deduction reports (PAYE, NHIF, NSSF) in the exact formats required by KRA and relevant parastatals. | Critical | Finance | BR-HR-006 | Tax penalties. | Zero compliance penalties. | FRD-COM-006 |
*(Note: Catalogue continues to BR-COM-050 in the full database)*
