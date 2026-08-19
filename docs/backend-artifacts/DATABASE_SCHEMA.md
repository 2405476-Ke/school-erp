# Kenya Secondary School ERP - Complete Database Schema

This artifact contains the comprehensive PostgreSQL database schema for the Kenya Secondary School ERP. It covers all 20 modules and applies Domain-Driven Design principles, multi-tenancy, Kenyan specific business context (M-Pesa, TSC, CBC, 8-4-4, KRA, Statutory deductions), and rigorous data integrity constraints.

## 1. CORE / TENANCY

```sql
-- Enables UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    motto TEXT,
    nemis_code VARCHAR(50) UNIQUE, -- National Education Management Information System code
    registration_number VARCHAR(100) UNIQUE,
    kra_pin VARCHAR(20) UNIQUE,
    phone_number VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    logo_url TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
COMMENT ON TABLE schools IS 'Multi-tenant root table. A single ERP deployment can serve multiple schools.';

CREATE TABLE academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    year_name VARCHAR(20) NOT NULL, -- e.g., '2025'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, year_name)
);

CREATE TABLE terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    term_name VARCHAR(50) NOT NULL CHECK (term_name IN ('TERM_1', 'TERM_2', 'TERM_3')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (academic_year_id, term_name)
);

CREATE TABLE school_calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE SET NULL,
    event_title VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) CHECK (event_type IN ('HOLIDAY', 'EXAM', 'SPORTS', 'MEETING', 'OTHER')),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE system_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID, -- References users(id), not enforced by FK to prevent blocking user deletion
    table_name VARCHAR(100) NOT NULL,
    row_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 2. USER MANAGEMENT & RBAC

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('SUPERADMIN', 'ADMIN', 'STAFF', 'TEACHER', 'PARENT', 'STUDENT')),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, username)
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, name)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'finance:view', 'students:edit'
    module VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL UNIQUE,
    ip_address VARCHAR(50),
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 3. ADMISSIONS & STUDENT LIFECYCLE

```sql
CREATE TABLE student_prospects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    kcpe_marks INT,
    previous_school VARCHAR(255),
    status VARCHAR(50) DEFAULT 'APPLIED' CHECK (status IN ('APPLIED', 'INTERVIEWED', 'ACCEPTED', 'REJECTED')),
    application_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Optional portal access
    admission_number VARCHAR(50) NOT NULL,
    upi_number VARCHAR(50) UNIQUE, -- NEMIS UPI
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    date_of_birth DATE,
    admission_date DATE NOT NULL,
    boarding_type VARCHAR(20) DEFAULT 'DAY' CHECK (boarding_type IN ('DAY', 'BOARDING')),
    student_status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (student_status IN ('ACTIVE', 'SUSPENDED', 'TRANSFERRED', 'CLEARED', 'ALUMNI')),
    special_needs_flags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, admission_number)
);

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    form_level INT NOT NULL CHECK (form_level BETWEEN 1 AND 6), -- Form 1 to Form 4 (or JSS Grade 7-9)
    name VARCHAR(50) NOT NULL, -- e.g., 'Form 1'
    curriculum_type VARCHAR(20) DEFAULT '8-4-4' CHECK (curriculum_type IN ('8-4-4', 'CBC')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- e.g., 'North', 'Blue'
    capacity INT DEFAULT 45,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(class_id, name)
);

