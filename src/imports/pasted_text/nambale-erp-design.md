Design the frontend UI for "Nambale ERP" — an enterprise resource planning web application 
for Kenyan secondary schools. It replaces paper-based processes across admissions, academics, 
finance, procurement, HR, boarding, transport, gate security, and regulatory compliance. 
The system serves multiple institutions (public and private, boarding and day, National to 
Sub-County level) and must feel authoritative, calm, and trustworthy — this is a system of 
record for student safety and school finances, not a consumer app. Primary users are non-technical 
school staff (Principals, Bursars, Deputy Principals, HODs, Teachers, Storekeepers, Gate Officers, 
Nurses) working on shared desktop computers, plus a mobile/tablet view for Gate Officers and a 
lightweight parent-facing portal accessed on low-end Android phones.

Design for role-based views: what a user sees and can act on depends on their role and the 
Delegation of Authority (DOA) tier they hold. Every write action that changes money, grades, 
or student status must visually communicate an approval/maker-checker step — never let critical 
actions look like a single, casual click.


DESIGN SYSTEM

Visual direction: Institutional, precise, and quietly serious — closer to a national banking 
or government portal than a startup SaaS product. Avoid playful illustration, avoid gradients, 
avoid rounded "bubbly" UI. This should feel like an audited system of record.

Color palette (define as tokens, use consistently):
- Ink (primary text/dark surfaces): #16241D
- Primary (success, confirmed, positive financial values, active status): #1F6F4A (deep green)
- Ochre (warnings, pending approvals, Tier 2 flags): #B5751F
- Rust (errors, blocked actions, suspensions, negative financial values): #9C3B2E
- Bone (app background): #F3EFE4
- Surface (card/panel background): #FFFFFF
- Muted text / secondary labels: #7A8078
- Border/line: #DCD6C4
- Dark sidebar background: #16241D with off-white text #E9E6DA

Typography:
- Display/heading typeface: a serif with editorial weight (e.g. Fraunces or similar) — used only 
  for page titles, section titles, and large KPI numbers, to give the system gravitas.
- Body/UI typeface: a clean grotesk sans (e.g. IBM Plex Sans) for all body text, labels, table 
  content, and form fields.
- Monospace typeface (e.g. IBM Plex Mono) for all financial figures, IDs, admission numbers, 
  UPIs, LPO numbers, and audit-log timestamps — this creates a visual distinction between 
  "narrative" content and "record" content, which matters in an auditable system.

Layout system:
- Fixed left sidebar navigation (230px), dark ink background, grouped by section with uppercase 
  micro-labels ("Overview", "Modules", etc.), active item marked with a left accent border in ochre.
- Top bar per page: page title (serif), one-line context subtitle (muted), and a status/term 
  badge on the right (e.g. "Term 2 · Week 6").
- Content area: generous padding (24–28px), card-based panels with 1px hairline borders (no 
  heavy shadows), 2–3px border radius only (sharp, not soft/bubbly).
- Data tables: hairline row dividers, uppercase 10–11px column headers in muted color, zebra-free 
  by default but with a subtle hover state per row.
- A recurring "ledger" component: a dashed-border monospace panel used anywhere money, stock, 
  or sequential events are displayed as a running list with a bold total row at the bottom. 
  Use this same component for financial ledgers, gate activity logs, and audit trails — it 
  should read as this system's signature motif.

