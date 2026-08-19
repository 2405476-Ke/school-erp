# Appendix 4: Requirements Catalogue - Academics & Admissions
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Admissions Domain (BR-ADM)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-ADM-001 | The system shall provide a facility to capture prospective student details prior to formal admission. | Medium | Admissions | None | Data duplication if not checked against existing records. | 100% of prospects tracked digitally. | FRD-ADM-001 |
| BR-ADM-002 | The system shall mandate the input of a valid NEMIS Unique Personal Identifier (UPI) for all public school admissions. | High | Admissions | MOE Guidelines | NEMIS portal downtime preventing validation. | Zero students enrolled without a UPI. | FRD-ADM-002 |
| BR-ADM-003 | The system shall automatically block the registration of a UPI that is already active within the school's database. | High | Admissions | BR-ADM-002 | - | Zero duplicate UPIs. | FRD-ADM-003 |
| BR-ADM-004 | The system shall support the upload and secure storage of digital copies of birth certificates and previous academic leaving certificates. | Medium | Admissions | Cloud Storage | Exceeding storage quotas. | 100% paperless admission files. | FRD-ADM-004 |
| BR-ADM-005 | The system shall automatically assign an internal Admission Number based on a customizable, sequential institutional format (e.g., YYYY/NNNN). | High | Admissions | None | Format misalignment with legacy records. | Sequential numbering maintained. | FRD-ADM-005 |
| BR-ADM-006 | The system shall provide a workflow to route admission files for Principal approval before a student is marked as "Active". | High | Principal | None | Bottleneck if Principal is unavailable. | 100% of admissions approved digitally. | FRD-ADM-006 |
| BR-ADM-007 | The system shall automatically trigger the generation of a Term 1 Fee Invoice upon the transition of a student's status to "Active". | High | Finance | BR-FIN-010 | Billing errors if class assignment is wrong. | Zero delay between admission and billing. | FRD-ADM-007 |
| BR-ADM-008 | The system shall provide a facility to process student transfers, generating a digital leaving certificate and academic transcript. | High | Deputy (Admin) | None | - | Transfers processed in < 1 hour. | FRD-ADM-008 |
| BR-ADM-009 | The system shall allow the definition of custom admission criteria checklists specific to boarding vs. day students. | Low | Admissions | None | - | Checklist completion enforced. | FRD-ADM-009 |
| BR-ADM-010 | The system shall provide an automated class assignment algorithm based on gender balance and academic entry scores. | Medium | Deputy (Acad) | None | Algorithm grouping errors. | Evenly balanced streams. | FRD-ADM-010 |
*(Note: Catalogue continues to BR-ADM-150 in the full database)*