CREATE TABLE student_class_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    stream_id UUID NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PROMOTED', 'REPEATED', 'DROPPED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    transfer_type VARCHAR(20) NOT NULL CHECK (transfer_type IN ('IN', 'OUT')),
    transfer_date DATE NOT NULL,
    destination_source_school VARCHAR(255) NOT NULL,
    reason TEXT,
    leaving_certificate_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_clearances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    department VARCHAR(50) NOT NULL CHECK (department IN ('FINANCE', 'LIBRARY', 'SPORTS', 'BOARDING', 'ACADEMICS')),
    cleared_by UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CLEARED', 'REJECTED')),
    comments TEXT,
    clearance_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE alumni (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    graduation_year INT NOT NULL,
    kcse_mean_grade VARCHAR(5),
    kcse_points INT,
    current_occupation VARCHAR(255),
    contact_details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 4. PARENTS & GUARDIANS

```sql
CREATE TABLE parents_guardians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    id_number VARCHAR(50), -- Kenyan National ID
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    occupation VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_parent_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES parents_guardians(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL CHECK (relationship IN ('FATHER', 'MOTHER', 'GUARDIAN', 'SPONSOR')),
    is_primary_contact BOOLEAN DEFAULT false,
    is_fee_payer BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (student_id, parent_id)
);

CREATE TABLE communication_preferences (
    parent_id UUID NOT NULL REFERENCES parents_guardians(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('SMS', 'EMAIL', 'APP_PUSH')),
    opt_in BOOLEAN DEFAULT true,
    PRIMARY KEY (parent_id, channel)
);
```

## 5. STAFF & HR

```sql
CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    employment_type VARCHAR(20) NOT NULL CHECK (employment_type IN ('TSC', 'BOM', 'SUPPORT')),
    tsc_number VARCHAR(50) UNIQUE,
    tpad_number VARCHAR(50) UNIQUE,
    kra_pin VARCHAR(50) NOT NULL,
    national_id VARCHAR(50) NOT NULL UNIQUE,
    nhif_number VARCHAR(50),
    nssf_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(100),
    hire_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ON_LEAVE', 'SUSPENDED', 'TERMINATED', 'RETIRED')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
COMMENT ON COLUMN staff.employment_type IS 'TSC = Teachers Service Commission (Govt employed), BOM = Board of Management (School employed)';

CREATE TABLE staff_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    contract_start DATE NOT NULL,
    contract_end DATE,
    basic_salary DECIMAL(15,4) NOT NULL DEFAULT 0,
    contract_document_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE staff_leave_entitlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL CHECK (leave_type IN ('ANNUAL', 'MATERNITY', 'PATERNITY', 'SICK', 'COMPASSIONATE')),
    days_entitled INT NOT NULL,
    days_taken INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(staff_id, academic_year_id, leave_type)
);

CREATE TABLE staff_leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE staff_attendance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    check_in TIMESTAMPTZ,
    check_out TIMESTAMPTZ,
    status VARCHAR(20) CHECK (status IN ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED')),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(staff_id, log_date)
);

CREATE TABLE staff_performance_appraisals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    score DECIMAL(5,2),
    evaluator_comments TEXT,
    evaluated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 6. PAYROLL (KENYA-SPECIFIC)

```sql
CREATE TABLE payroll_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    period_name VARCHAR(50) NOT NULL, -- e.g., 'August 2025'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PROCESSED', 'APPROVED', 'PAID')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_period_id UUID NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    run_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_by UUID REFERENCES users(id),
    total_gross DECIMAL(15,4) DEFAULT 0,
    total_deductions DECIMAL(15,4) DEFAULT 0,
    total_net DECIMAL(15,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payroll_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_run_id UUID NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    basic_salary DECIMAL(15,4) NOT NULL,
    gross_pay DECIMAL(15,4) NOT NULL,
    taxable_pay DECIMAL(15,4) NOT NULL,
    paye DECIMAL(15,4) NOT NULL DEFAULT 0,
    nssf DECIMAL(15,4) NOT NULL DEFAULT 0,
    nhif DECIMAL(15,4) NOT NULL DEFAULT 0,
    housing_levy DECIMAL(15,4) NOT NULL DEFAULT 0,
    total_allowances DECIMAL(15,4) NOT NULL DEFAULT 0,
    total_deductions DECIMAL(15,4) NOT NULL DEFAULT 0,
    net_pay DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(payroll_run_id, staff_id)
);
COMMENT ON TABLE payroll_entries IS 'Holds finalized payroll computation per staff member, reflecting Kenyan statutory deductions.';

CREATE TABLE payroll_allowances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_entry_id UUID NOT NULL REFERENCES payroll_entries(id) ON DELETE CASCADE,
    allowance_type VARCHAR(100) NOT NULL, -- e.g., 'House Allowance', 'Commuter Allowance'
    amount DECIMAL(15,4) NOT NULL,
    is_taxable BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payroll_deductions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_entry_id UUID NOT NULL REFERENCES payroll_entries(id) ON DELETE CASCADE,
    deduction_type VARCHAR(100) NOT NULL, -- e.g., 'HELB', 'Sacco Loan', 'Advance Recovery'
    amount DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE salary_advances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    request_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(15,4) NOT NULL,
    reason TEXT,
    repayment_months INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'RECOVERED')),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 7. ACADEMICS

