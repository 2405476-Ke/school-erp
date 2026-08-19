# Appendix 6: Requirements Catalogue - HR, Admin & Operations
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Human Resources Domain (BR-HR)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-HR-001 | The system shall maintain comprehensive profiles for all staff (BOM and TSC), including KRA PIN, NHIF, NSSF, and TPAD numbers. | High | HR Admin | None | Data privacy breaches. | 100% staff records digitized. | FRD-HR-001 |
| BR-HR-002 | The system shall support a digital leave management workflow allowing staff to request Annual, Sick, Compassionate, and Maternity/Paternity leave. | Medium | HR Admin | None | - | Paperless leave requests. | FRD-HR-002 |
| BR-HR-003 | The system shall automatically route staff leave requests to the Deputy Principal (Administration) and Principal for approval. | High | Principal | BR-HR-002 | Delays if approver is away. | 100% adherence to approval chain. | FRD-HR-003 |
| BR-HR-004 | The system shall integrate with biometric clock-in devices to record daily staff attendance automatically. | Low | HR Admin | Biometric Hardware | Hardware failure. | Accurate daily attendance logs. | FRD-HR-004 |
| BR-HR-005 | The system shall generate a monthly payroll processing run for BOM-employed staff. | Critical | Finance | BR-HR-001 | Payroll calculation errors. | Automated salary generation. | FRD-HR-005 |
| BR-HR-006 | The system shall automatically calculate statutory deductions (PAYE, NSSF, NHIF, Housing Levy) based on current KRA tax bands. | Critical | Finance | BR-HR-005 | Non-compliance with tax laws. | Zero KRA penalties. | FRD-HR-006 |
| BR-HR-007 | The system shall allow the definition and deduction of custom payroll items (e.g., Staff Welfare Contributions, Salary Advances). | Medium | Finance | BR-HR-005 | - | Accurate net pay calculations. | FRD-HR-007 |
| BR-HR-008 | The system shall generate digital payslips that can be emailed or securely accessed via a staff self-service portal. | High | HR Admin | BR-HR-005 | - | Zero paper payslips printed. | FRD-HR-008 |
*(Note: Catalogue continues to BR-HR-100 in the full database)*

## 2. Boarding & Operations Domain (BR-BRD)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-BRD-001 | The system shall provide a facility to define the boarding infrastructure, including Hostels, Dormitories, Cubicles, and specific Bed capacities. | High | Boarding Master | None | - | Accurate capacity modeling. | FRD-BRD-001 |
| BR-BRD-002 | The system shall support the automated or manual allocation of students to specific beds at the beginning of the academic year. | High | Boarding Master | BR-BRD-001 | Overbooking a dorm. | 100% utilization tracking. | FRD-BRD-002 |
| BR-BRD-003 | The system shall provide a real-time "Muster Roll" dashboard showing exactly which students are currently checked into the dormitory versus on authorized leave. | Critical | Boarding Master | BR-SEC-005 | Inaccurate attendance data during emergencies. | 100% accurate nightly roll call. | FRD-BRD-003 |
| BR-BRD-004 | The system shall allow the Clinic/Nurse to digitally flag a student as "Admitted to Sickbay", automatically removing them from the expected dormitory roll call. | High | Nurse | None | - | Cross-department visibility. | FRD-BRD-004 |
| BR-BRD-005 | The system shall provide a workflow to record disciplinary infractions that occur within the boarding facilities, linking them directly to the student's main profile. | Medium | Boarding Master | None | - | Centralized disciplinary history. | FRD-BRD-005 |
*(Note: Catalogue continues to BR-BRD-050 in the full database)*

## 3. Inventory & Stores Domain (BR-INV)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-INV-001 | The system shall maintain a master catalogue of all inventory items (e.g., maize, rice, textbooks, lab chemicals) categorized by department. | High | Stores | None | - | Centralized item master. | FRD-INV-001 |
| BR-INV-002 | The system shall support the definition of minimum reorder levels for critical items, triggering an automated alert to Procurement when stock falls below the threshold. | Medium | Stores | BR-INV-001 | Stockouts of essential items. | Zero emergency procurement requests. | FRD-INV-002 |
| BR-INV-003 | The system shall mandate the creation of a digital Goods Issue Note (GIN) before inventory can be deducted from the system. | High | Stores | None | Inventory shrinkage/theft. | 100% traceability of stock usage. | FRD-INV-003 |
| BR-INV-004 | The system shall require the Kitchen department to submit a digital daily requisition for food supplies, which must be approved before the Storekeeper can issue the goods. | High | Stores | None | Over-issuing of food stores. | Food consumption matches student count. | FRD-INV-004 |
| BR-INV-005 | The system shall support periodic (e.g., termly) physical stocktake adjustments, logging any discrepancies (variances) between the system count and physical count for audit review. | Critical | Finance | BR-INV-001 | Masking of stolen inventory. | Accurate term-end valuations. | FRD-INV-005 |
*(Note: Catalogue continues to BR-INV-075 in the full database)*

## 4. Transport & Fleet Domain (BR-TRN)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-TRN-001 | The system shall allow the definition of school bus routes and the assignment of specific day scholars to those routes for billing purposes. | Medium | Finance | None | Billing day scholars incorrectly. | Accurate transport fee billing. | FRD-TRN-001 |
| BR-TRN-002 | The system shall maintain a digital logbook for the school fleet, tracking mileage, fuel consumption, and maintenance schedules. | Low | Admin | None | - | Improved fleet lifespan. | FRD-TRN-002 |
*(Note: Catalogue continues to BR-TRN-020 in the full database)*