## 2. Academics & Curriculum Domain (BR-ACA)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-ACA-001 | The system shall support the parallel configuration of the 8-4-4 curriculum and the Competency-Based Curriculum (CBC). | Critical | Deputy (Acad) | None | Complexity in reporting structures. | Both systems operate concurrently. | FRD-ACA-001 |
| BR-ACA-002 | The system shall allow the definition of CBC Learning Areas, Strands, and Sub-strands as per the Kenya Institute of Curriculum Development (KICD) guidelines. | High | Deputy (Acad) | MOE Guidelines | KICD syllabus changes. | 100% alignment with current KICD syllabus. | FRD-ACA-002 |
| BR-ACA-003 | The system shall provide a facility for teachers to input formative CBC assessments using the standard 1-4 scale (Below, Approaching, Meeting, Exceeding). | Critical | Teachers | BR-ACA-002 | Resistance from teachers used to percentages. | 100% of CBC assessments captured. | FRD-ACA-003 |
| BR-ACA-004 | The system shall aggregate formative CBC assessments across a term into a single summative competency rating per Learning Area. | High | Deputy (Acad) | BR-ACA-003 | Calculation logic errors. | Accurate termly CBC reports. | FRD-ACA-004 |
| BR-ACA-005 | The system shall support the 8-4-4 grading system, allowing the configuration of custom grade boundaries (e.g., A = 80-100, A- = 75-79). | High | Deputy (Acad) | None | - | Accurate 8-4-4 grading. | FRD-ACA-005 |
| BR-ACA-006 | The system shall provide a facility to block subject selection combinations that violate KNEC regulations for KCSE candidate registration. | High | Deputy (Acad) | KNEC Rules | Rule changes by KNEC. | Zero rejected KNEC registrations. | FRD-ACA-006 |
| BR-ACA-007 | The system shall automatically calculate subject mean scores and overall class mean scores for 8-4-4 examinations. | High | HODs | BR-ACA-005 | - | Real-time performance analytics. | FRD-ACA-007 |
| BR-ACA-008 | The system shall provide a facility to rank students within their stream and across the entire form/grade (for 8-4-4 only). | Medium | Deputy (Acad) | BR-ACA-007 | - | Accurate ranking tables. | FRD-ACA-008 |
| BR-ACA-009 | The system shall support the generation of individualized, printable Report Cards that combine academic performance, attendance, and disciplinary records. | High | Class Teachers | BR-ADM, BR-SEC | Print formatting issues. | 100% automated report generation. | FRD-ACA-009 |
| BR-ACA-010 | The system shall provide an automated timetable generation engine that resolves teacher, room, and subject combination conflicts. | High | Deputy (Acad) | None | Algorithm failing to find a solution. | Zero timetable clashes. | FRD-ACA-010 |
| BR-ACA-011 | The system shall allow the manual override of the automated timetable by authorized personnel. | Medium | Deputy (Acad) | BR-ACA-010 | Human error introducing clashes. | Flexibility in scheduling. | FRD-ACA-011 |
| BR-ACA-012 | The system shall track syllabus coverage by allowing teachers to check off completed topics against the KICD master syllabus. | Low | HODs | BR-ACA-002 | Low teacher compliance. | Real-time syllabus tracking. | FRD-ACA-012 |
*(Note: Catalogue continues to BR-ACA-200 in the full database)*

## 3. Examinations Domain (BR-EXM)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-EXM-001 | The system shall allow the scheduling of internal examinations (Opener, Mid-Term, End-of-Term). | High | Deputy (Acad) | BR-ACA-010 | - | All exams scheduled digitally. | FRD-EXM-001 |
| BR-EXM-002 | The system shall provide a secure, role-based portal for teachers to input raw exam marks. | Critical | Teachers | BR-SEC-001 | Unauthorized grade changes. | 100% secure mark entry. | FRD-EXM-002 |
| BR-EXM-003 | The system shall maintain an immutable audit trail of all mark entries and modifications, logging the User ID and timestamp. | Critical | Principal | BR-EXM-002 | - | Full auditability of grade changes. | FRD-EXM-003 |
| BR-EXM-004 | The system shall provide a workflow for HODs to review and lock exam marks, preventing further changes by subject teachers. | High | HODs | BR-EXM-002 | - | Enforced maker-checker on grades. | FRD-EXM-004 |
| BR-EXM-005 | The system shall generate a data export file formatted specifically for uploading candidate registration details to the KNEC portal. | Critical | Deputy (Acad) | KNEC Specs | KNEC changing the file format. | Zero manual data entry into KNEC. | FRD-EXM-005 |
| BR-EXM-006 | The system shall provide a facility to record and track continuous assessment tests (CATs) separately from main examinations. | Medium | Teachers | None | - | Granular performance tracking. | FRD-EXM-006 |
| BR-EXM-007 | The system shall automatically calculate the final term grade based on customizable weightings (e.g., CAT 1: 15%, CAT 2: 15%, Main Exam: 70%). | High | Deputy (Acad) | BR-EXM-006 | Weighting misconfiguration. | Accurate final term grades. | FRD-EXM-007 |
*(Note: Catalogue continues to BR-EXM-100 in the full database)*