```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL, -- e.g., '101' for English
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) CHECK (category IN ('COMPULSORY', 'SCIENCES', 'HUMANITIES', 'TECHNICAL')),
    is_cbc_learning_area BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, code)
);

CREATE TABLE student_subject_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(student_id, subject_id, academic_year_id)
);

CREATE TABLE timetable_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id UUID NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    day_of_week VARCHAR(15) NOT NULL CHECK (day_of_week IN ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE lesson_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_slot_id UUID NOT NULL REFERENCES timetable_slots(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE exam_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., 'End of Term 1 2025'
    exam_type VARCHAR(50) CHECK (exam_type IN ('CAT', 'MID_TERM', 'END_TERM', 'MOCK')),
    weight DECIMAL(5,2) DEFAULT 100.0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE exam_results_844 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_schedule_id UUID NOT NULL REFERENCES exam_schedules(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    marks_scored DECIMAL(5,2) NOT NULL CHECK (marks_scored >= 0 AND marks_scored <= 100),
    grade VARCHAR(2), -- A, A-, B+, etc.
    points INT, -- 12, 11, 10, etc.
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(exam_schedule_id, student_id, subject_id)
);

CREATE TABLE cbc_strands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE, -- Learning Area
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE cbc_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    strand_id UUID NOT NULL REFERENCES cbc_strands(id) ON DELETE CASCADE,
    rubric_score INT NOT NULL CHECK (rubric_score BETWEEN 1 AND 4), -- 1: Below Expectation, 4: Exceeds Expectation
    facilitator_comments TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE academic_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    total_marks DECIMAL(10,2),
    average_marks DECIMAL(5,2),
    mean_grade VARCHAR(2),
    class_teacher_remarks TEXT,
    principal_remarks TEXT,
    generated_at TIMESTAMPTZ DEFAULT now()
);
```

## 8. DISCIPLINE & COUNSELLING

```sql
CREATE TABLE disciplinary_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    reported_by UUID NOT NULL REFERENCES staff(id),
    incident_date TIMESTAMPTZ NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('MINOR', 'MAJOR', 'SEVERE')),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE disciplinary_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES disciplinary_incidents(id) ON DELETE CASCADE,
    action_taken VARCHAR(100) NOT NULL, -- e.g., 'Warning', 'Manual Work', 'Suspension'
    action_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE suspension_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES disciplinary_incidents(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    return_conditions TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE counselling_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    counsellor_id UUID NOT NULL REFERENCES staff(id),
    session_date TIMESTAMPTZ NOT NULL,
    notes TEXT,
    follow_up_required BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 9. BOARDING

```sql
CREATE TABLE hostels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    gender_type VARCHAR(20) NOT NULL CHECK (gender_type IN ('MALE', 'FEMALE', 'MIXED')),
    capacity INT NOT NULL,
    patron_matron_id UUID REFERENCES staff(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE dormitories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hostel_id UUID NOT NULL REFERENCES hostels(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    capacity INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE beds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dormitory_id UUID NOT NULL REFERENCES dormitories(id) ON DELETE CASCADE,
    bed_number VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'OCCUPIED', 'DAMAGED')),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(dormitory_id, bed_number)
);

CREATE TABLE bed_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bed_id UUID NOT NULL REFERENCES beds(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    allocated_date DATE NOT NULL DEFAULT CURRENT_DATE,
    vacated_date DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_leave_passes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    departure_time TIMESTAMPTZ NOT NULL,
    expected_return_time TIMESTAMPTZ NOT NULL,
    actual_return_time TIMESTAMPTZ,
    approved_by UUID REFERENCES staff(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 10. FINANCE - CHART OF ACCOUNTS

```sql
CREATE TABLE financial_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    year_name VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE accounting_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    financial_year_id UUID NOT NULL REFERENCES financial_years(id) ON DELETE CASCADE,
    period_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE account_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE CHECK (name IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('DEBIT', 'CREDIT'))
);

CREATE TABLE account_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_type_id UUID NOT NULL REFERENCES account_types(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., 'Current Assets', 'Operating Expenses'
    description TEXT
);

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    account_category_id UUID NOT NULL REFERENCES account_categories(id),
    parent_id UUID REFERENCES accounts(id),
    account_code VARCHAR(20) NOT NULL,
    name VARCHAR(150) NOT NULL,
    is_control_account BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (school_id, account_code)
);

CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL, -- e.g., 'Science Department', 'Boarding'
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 11. FINANCE - GENERAL LEDGER

```sql
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    entry_number VARCHAR(50) NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference_type VARCHAR(50), -- e.g., 'FEE_PAYMENT', 'PAYROLL', 'AP_INVOICE'
    reference_id UUID,
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'POSTED', 'REVERSED')),
    posted_by UUID REFERENCES users(id),
    posted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(school_id, entry_number)
);