Status tags: small pill-shaped labels, three states minimum —
  ok/positive (green bg #E7F0EA, green text), 
  warn/pending (ochre bg #F5EAD6, ochre text), 
  bad/blocked (rust bg #F7E6E2, rust text).
Use these consistently for every domain: fee status, admission stage, disciplinary status, 
requisition approval stage, gate authorization, stock levels.

Accessibility: all interactive elements need visible keyboard focus states; color is never the 
only signal (pair every status tag with text, not just color); maintain WCAG AA contrast; 
support a minimum 375px mobile width for the Gate Officer and Parent views specifically.


INFORMATION ARCHITECTURE

Design a persistent left sidebar with these top-level sections and pages. Generate each page 
as a separate frame/screen, all sharing the same design system and component library.

SECTION: Overview
  - Principal Dashboard (role: Principal, BOM)
  - Bursar Dashboard (role: Finance Officer)

SECTION: Student Lifecycle
  - Prospect Tracker
  - New Admission
  - Student Profile (360° record view)
  - Transfers & Clearance
  - Class & Stream Assignment

SECTION: Academics
  - Timetable Builder
  - CBC Formative Assessment Entry
  - 8-4-4 Exam Mark Entry
  - HOD Mark Review & Lock
  - Report Card Preview
  - KNEC Candidate Export

SECTION: Finance
  - Fee Structure Configuration
  - Student Fee Ledger
  - M-Pesa Reconciliation / Unallocated Funds
  - General Ledger & Trial Balance
  - Period-End Closing Workflow
  - Capitation Tracking

SECTION: Procurement & Inventory
  - Purchase Requisition (create + approval queue)
  - LPO Register
  - Goods Received Note (GRN) Entry
  - Stores / Inventory Master
  - Stocktake Reconciliation

SECTION: HR & Payroll
  - Staff Directory
  - Leave Request & Approval
  - Payroll Run
  - Digital Payslip

SECTION: Boarding & Transport
  - Dormitory & Bed Allocation
  - Evening Muster Roll
  - Bus Route Assignment

SECTION: Gate & Security
  - Gate Verification Console (touch/tablet optimized)
  - Visitor Log
  - Digital Leave Pass Approval Queue

SECTION: Compliance & Reporting
  - NEMIS/KEMIS Export Center
  - KRA Statutory Reports
  - Audit Log Viewer

SECTION: External / Parent-facing
  - Parent Portal (mobile-first, separate simplified nav): fee balance, payment history, 
    academic summary, disciplinary/attendance alerts

For each page below, build exactly the fields, states, and interactions listed — these map 
directly to backend requirement IDs so the generated UI can be wired to real API endpoints 
without redesign.


DOMAIN 1 — ADMISSIONS (maps to BR-ADM-001 through BR-ADM-010)

Prospect Tracker: table of prospective students with columns Name, Guardian Contact, Applied 
For (Form/Stream), Stage (tag: Enquiry / Documents Pending / Interview / Offer Sent / 
Cleared), Date Added. Include a "+ Add Prospect" button opening a slide-over form.

New Admission form, fields:
  - Full Name (text)
  - NEMIS UPI (text, monospace, with inline validation state: neutral / checking / valid-green 
    / duplicate-blocked-red) — this field must visibly demonstrate a real-time validation 
    pattern since duplicate-UPI blocking is a Critical business rule
  - Date of Birth (date picker)
  - Gender (select)
  - Category (radio: Boarder / Day Scholar)
  - Assigned Class/Stream (select, populated from Class entity)
  - Guardian Name, Phone, Relationship (repeatable group, at least one required)
  - Document upload zone (Birth Certificate, KCPE Result Slip, Leaving Certificate) with 
    per-file upload status
  - Admission Criteria Checklist (dynamic checklist based on Boarder/Day selection)
Primary action: "Validate & Register" button. On success, show a confirmation state: 
"UPI validated. Status set to Active — Term 1 invoice will auto-generate" with a green 
callout. On duplicate, show a red callout blocking submission and explaining why (do not 
let the user silently override).

Student Profile page: a 360° record with tabs — Overview (photo, UPI, admission no., class, 
guardian contacts), Academic (grades trend, CBC ratings, attendance %), Finance (running fee 
balance, mini-ledger preview), Disciplinary (incident log), Boarding (dorm/bed if applicable), 
Documents (uploaded files). This page is the hub every other module deep-links into.

Transfers & Clearance: a stepper/workflow view — Request → Clearance Certificate Generated → 
Academic Transcript Attached → Complete. Show which party owns each step.


DOMAIN 2 — ACADEMICS & EXAMINATIONS (BR-ACA-001–012, BR-EXM-001–007)

Design explicitly for TWO parallel curriculum tracks running side by side — this dual-track 
requirement is the single most distinctive feature of this product and should be visually 
obvious, e.g. a persistent toggle or split-tab at the top of every academics screen: 
"CBC" | "8-4-4". Never merge their data models visually.

CBC Formative Assessment Entry: table of students in a class for one Learning Strand. Each 
row: Student Name, then a horizontal row of four circular rating buttons labeled 1–4 
(1=Below, 2=Approaching, 3=Meeting, 4=Exceeding — show these labels on hover/tooltip). 
Selected rating fills solid in primary green. A strand cannot be submitted while any active 
student has no rating selected — show a persistent counter "3 of 24 students rated" and 
disable the Submit button until complete, with the disabled state explaining why.

8-4-4 Exam Mark Entry: spreadsheet-style table, Student Name + numeric mark input (0–100) 
per subject column, auto-computed letter grade shown inline as marks are typed, with a 
class mean row pinned at the bottom that recalculates live.

HOD Mark Review & Lock: read-only view of submitted marks with a prominent "Lock Marks" 
action that, once clicked, visibly changes every mark cell to a locked/read-only state 
(subtle diagonal hatch or lock icon) — this must communicate the maker-checker boundary 
clearly, since after locking, subject teachers can no longer edit.

Report Card Preview: a print-style preview combining academic performance (both tracks, 
whichever applies to the student's grade), attendance %, and a disciplinary summary line — 
this pulls from three different domains into one document, make that visually clear via 
labeled sections.

KNEC Candidate Export: a simple export configuration screen — select candidates, preview a 
validation summary ("142 candidates ready, 3 flagged: missing UPI"), and a "Generate Export 
File" button. Frame this explicitly as generating a downloadable file for manual upload to 
KNEC's portal, not a live API push — the UI copy should say "Download KNEC Upload File," 
never "Submit to KNEC."

Timetable Builder: a weekly grid (days × periods), drag-and-drop subject/teacher/room blocks, 
with a conflict indicator (red outline + tooltip) on any cell where a teacher or room is 
double-booked. Include a "Regenerate Automatically" button and a manual override toggle.


DOMAIN 3 — FINANCE & BILLING (BR-FIN-001–009, BR-REC-001–008)

Use the signature ledger component throughout this section.

Student Fee Ledger: per-student ledger showing line items in chronological order — arrears 
carried forward, current term Vote Head charges (Tuition, Boarding, Activity, RMI — each its 
own line), payments received (tagged with source: M-Pesa ref / Bank / Bursary credit), and a 
bold running balance total. Payments should visually show which they were allocated against 
(arrears first, per business rule) via a small annotation.

M-Pesa Reconciliation / Unallocated Funds: two-panel view — left panel is a live-updating feed 
of incoming payments (reference number, amount, timestamp, matched student or "Unmatched"); 
right panel is a manual matching tool for the Bursar — search a student, drag or assign an 
unmatched payment to their account. Unmatched payments sit in a visually distinct amber 
"suspense" zone until resolved.

General Ledger & Trial Balance: a formal accounting table — Account Code, Account Name, Debit, 
Credit, Running Balance — with the totals row enforcing that Debits = Credits visually (show 
a green checkmark "Balanced" or red "Out of balance by KES X" state).

Period-End Closing Workflow: a confirmation-heavy, multi-step modal — this is a dangerous, 
irreversible action (locks the ledger). Require a summary review screen before the final 
"Close Period" button, and show clearly who is authorized (BOM Finance Chair override only 
after close).

Fee Structure Configuration: a matrix/table editor — rows are Vote Heads (Tuition, Boarding, 
Activity, RMI, Transport), columns are student categories (Form 1–4 × Boarder/Day) — editable 
currency cells.

Capitation Tracking: a dedicated sub-ledger view showing government capitation funds received 
per Vote Head, with a locked/restricted visual treatment communicating these funds cannot be 
reassigned to unrelated Vote Heads.


DOMAIN 4 — PROCUREMENT & INVENTORY (BR-PRO-001–007, BR-INV-001–005)

Design this entire domain as a visible pipeline/stepper: Requisition → Budget Check → 
Tier 1 Approval (Bursar) → Tier 2 Approval (Principal, if above threshold) → LPO Generated → 
Goods Received (GRN) → 3-Way Match → Payment Authorized. Every screen in this domain should 
show this stepper at the top with the current stage highlighted, so a non-technical user 
always understands where a purchase is in its lifecycle.

Purchase Requisition form: HOD, Department, Vote Head (select — triggers a live "Remaining 
Budget: KES X" readout), Items table (description, quantity, estimated unit cost, computed 
subtotal), Justification text field. If total exceeds remaining Vote Head budget, hard-block 
submission with a red inline message referencing the Vote Head and shortfall amount — do not 
allow a silent override.

Approval Queue: a task list view filtered to the current user's role/tier, each row showing 
Requisition ID, Requestor, Amount, Vote Head, and Approve/Reject buttons. Show the DOA tier 
badge on each row (Tier 1 / Tier 2 / Tier 3 — BOM).

LPO Register: table of generated LPOs with status tags (Draft / Approved / Awaiting Delivery / 
GRN Received / Paid).

GRN Entry: Storekeeper-facing form — select an existing LPO, then a checklist of ordered line 
items where the Storekeeper confirms quantity received vs. ordered per line (flag mismatches 
in rust color).

3-Way Match view: a three-column comparison — LPO line items | GRN quantities | Supplier 
Invoice amounts — with automatic green/red match indicators per row, and payment authorization 
blocked until all rows match (or an explicit exception is logged).

Stores/Inventory Master: item catalogue table with Reorder Level column and a visual low-stock 
indicator (rust tag "Reorder now") when current stock falls below threshold.

Stocktake Reconciliation: a two-column comparison, System Count vs. Physical Count, with 
variance auto-calculated and highlighted per item.


DOMAIN 5 — HR & PAYROLL (BR-HR-001–008)

Staff Directory: searchable table — Name, Role, TSC/BOM designation, Department, Contact. 
Click into a Staff Profile with tabs: Personal (KRA PIN, NHIF, NSSF, TPAD number), Contract, 
Leave Balance, Payroll History.

Leave Request & Approval: a request form (Leave Type: Annual/Sick/Compassionate/Maternity-
Paternity, Date Range, Reason) plus an approval queue showing the routing chain visually 
(Staff → Deputy Principal Administration → Principal) with current position highlighted.

Payroll Run: a review-before-commit screen — table of all staff with Gross Pay, computed 
statutory deductions (PAYE, NHIF, NSSF, Housing Levy) broken out in separate columns, Net Pay. 
A prominent "Run Payroll" button that requires a confirmation step given its financial 
significance.

Digital Payslip: a clean, printable single-staff-member document view — earnings breakdown, 
deductions breakdown, net pay, accessible from a staff self-service view.


DOMAIN 6 — BOARDING & TRANSPORT (BR-BRD-001–005, BR-TRN-001–002)

Dormitory & Bed Allocation: a visual floor-plan-style grid of beds grouped by dormitory, each 
bed cell showing occupied (student initials) or vacant, with drag-to-assign interaction and 
an overbooking prevention state (cannot drop a student onto an occupied bed).

Evening Muster Roll: a real-time dashboard — large summary counts at the top (In Dorm / On 
Leave / In Sickbay / Unaccounted) followed by a filterable student list, each row tagged with 
current status. The "Unaccounted" count should be visually the most alarming element on the 
page (rust color, largest weight) since this is a student-safety-critical view.

Bus Route Assignment: a simple list-based UI — Routes as expandable groups, each containing 
assigned Day Scholars, with a running count against vehicle capacity.


DOMAIN 7 — GATE & SECURITY (BR-SEC-001–006)

Gate Verification Console: design this specifically for a tablet/touchscreen at a physical 
gate, used standing up, in bright daylight — very large touch targets, high contrast, minimal 
text entry. Center-stage: an Admission Number input (large, numeric-friendly) and a big circular 
status indicator that fills either green ("Authorized — Exit OK") or rust red ("DO NOT EXIT") 
after a scan/lookup, with the reason shown below in large text (e.g. "Active suspension on 
file" or "No approved leave pass"). Below that, a running log of today's scans in a compact 
list. This screen should function correctly even if described to someone who has never used 
a computer.

Digital Leave Pass Approval Queue: (Deputy Principal-facing) a queue of pending leave requests 
with Requestor, Student, Reason, Requested Exit Time — Approve/Deny actions that, once approved, 
immediately make the pass valid for gate scanning.

Visitor Log: a simple form (Visitor Name, ID Number, Visiting Whom, Purpose, Time In) plus a 
table of today's visitors with a "Sign Out" action per row that captures Time Out.

Audit Log Viewer: (Principal/Security Admin-facing) a filterable, searchable table of every 
system action — Timestamp, User, Action, Entity Affected, Before/After values where applicable. 
Design this to feel immutable and official — monospace timestamps, no edit affordances of any 
kind, read-only throughout.


DOMAIN 8 — COMPLIANCE & REPORTING (BR-COM-001–006)

NEMIS/KEMIS Export Center: a validation-first workflow — "Run Validation Check" button produces 
a report ("1,284 records checked · 3 flagged") with flagged records listed and explained (e.g. 
"UPI format invalid," "Age anomaly"), each linking directly to the affected Student Profile for 
correction. Only after validation passes does a "Generate NEMIS Export File" button become 
active. Label this clearly as a downloadable file, consistent with the manual-upload reality 
described in DOMAIN 2's KNEC export.

KRA Statutory Reports: similar pattern — select reporting period, generate PAYE/NHIF/NSSF 
report files in the required format, with a small preview table before download.


PARENT PORTAL (mobile-first, separate simplified navigation, 3–4 items max)

Design as a distinct, much simpler mobile app-like experience: Fee Balance (large, single 
number, with a mini payment history list below), Academic Summary (most recent report card 
summary, no editing), Notifications feed (chronological list of SMS-style alerts already sent 
— gate exit, fee receipt, disciplinary notice), and a simple Contact School action. Keep this 
entirely read-only; parents never edit data in this system.


COMPONENT LIBRARY TO BUILD AS REUSABLE, NAMED COMPONENTS

Build these as a proper Figma component library with variants, not one-off elements, so they 
can be reused consistently across all screens above:
  - StatusTag (variants: ok / warn / bad / neutral)
  - PriorityTag (variants: Critical / High / Medium / Low)
  - KPICard (label, large serif value, delta indicator)
  - LedgerPanel (list of label+amount rows, dashed border, bold total row, positive/negative 
    amount coloring)
  - DataTable (header row, zebra-free body, hover state, optional row-click)
  - ApprovalStepper (horizontal stepper showing multi-stage workflow with current-stage 
    highlight — reused across Procurement, Admissions, Leave)
  - RatingSelector (the 1–4 circular CBC rating control)
  - ValidationCallout (inline success/error message block, used for UPI checks, budget checks, 
    NEMIS validation)
  - RoleBadge (small pill showing current user's role, shown in sidebar footer)
  - GateStatusIndicator (large circular authorized/blocked indicator for the Gate Console)


DATA MAPPING & NAMING CONVENTIONS FOR BACKEND HANDOFF

Name every Figma layer, frame, and component using the same field and entity names as the 
source data model so a developer can map components to API responses without a translation 
step. Specifically:
  - Frame names should match the page names given above exactly (e.g. "Student Fee Ledger," 
    not "Finance Page 3").
  - Any field bound to a data value should be named after its entity.field, e.g. 
    "student.admissionNumber," "student.upi," "feeLedger.runningBalance," "lpo.status," 
    "requisition.voteHead," "leavePass.approvedBy," "gateLog.timestamp." Use the entity names: 
    Student, Parent/Guardian, Staff, Class/Stream, Subject/Strand, Financial Account, Fee Vote 
    Head, LPO, Asset, Leave Pass — matching the BRD's Conceptual Business Entities.
  - Every status tag instance should have a text variant whose label matches a real backend 
    enum value where one is implied by the BRD (e.g. GateStatusIndicator states are exactly 
    "Authorized" and "DO NOT EXIT"; requisition approval stages are exactly "Tier 1 Pending," 
    "Tier 2 Pending," "Approved," "Rejected").
  - Every primary action button's label should be the literal verb-first instruction a 
    developer will wire to an endpoint (e.g. "Validate & Register," "Generate NEMIS Export 
    File," "Lock Marks," "Close Period," "Run Payroll") — avoid vague labels like "Submit" or 
    "Continue" anywhere a specific business action is happening.
  - Annotate Critical-priority actions (period closing, mark locking, suspension, payroll run) 
    with a Figma comment or sticky note flagging "requires confirmation step + audit log entry" 
    so this isn't lost in developer handoff.

Generate the file with clear frame organization by the sections listed in the Information 
Architecture, using consistent 8px spacing grid throughout, and produce both a desktop 
(1440px) and mobile (375px) version of the Gate Verification Console and the Parent Portal 
specifically, since those two are explicitly designed for handheld/field use.