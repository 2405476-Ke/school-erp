/**
 * StudentProfile Component
 *
 * Multi-tab student profile with:
 * - Lazy-loaded data fetching (only fetch active tab)
 * - Real-time data from 4+ backend endpoints
 * - Data transformations (currency formatting, date formatting, etc.)
 * - Loading states per tab
 */

import React, { useState, useEffect } from 'react';
import { apiGet } from '@/services/api';
import { tokenManager } from '@/services/api';
import { formatKES, formatDate, formatStudentName } from '@/services/formatting';
import type { 
  Student, 
  FeeAccountLine, 
  AssessmentEntry, 
  DisciplineCase 
} from '@/types/api';

interface StudentProfileProps {
  studentId?: string;
}

// ─── Custom Hooks for Each Tab's Data ───────────────────────────────────────

/**
 * Hook: Fetch student overview data
 * Endpoint: GET /admissions/students/{id}
 */
function useStudentOverview(studentId: string | undefined) {
  const [data, setData] = useState<Student | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<Student>(`/admissions/students/${studentId}`);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load student data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch fee account data
 * Endpoint: GET /finance/fee-accounts/{id}
 * Transformation 3.3: Apply KES formatting
 */
function useFeeAccount(studentId: string | undefined) {
  const [data, setData] = useState<FeeAccountLine[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<{ fee_account_lines: FeeAccountLine[] }>(
          `/finance/fee-accounts/${studentId}`
        );
        setData(result?.fee_account_lines || null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fee data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch academic assessment data
 * Endpoint: GET /academics/assessment-entries?student_id={id}
 */
function useStudentAcademics(studentId: string | undefined) {
  const [data, setData] = useState<AssessmentEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<AssessmentEntry[]>(
          `/academics/assessment-entries?student_id=${studentId}`
        );
        setData(result || null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load academic data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch discipline cases data
 * Endpoint: GET /boarding/discipline-cases?student_id={id}
 */
function useStudentDiscipline(studentId: string | undefined) {
  const [data, setData] = useState<DisciplineCase[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<DisciplineCase[]>(
          `/boarding/discipline-cases?student_id=${studentId}`
        );
        setData(result || null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load discipline data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function StudentProfile({ studentId }: StudentProfileProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const tabs = ['overview', 'academic', 'finance', 'disciplinary', 'boarding', 'documents'];

  // Get student ID from URL params or props (default to demo ID for now)
  const effectiveStudentId = studentId || 'demo-student-id';

  // Lazy-load data: only fetch when tab becomes active
  const overview = useStudentOverview(activeTab === 'overview' ? effectiveStudentId : undefined);
  const academics = useStudentAcademics(activeTab === 'academic' ? effectiveStudentId : undefined);
  const fees = useFeeAccount(activeTab === 'finance' ? effectiveStudentId : undefined);
  const discipline = useStudentDiscipline(activeTab === 'disciplinary' ? effectiveStudentId : undefined);

  // Generate initials from student name
  const getInitials = (student: Student | null) => {
    if (!student) return 'N/A';
    const first = student.first_name[0];
    const last = student.last_name[0];
    return `${first}${last}`.toUpperCase();
  };

  const studentName = overview.data
    ? formatStudentName(overview.data.first_name, overview.data.last_name)
    : 'Loading...';

  return (
    <div>
      <PageHeader
        title={studentName}
        subtitle={overview.data ? `${overview.data.admission_number} · ${overview.data.current_class} Stream ${overview.data.current_stream}` : 'Loading...'}
      />

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-4 border-b border-[#DCD6C4] overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-xs uppercase tracking-wide font-semibold font-['IBM_Plex_Sans'] capitalize border-b-2 transition-colors whitespace-nowrap
              ${activeTab === t ? 'border-[#1F6F4A] text-[#1F6F4A]' : 'border-transparent text-[#7A8078] hover:text-[#16241D]'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <OverviewTab student={overview.data} loading={overview.loading} error={overview.error} />
      )}

      {/* Tab: Academic */}
      {activeTab === 'academic' && (
        <AcademicTab academics={academics.data} loading={academics.loading} error={academics.error} />
      )}

      {/* Tab: Finance */}
      {activeTab === 'finance' && (
        <FinanceTab fees={fees.data} loading={fees.loading} error={fees.error} student={overview.data} />
      )}

      {/* Tab: Disciplinary */}
      {activeTab === 'disciplinary' && (
        <DisciplinaryTab cases={discipline.data} loading={discipline.loading} error={discipline.error} />
      )}

      {/* Tab: Boarding (Placeholder) */}
      {activeTab === 'boarding' && (
        <PlaceholderTab label="Boarding Information" />
      )}

      {/* Tab: Documents (Placeholder) */}
      {activeTab === 'documents' && (
        <PlaceholderTab label="Document Status" />
      )}
    </div>
  );
}

// ─── Tab Components ─────────────────────────────────────────────────────────

interface TabProps {
  loading: boolean;
  error: string | null;
}

/**
 * Overview Tab
 * Shows basic student info, guardian contacts, KPIs
 */
function OverviewTab({ student, loading, error }: TabProps & { student: Student | null }) {
  if (error) {
    return (
      <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
          ⚠️ Failed to load student data: {error}
        </p>
      </div>
    );
  }

  if (loading || !student) {
    return <TabLoadingSpinner />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {/* Student Card */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 flex flex-col items-center gap-3">
        <div className="w-20 h-20 rounded-full bg-[#E7F0EA] flex items-center justify-center">
          <span className="font-['Fraunces'] text-2xl text-[#1F6F4A]">
            {student.first_name[0]}{student.last_name[0]}
          </span>
        </div>
        <div className="text-center">
          <p className="font-['Fraunces'] text-lg text-[#16241D]">
            {formatStudentName(student.first_name, student.last_name)}
          </p>
          <p className="font-['IBM_Plex_Mono'] text-xs text-[#7A8078] mt-0.5">
            UPI: {student.upi || 'N/A'}
          </p>
        </div>
        <StatusTag
          variant={student.is_active ? 'ok' : 'bad'}
          label={student.is_active ? 'Active' : 'Inactive'}
        />
        <div className="w-full border-t border-[#DCD6C4] pt-3 space-y-1.5">
          {[
            ['Class', `${student.current_class} · Stream ${student.current_stream}`],
            ['Category', student.category === 'BOARDER' ? 'Boarder' : 'Day Scholar'],
            ['Gender', student.gender === 'MALE' ? 'Male' : 'Female'],
            ['Enrolled', formatDate(student.created_at)],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between text-xs font-['IBM_Plex_Sans']">
              <span className="text-[#7A8078]">{k}</span>
              <span className="text-[#16241D] font-medium">{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Guardian Contacts & KPIs */}
      <div className="lg:col-span-2 space-y-4">
        {/* Guardian Contacts (Placeholder for now) */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
            Guardian Contacts
          </p>
          <div className="space-y-2">
            {[
              { name: 'Guardian Name', phone: 'N/A', rel: 'Contact' },
            ].map((g) => (
              <div key={g.name} className="flex items-center gap-4 py-2 border-b border-[#DCD6C4] last:border-0">
                <div className="flex-1">
                  <p className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{g.name}</p>
                  <p className="text-xs text-[#7A8078] font-['IBM_Plex_Mono']">{g.phone}</p>
                </div>
                <StatusTag variant="neutral" label={g.rel} />
              </div>
            ))}
          </div>
        </div>

        {/* KPI Cards (Placeholder) */}
        <div className="grid grid-cols-3 gap-3">
          <KPICard label="Attendance %" value="N/A" delta="Loading..." deltaDir="up" />
          <KPICard label="Fee Balance" value="N/A" delta="Loading..." deltaDir="down" mono />
          <KPICard label="Incidents" value="0" delta="Loading..." deltaDir="up" />
        </div>
      </div>
    </div>
  );
}

/**
 * Academic Tab
 * Shows grades and assessment data
 */
function AcademicTab({
  academics,
  loading,
  error,
}: TabProps & { academics: AssessmentEntry[] | null }) {
  if (error) {
    return (
      <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
          ⚠️ Failed to load academic data: {error}
        </p>
      </div>
    );
  }

  if (loading || !academics) {
    return <TabLoadingSpinner />;
  }

  if (academics.length === 0) {
    return (
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
          No assessment entries found
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
      <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
        Grade Summary
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                Subject
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                Grade
              </th>
            </tr>
          </thead>
          <tbody>
            {academics.map((entry, idx) => (
              <tr key={idx} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                <td className="px-4 py-3 text-[#16241D]">{entry.subject_name || 'Unknown'}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#16241D]">
                  {entry.score || 'N/A'}
                </td>
                <td className="px-4 py-3">
                  {entry.grade ? (
                    <StatusTag variant="ok" label={entry.grade} />
                  ) : (
                    <StatusTag variant="neutral" label="—" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Finance Tab
 * Shows fee account with Transformation 3.3 (KES formatting)
 */
function FinanceTab({
  fees,
  loading,
  error,
  student,
}: TabProps & { fees: FeeAccountLine[] | null; student: Student | null }) {
  if (error) {
    return (
      <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
          ⚠️ Failed to load fee data: {error}
        </p>
      </div>
    );
  }

  if (loading || !fees) {
    return <TabLoadingSpinner />;
  }

  // Calculate totals
  const totalAmount = fees.reduce((sum, line) => sum + parseFloat(line.total_amount || '0'), 0);
  const totalPaid = fees.reduce((sum, line) => sum + parseFloat(line.amount_paid || '0'), 0);
  const totalBalance = fees.reduce((sum, line) => sum + parseFloat(line.amount_balance || '0'), 0);

  return (
    <div className="space-y-4">
      {/* Summary KPIs */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <KPICard
          label="Outstanding Balance"
          value={formatKES(totalBalance)}
          delta={totalBalance > 0 ? 'Amount owed' : 'Fully paid'}
          deltaDir={totalBalance > 0 ? 'down' : 'up'}
          mono
        />
        <KPICard
          label="Total Paid"
          value={formatKES(totalPaid)}
          delta={`${fees.length} line items`}
          deltaDir="up"
          mono
        />
        <KPICard
          label="Total Charge"
          value={formatKES(totalAmount)}
          mono
        />
      </div>

      {/* Fee Ledger */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
          Fee Breakdown
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                  Fee Item
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                  Amount
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                  Paid
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                  Balance
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {fees.map((line, idx) => {
                const balance = parseFloat(line.amount_balance || '0');
                const paid = parseFloat(line.amount_paid || '0');
                const total = parseFloat(line.total_amount || '0');
                const status = balance <= 0 ? 'ok' : balance > 0 && paid > 0 ? 'warn' : 'bad';

                return (
                  <tr key={idx} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                    <td className="px-4 py-3 text-[#16241D]">{line.fee_item_name}</td>
                    <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#16241D]">
                      {formatKES(total)}
                    </td>
                    <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#1F6F4A]">
                      {formatKES(paid)}
                    </td>
                    <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#9C3B2E]">
                      {formatKES(balance)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusTag
                        variant={status}
                        label={balance <= 0 ? 'Paid' : 'Pending'}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-[#16241D] bg-[#F3EFE4] font-semibold">
                <td className="px-4 py-3 text-xs uppercase text-[#7A8078]">Totals</td>
                <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#16241D]">
                  {formatKES(totalAmount)}
                </td>
                <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#1F6F4A]">
                  {formatKES(totalPaid)}
                </td>
                <td className="px-4 py-3 text-right font-['IBM_Plex_Mono'] text-[#9C3B2E]">
                  {formatKES(totalBalance)}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * Disciplinary Tab
 * Shows discipline cases
 */
function DisciplinaryTab({
  cases,
  loading,
  error,
}: TabProps & { cases: DisciplineCase[] | null }) {
  if (error) {
    return (
      <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
          ⚠️ Failed to load discipline data: {error}
        </p>
      </div>
    );
  }

  if (loading || !cases) {
    return <TabLoadingSpinner />;
  }

  if (cases.length === 0) {
    return (
      <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-6 text-center">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">
          ✓ Clean record — no discipline cases recorded
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
      <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
        Discipline Cases
      </p>
      <div className="space-y-3">
        {cases.map((caseRecord, idx) => (
          <div key={idx} className="border border-[#DCD6C4] rounded-sm p-3">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div>
                <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans']">
                  {caseRecord.incident_description || 'Incident'}
                </p>
                <p className="text-xs text-[#7A8078] font-['IBM_Plex_Mono'] mt-1">
                  {formatDate(caseRecord.incident_date)}
                </p>
              </div>
              <StatusTag
                variant={caseRecord.case_status === 'CLOSED' ? 'ok' : 'warn'}
                label={caseRecord.case_status || 'Unknown'}
              />
            </div>
            {caseRecord.action_taken && (
              <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
                Action: {caseRecord.action_taken}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Placeholder Tab
 * For tabs not yet wired to backend
 */
function PlaceholderTab({ label }: { label: string }) {
  return (
    <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
      <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
        {label} — Coming soon
      </p>
    </div>
  );
}

// ─── Loading & UI Components ────────────────────────────────────────────────

function TabLoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-center">
        <div className="inline-block animate-spin mb-3">
          <svg
            className="h-8 w-8 text-[#1F6F4A]"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
          Loading...
        </p>
      </div>
    </div>
  );
}

// ─── Reusable UI Components ─────────────────────────────────────────────────

type StatusVariant = 'ok' | 'warn' | 'bad' | 'neutral';

function StatusTag({ variant, label }: { variant: StatusVariant; label: string }) {
  const styles: Record<StatusVariant, string> = {
    ok: 'bg-[#E7F0EA] text-[#1F6F4A]',
    warn: 'bg-[#F5EAD6] text-[#B5751F]',
    bad: 'bg-[#F7E6E2] text-[#9C3B2E]',
    neutral: 'bg-[#EBE7DC] text-[#7A8078]',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-['IBM_Plex_Sans'] ${styles[variant]}`}
    >
      {label}
    </span>
  );
}

interface KPICardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaDir?: 'up' | 'down';
  mono?: boolean;
}

function KPICard({ label, value, delta, deltaDir, mono }: KPICardProps) {
  return (
    <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
      <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">
        {label}
      </p>
      <p className={`text-lg font-bold text-[#16241D] ${mono ? "font-['IBM_Plex_Mono']" : "font-['Fraunces']"}`}>
        {value}
      </p>
      {delta && (
        <p className={`text-xs mt-1.5 font-['IBM_Plex_Sans'] ${deltaDir === 'up' ? 'text-[#1F6F4A]' : 'text-[#9C3B2E]'}`}>
          {deltaDir === 'up' ? '↑' : '↓'} {delta}
        </p>
      )}
    </div>
  );
}

function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-3xl font-bold font-['Fraunces'] text-[#16241D] mb-1">
        {title}
      </h1>
      <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">{subtitle}</p>
    </div>
  );
}