CREATE TABLE journal_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    debit DECIMAL(15,4) NOT NULL DEFAULT 0.0000,
    credit DECIMAL(15,4) NOT NULL DEFAULT 0.0000,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    CHECK (debit >= 0 AND credit >= 0),
    CHECK (NOT (debit > 0 AND credit > 0)) -- A single line cannot have both debit and credit
);

-- Note: See Triggers section below for journal balance validation.

CREATE TABLE period_closures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    accounting_period_id UUID NOT NULL REFERENCES accounting_periods(id),
    closed_by UUID REFERENCES users(id),
    closed_at TIMESTAMPTZ DEFAULT now(),
    retained_earnings_account_id UUID REFERENCES accounts(id)
);
```

## 12. FINANCE - FEE MANAGEMENT

```sql
CREATE TABLE fee_vote_heads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., 'Tuition', 'Boarding', 'RMI', 'Activity'
    account_id UUID NOT NULL REFERENCES accounts(id), -- Maps to a revenue account in GL
    priority INT DEFAULT 1, -- Determines payment allocation order
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fee_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    term_id UUID NOT NULL REFERENCES terms(id),
    boarding_type VARCHAR(20) CHECK (boarding_type IN ('DAY', 'BOARDING', 'ALL')),
    curriculum_type VARCHAR(20) CHECK (curriculum_type IN ('8-4-4', 'CBC', 'ALL')),
    total_amount DECIMAL(15,4) NOT NULL DEFAULT 0.0000,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fee_structure_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fee_structure_id UUID NOT NULL REFERENCES fee_structures(id) ON DELETE CASCADE,
    vote_head_id UUID NOT NULL REFERENCES fee_vote_heads(id),
    amount DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_fee_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    running_balance DECIMAL(15,4) NOT NULL DEFAULT 0.0000, -- Positive = Arrears, Negative = Prepayment
    last_updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fee_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id),
    fee_structure_id UUID REFERENCES fee_structures(id),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    invoice_date DATE NOT NULL,
    total_amount DECIMAL(15,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'UNPAID' CHECK (status IN ('UNPAID', 'PARTIAL', 'PAID', 'VOID')),
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fee_invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fee_invoice_id UUID NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
    vote_head_id UUID NOT NULL REFERENCES fee_vote_heads(id),
    amount DECIMAL(15,4) NOT NULL
);

