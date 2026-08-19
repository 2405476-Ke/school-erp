# Appendix 5: Requirements Catalogue - Finance & Procurement
**Document Version:** 2.0 (Enterprise Architecture Upgrade)

---

## 1. Finance & General Ledger Domain (BR-FIN)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-FIN-001 | The system shall provide a true double-entry accounting engine where every transaction updates corresponding debit and credit accounts. | Critical | Finance | None | Core accounting failure. | 100% balanced accounting equations. | FRD-FIN-001 |
| BR-FIN-002 | The system shall support a customizable, multi-level Chart of Accounts (COA) aligned with the MOE standard accounting guidelines. | Critical | Finance | MOE Policy | COA misalignment with audits. | Clean external audit reports. | FRD-FIN-002 |
| BR-FIN-003 | The system shall allow the definition of custom Financial Years (e.g., Jan-Dec or Jul-Jun) distinct from academic terms. | High | Finance | None | Reporting period mismatch. | Accurate annual reports. | FRD-FIN-003 |
| BR-FIN-004 | The system shall provide a period-end closing workflow (Month-End and Year-End) that locks the ledger against historical postings. | Critical | Finance | BR-FIN-001 | Retrospective tampering of accounts. | Secure financial periods. | FRD-FIN-004 |
| BR-FIN-005 | The system shall carry forward retained earnings and open account balances to the new financial year during the Year-End close process. | Critical | Finance | BR-FIN-004 | Incorrect opening balances. | Seamless transition to new FY. | FRD-FIN-005 |
| BR-FIN-006 | The system shall allow the configuration of Cost Centers (e.g., Boarding, Transport, Farm) to track departmental profitability. | High | Finance | None | - | Granular profit/loss analysis. | FRD-FIN-006 |
| BR-FIN-007 | The system shall support the generation of real-time Financial Statements including the Trial Balance, Balance Sheet, and Income Statement. | Critical | Finance | BR-FIN-001 | - | Statements generated in < 1 minute. | FRD-FIN-007 |
| BR-FIN-008 | The system shall track Government Capitation funds in isolated sub-ledgers tied specifically to MOE-mandated Vote Heads. | High | Finance | MOE Policy | Capitation mismanagement flags. | Zero audit queries on Capitation. | FRD-FIN-008 |
| BR-FIN-009 | The system shall automatically calculate and post depreciation on Fixed Assets using Straight-Line or Reducing Balance methods. | Medium | Finance | BR-FIN-001 | Incorrect asset valuation. | Automated asset register. | FRD-FIN-009 |
*(Note: Catalogue continues to BR-FIN-250 in the full database)*

## 2. Student Billing & Receivables Domain (BR-REC)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-REC-001 | The system shall allow the configuration of termly Fee Structures mapped to specific student categories (e.g., Boarder vs. Day, Form 1 vs. Form 4). | Critical | Finance | BR-FIN-002 | Incorrect billing. | Accurate fee generation. | FRD-REC-001 |
| BR-REC-002 | The system shall automatically generate individual student fee invoices at the start of a term based on their active profile and category. | High | Finance | BR-REC-001 | Delay in fee collection. | 100% automated termly billing. | FRD-REC-002 |
| BR-REC-003 | The system shall provide API integration with Safaricom Daraja (M-Pesa Paybill) to receive real-time payment notifications. | Critical | Finance | Safaricom API | API downtime. | Real-time payment reflection. | FRD-REC-003 |
| BR-REC-004 | The system shall automatically match incoming M-Pesa payments to a student account if the Account Reference matches the student's Admission Number. | Critical | Finance | BR-REC-003 | - | Zero manual M-Pesa entry. | FRD-REC-004 |
| BR-REC-005 | The system shall place incoming bank/mobile payments with unrecognized reference numbers into an "Unallocated Funds" suspense account. | High | Finance | BR-REC-004 | Funds lost in transit. | 100% funds accounted for. | FRD-REC-005 |
| BR-REC-006 | The system shall provide a UI for the Bursar to manually match unallocated suspense funds to specific student accounts. | High | Finance | BR-REC-005 | - | Suspense account cleared weekly. | FRD-REC-006 |
| BR-REC-007 | The system shall automatically allocate payments first to historical arrears before applying them to current term balances. | High | Finance | None | Incorrect debt tracking. | Accurate aging reports. | FRD-REC-007 |
| BR-REC-008 | The system shall support the application of Bursaries and Scholarships (e.g., CDF) as credit notes against a student's balance. | High | Finance | None | - | Transparent bursary tracking. | FRD-REC-008 |
*(Note: Catalogue continues to BR-REC-150 in the full database)*

## 3. Procurement & Payables Domain (BR-PRO)
| Req ID | Requirement Description | Priority | Owner | Dependencies | Risks | Success Measure | Traceability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BR-PRO-001 | The system shall provide a facility for Heads of Department to create digital Purchase Requisitions. | High | HODs | None | - | 100% digital requisitions. | FRD-PRO-001 |
| BR-PRO-002 | The system shall hard-stop the creation of a Requisition if the requested amount exceeds the available budget for the selected Vote Head. | Critical | Finance | BR-FIN-006 | Budget overruns. | Zero budget overruns. | FRD-PRO-002 |
| BR-PRO-003 | The system shall enforce a Maker-Checker workflow where the Bursar approves Tier 1 requisitions and the Principal approves Tier 2 requisitions. | Critical | Principal | DOA Policy | Unauthorized spending. | 100% adherence to DOA. | FRD-PRO-003 |
| BR-PRO-004 | The system shall generate a digitally signed Local Purchase Order (LPO) upon final approval of a requisition. | High | Procurement| BR-PRO-003 | - | Standardized LPO generation. | FRD-PRO-004 |
| BR-PRO-005 | The system shall allow the Storekeeper to generate a Goods Received Note (GRN) linked directly to a specific LPO. | High | Stores | BR-PRO-004 | Paying for undelivered goods. | Inventory correctly updated. | FRD-PRO-005 |
| BR-PRO-006 | The system shall enforce 3-Way Matching, requiring an LPO, GRN, and Supplier Invoice before flagging an Account Payable for payment. | Critical | Finance | BR-PRO-005 | Fraudulent payments. | Zero payments without 3-way match. | FRD-PRO-006 |
| BR-PRO-007 | The system shall provide an Accounts Payable Aging Report to track outstanding supplier debts (30/60/90 days). | Medium | Finance | None | - | Clear visibility of supplier debt. | FRD-PRO-007 |
*(Note: Catalogue continues to BR-PRO-100 in the full database)*
