# Kenya Secondary School ERP Platform

> Enterprise Resource Planning system purpose-built for Kenyan secondary schools — National, Extra County, County, Sub-County, Boarding, Day, Mixed, Boys, Girls, Public, and Private.

---

## Project Origin

This project originated from an innovation proposed by a student at **Nambale Secondary School**. The initial challenge identified was congestion at school gates caused by manual verification during student reporting and dismissal. That single observation grew into a complete institutional ERP.

---

## Repository Structure

```
/
├── docs/
│   ├── brd/                        # Business Requirements Document (V2.0)
│   └── backend-artifacts/          # Backend technical specifications
│
├── backend/                        # FastAPI application (to be scaffolded)
└── README.md
```

---

## Documentation

### Business Requirements Document (BRD)
The authoritative business document from which all functional requirements, system design, and implementation plans are derived.

| Document | Description |
|:---------|:------------|
| `BRD_Master_v2.md` | Master document — Executive Summary, Vision, Governance, Personas, Glossary |
| `BRD_Stakeholders_Departments_v2.md` | Stakeholder analysis, department needs, integration matrices |
| `BRD_Processes_Capabilities_v2.md` | Level-3 capability maps, detailed business process workflows |
| `BRD_Rules_Events_Entities_v2.md` | Business rules catalogue, events catalogue, conceptual entities |
| `BRD_Req_Academics_Admissions_v2.md` | Requirements: BR-ADM, BR-ACA, BR-EXM domains |
| `BRD_Req_Finance_Procurement_v2.md` | Requirements: BR-FIN, BR-REC, BR-PRO domains |
| `BRD_Req_HR_Admin_Ops_v2.md` | Requirements: BR-HR, BR-BRD, BR-INV, BR-TRN domains |
| `BRD_Req_Security_Compliance_v2.md` | Requirements: BR-SEC, BR-COM domains |

### Backend Technical Specifications

| Document | Description |
|:---------|:------------|
| `TECH_STACK.md` | Technology decisions, full dependency manifest, project structure |
| `ARCHITECTURE.md` | DDD architecture, base classes, async DB engine, event patterns |
| `DATABASE_SCHEMA.md` | Complete PostgreSQL DDL — 20 domains, triggers, indexes, views |
| `FINANCE_BACKEND_GUIDE.md` | General Ledger, COA, Journal Engine, Period Close, Financial Reports |
| `FEE_BILLING_GUIDE.md` | Fee structures, billing runs, receipts, bursaries, clearance API |
| `MPESA_INTEGRATION_GUIDE.md` | Daraja API — STK Push, C2B webhooks, bank reconciliation |
| `PROCUREMENT_AP_GUIDE.md` | Requisitions → LPO → GRN → 3-Way Match → AP Payment |
| `PAYROLL_HR_GUIDE.md` | Kenya 2024 tax bands, PAYE/NSSF/SHA/Housing Levy, KRA P10 |
| `REPORTING_GUIDE.md` | Financial statements, report cards (CBC+8-4-4), NEMIS export |
| `SECURITY_GUIDE.md` | JWT, RBAC (25+ permissions), KDPA compliance, audit trail |
| `OPENAPI_SPEC.yaml` | Complete OpenAPI 3.1.0 spec — 37 Finance & Accounting endpoint groups |
| `DEVOPS_GUIDE.md` | Docker, Alembic, GitHub Actions CI/CD, Nginx, Celery beat |

---

## Technology Stack

| Layer | Technology |
|:------|:-----------|
| API Framework | FastAPI + Uvicorn/Gunicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| Task Queue | Celery + Redis |
| Payment | Safaricom Daraja API (M-Pesa) |
| Auth | JWT (python-jose) + bcrypt |
| PDF | ReportLab |
| Testing | pytest + testcontainers |

---

## Kenyan Compliance

- **CBC & 8-4-4** curriculum dual support
- **NEMIS/KEMIS** enrollment export
- **KNEC** candidate registration data export
- **TSC TPAD** teacher attendance support
- **KRA PAYE/NSSF/SHA/Housing Levy** payroll compliance
- **Kenya Data Protection Act 2019** — encrypted sensitive fields
- **Public Finance Management Act** — vote head controls

---

## License

Proprietary — All rights reserved.