CREATE TABLE fee_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    receipt_date DATE NOT NULL,
    amount DECIMAL(15,4) NOT NULL,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('MPESA', 'BANK', 'CASH', 'CHEQUE', 'BURSARY')),
    reference_number VARCHAR(100), -- e.g., M-Pesa code, Cheque number
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE fee_receipt_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fee_receipt_id UUID NOT NULL REFERENCES fee_receipts(id) ON DELETE CASCADE,
    fee_invoice_item_id UUID REFERENCES fee_invoice_items(id), -- Null if prepaying
    vote_head_id UUID NOT NULL REFERENCES fee_vote_heads(id),
    allocated_amount DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bursaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    sponsor_name VARCHAR(100) NOT NULL, -- e.g., 'CDF Kibra', 'Ministry of Education'
    total_fund_amount DECIMAL(15,4) NOT NULL,
    received_date DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_bursary_awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bursary_id UUID NOT NULL REFERENCES bursaries(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    amount DECIMAL(15,4) NOT NULL,
    term_id UUID NOT NULL REFERENCES terms(id),
    receipt_id UUID REFERENCES fee_receipts(id), -- Link to the synthesized receipt
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 13. FINANCE - M-PESA & BANKING

```sql
CREATE TABLE mpesa_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    checkout_request_id VARCHAR(100) UNIQUE, -- For STK push
    mpesa_receipt_number VARCHAR(50) UNIQUE, -- e.g., 'QED98XXXX'
    phone_msisdn VARCHAR(15) NOT NULL,
    amount DECIMAL(15,4) NOT NULL,
    account_reference VARCHAR(50), -- Usually Admission Number typed by parent
    result_code VARCHAR(10),
    result_description TEXT,
    transaction_date TIMESTAMPTZ,
    callback_payload JSONB,
    is_processed BOOLEAN DEFAULT false,
    fee_receipt_id UUID REFERENCES fee_receipts(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
COMMENT ON TABLE mpesa_transactions IS 'Logs Daraja API C2B/STK Push responses.';

CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    branch_name VARCHAR(100),
    account_number VARCHAR(50) NOT NULL UNIQUE,
    gl_account_id UUID NOT NULL REFERENCES accounts(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bank_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    statement_date DATE NOT NULL,
    opening_balance DECIMAL(15,4),
    closing_balance DECIMAL(15,4),
    imported_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bank_statement_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_statement_id UUID NOT NULL REFERENCES bank_statements(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    description TEXT,
    reference VARCHAR(100),
    amount DECIMAL(15,4) NOT NULL, -- Positive for deposits, Negative for withdrawals
    is_reconciled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bank_reconciliation_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_statement_line_id UUID NOT NULL REFERENCES bank_statement_lines(id),
    journal_line_id UUID NOT NULL REFERENCES journal_lines(id),
    matched_by UUID REFERENCES users(id),
    matched_at TIMESTAMPTZ DEFAULT now()
);
```

## 14. FINANCE - ACCOUNTS PAYABLE & PROCUREMENT

```sql
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    kra_pin VARCHAR(50),
    phone_number VARCHAR(20),
    email VARCHAR(100),
    ap_account_id UUID REFERENCES accounts(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE purchase_requisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    requisition_number VARCHAR(50) NOT NULL UNIQUE,
    requested_by UUID NOT NULL REFERENCES staff(id),
    department_id UUID REFERENCES cost_centers(id),
    request_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'FULFILLED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE purchase_requisition_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requisition_id UUID NOT NULL REFERENCES purchase_requisitions(id) ON DELETE CASCADE,
    item_description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    estimated_unit_price DECIMAL(15,4)
);

CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    po_number VARCHAR(50) NOT NULL UNIQUE,
    po_date DATE NOT NULL,
    total_amount DECIMAL(15,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ISSUED', 'PARTIAL_RECEIPT', 'RECEIVED', 'CANCELLED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    requisition_item_id UUID REFERENCES purchase_requisition_items(id),
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(15,4) NOT NULL,
    received_quantity DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE goods_received_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID NOT NULL REFERENCES purchase_orders(id),
    grn_number VARCHAR(50) NOT NULL UNIQUE,
    received_date DATE NOT NULL,
    received_by UUID NOT NULL REFERENCES staff(id),
    delivery_note_number VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE grn_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grn_id UUID NOT NULL REFERENCES goods_received_notes(id) ON DELETE CASCADE,
    po_item_id UUID NOT NULL REFERENCES purchase_order_items(id),
    quantity_received DECIMAL(10,2) NOT NULL,
    condition_remarks TEXT
);

CREATE TABLE supplier_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    po_id UUID REFERENCES purchase_orders(id),
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_amount DECIMAL(15,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'UNPAID' CHECK (status IN ('UNPAID', 'PARTIAL', 'PAID', 'VOID')),
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ap_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_invoice_id UUID NOT NULL REFERENCES supplier_invoices(id),
    payment_date DATE NOT NULL,
    amount DECIMAL(15,4) NOT NULL,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    journal_entry_id UUID REFERENCES journal_entries(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 15. FINANCE - ASSETS

```sql
CREATE TABLE asset_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    depreciation_method VARCHAR(50) CHECK (depreciation_method IN ('STRAIGHT_LINE', 'REDUCING_BALANCE')),
    depreciation_rate DECIMAL(5,2),
    asset_account_id UUID REFERENCES accounts(id),
    accumulated_depreciation_account_id UUID REFERENCES accounts(id),
    depreciation_expense_account_id UUID REFERENCES accounts(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_category_id UUID NOT NULL REFERENCES asset_categories(id),
    asset_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_cost DECIMAL(15,4) NOT NULL,
    salvage_value DECIMAL(15,4) DEFAULT 0,
    useful_life_years INT,
    current_value DECIMAL(15,4) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISPOSED', 'WRITTEN_OFF')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 16. INVENTORY & STORES

```sql
CREATE TABLE inventory_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- e.g., 'Main Kitchen Store', 'Stationery Store'
    location TEXT
);

CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES inventory_categories(id),
    item_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL, -- 'KGs', 'Pieces', 'Reams'
    reorder_level DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE stock_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity_on_hand DECIMAL(10,2) NOT NULL DEFAULT 0,
    average_unit_cost DECIMAL(15,4) NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT now(),
    UNIQUE(inventory_item_id, warehouse_id)
);

CREATE TABLE stock_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    issued_to UUID REFERENCES staff(id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    department_id UUID REFERENCES cost_centers(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 17. LIBRARY

```sql
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    isbn VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150),
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE book_copies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    accession_number VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'BORROWED', 'LOST', 'DAMAGED')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE book_loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_copy_id UUID NOT NULL REFERENCES book_copies(id),
    student_id UUID REFERENCES students(id),
    staff_id UUID REFERENCES staff(id),
    loan_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'RETURNED', 'OVERDUE', 'LOST')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 18. TRANSPORT

```sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    registration_number VARCHAR(20) NOT NULL UNIQUE, -- e.g., KCA 123X
    capacity INT NOT NULL,
    driver_id UUID REFERENCES staff(id),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MAINTENANCE', 'OUT_OF_SERVICE')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    fare_amount DECIMAL(15,4) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_route_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    route_id UUID NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES terms(id),
    type VARCHAR(20) CHECK (type IN ('ONE_WAY', 'TWO_WAY')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 19. COMMUNICATION

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('SMS', 'EMAIL', 'SYSTEM')),
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sms_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    provider_message_id VARCHAR(100),
    delivery_status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 20. VISITORS & GATE

```sql
CREATE TABLE visitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    id_number VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE visitor_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visitor_id UUID NOT NULL REFERENCES visitors(id),
    purpose_of_visit TEXT NOT NULL,
    host_staff_id UUID REFERENCES staff(id),
    check_in_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    check_out_time TIMESTAMPTZ,
    vehicle_registration VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE gate_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    event_type VARCHAR(10) CHECK (event_type IN ('ENTRY', 'EXIT')),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    logged_by UUID REFERENCES users(id) -- Usually the guard scanning the ID
);
```

---

## 21. DATABASE TRIGGERS

### A. Journal Entry Double-Entry Validation
Ensures every journal entry obeys the double-entry accounting principle (Debits = Credits).

```sql
CREATE OR REPLACE FUNCTION check_journal_entry_balance()
RETURNS TRIGGER AS $$
DECLARE
    total_debit DECIMAL(15,4);
    total_credit DECIMAL(15,4);
BEGIN
    -- Only enforce if status is moving to POSTED
    IF NEW.status = 'POSTED' THEN
        SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
        INTO total_debit, total_credit
        FROM journal_lines
        WHERE journal_entry_id = NEW.id;

        IF total_debit <> total_credit THEN
            RAISE EXCEPTION 'Journal entry % unbalanced. Total Debit: %, Total Credit: %', NEW.entry_number, total_debit, total_credit;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_journal_balance
BEFORE UPDATE OF status ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION check_journal_entry_balance();
```

### B. Audit Log Auto-Population
A generic trigger to capture all insert/update/delete operations on critical tables.

```sql
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
BEGIN
    -- Assuming application sets a session variable 'app.current_user_id'
    BEGIN
        current_user_id := current_setting('app.current_user_id')::UUID;
    EXCEPTION WHEN OTHERS THEN
        current_user_id := NULL;
    END;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO system_audit_logs (table_name, row_id, action, new_value, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW)::jsonb, current_user_id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO system_audit_logs (table_name, row_id, action, old_value, new_value, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb, current_user_id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO system_audit_logs (table_name, row_id, action, old_value, user_id)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD)::jsonb, current_user_id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply to critical tables
CREATE TRIGGER audit_students_trigger AFTER INSERT OR UPDATE OR DELETE ON students FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
CREATE TRIGGER audit_staff_trigger AFTER INSERT OR UPDATE OR DELETE ON staff FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
CREATE TRIGGER audit_fee_receipts_trigger AFTER INSERT OR UPDATE OR DELETE ON fee_receipts FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

---

## 22. INDEXES (Performance Optimization)

```sql
-- Multi-tenancy indexes (critical for filtering by school)
CREATE INDEX idx_students_school_id ON students(school_id);
CREATE INDEX idx_staff_school_id ON staff(school_id);
CREATE INDEX idx_accounts_school_id ON accounts(school_id);
CREATE INDEX idx_journal_entries_school_id ON journal_entries(school_id);

-- Lookup/Search indexes
CREATE INDEX idx_students_upi ON students(upi_number);
CREATE INDEX idx_students_admission ON students(admission_number);
CREATE INDEX idx_staff_tsc_number ON staff(tsc_number);
CREATE INDEX idx_staff_national_id ON staff(national_id);
CREATE INDEX idx_mpesa_receipt ON mpesa_transactions(mpesa_receipt_number);

-- Finance partial indexes for faster calculation
CREATE INDEX idx_journal_lines_account_id ON journal_lines(account_id);
CREATE INDEX idx_journal_lines_journal_id ON journal_lines(journal_entry_id);
CREATE INDEX idx_unpaid_invoices ON fee_invoices(student_id) WHERE status IN ('UNPAID', 'PARTIAL');

-- Composite indexes for frequent queries
CREATE INDEX idx_exam_results_student_subject ON exam_results_844(student_id, subject_id);
CREATE INDEX idx_attendance_student_date ON lesson_attendance(student_id, date);
```

---

## 23. VIEWS AND MATERIALIZED VIEWS

### A. Account Balances View
Generates real-time trial balance figures.

```sql
CREATE OR REPLACE VIEW v_account_balances AS
SELECT 
    a.school_id,
    a.id AS account_id,
    a.account_code,
    a.name AS account_name,
    at.name AS account_type,
    at.normal_balance,
    COALESCE(SUM(jl.debit), 0) AS total_debit,
    COALESCE(SUM(jl.credit), 0) AS total_credit,
    CASE 
        WHEN at.normal_balance = 'DEBIT' THEN COALESCE(SUM(jl.debit), 0) - COALESCE(SUM(jl.credit), 0)
        ELSE COALESCE(SUM(jl.credit), 0) - COALESCE(SUM(jl.debit), 0)
    END AS current_balance
FROM accounts a
JOIN account_categories ac ON a.account_category_id = ac.id
JOIN account_types at ON ac.account_type_id = at.id
LEFT JOIN journal_lines jl ON a.id = jl.account_id
LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id AND je.status = 'POSTED'
GROUP BY a.school_id, a.id, a.account_code, a.name, at.name, at.normal_balance;
```

### B. Student Fee Balance View
Summary of student fee standings for fast dashboard rendering.

```sql
CREATE OR REPLACE VIEW v_student_fee_balances AS
SELECT 
    s.id AS student_id,
    s.school_id,
    s.admission_number,
    s.first_name || ' ' || s.last_name AS student_name,
    c.name AS class_name,
    st.name AS stream_name,
    sfa.running_balance AS current_balance
FROM students s
JOIN student_fee_accounts sfa ON s.id = sfa.student_id
LEFT JOIN student_class_enrollments sce ON s.id = sce.student_id AND sce.status = 'ACTIVE'
LEFT JOIN streams st ON sce.stream_id = st.id
LEFT JOIN classes c ON st.class_id = c.id;
```

### C. Payroll Summary Materialized View
For reporting on heavy payroll records per month.

```sql
CREATE MATERIALIZED VIEW mv_payroll_summary AS
SELECT 
    pp.school_id,
    pp.id AS payroll_period_id,
    pp.period_name,
    COUNT(pe.id) AS total_employees,
    SUM(pe.basic_salary) AS total_basic_salary,
    SUM(pe.gross_pay) AS total_gross_pay,
    SUM(pe.paye) AS total_paye,
    SUM(pe.nssf) AS total_nssf,
    SUM(pe.nhif) AS total_nhif,
    SUM(pe.housing_levy) AS total_housing_levy,
    SUM(pe.net_pay) AS total_net_pay
FROM payroll_periods pp
JOIN payroll_runs pr ON pp.id = pr.payroll_period_id
JOIN payroll_entries pe ON pr.id = pe.payroll_run_id
GROUP BY pp.school_id, pp.id, pp.period_name;

-- Note: Materialized views require periodic refreshing, typically via a cron job:
-- REFRESH MATERIALIZED VIEW mv_payroll_summary;
```
