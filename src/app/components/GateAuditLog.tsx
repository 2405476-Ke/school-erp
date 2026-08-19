/**
 * GateAuditLog Component
 *
 * View and filter gate security audit trail:
 * - All student entries/exits
 * - Visitor check-ins/check-outs
 * - Blocked access attempts
 */

import React, { useState, useEffect } from 'react';
import { XCircle, Filter } from 'lucide-react';
import { apiGet } from '@/services/api';
import { formatDate } from '@/services/formatting';
import { getErrorMessage } from '@/types/api';
import type { GateAuditEntry } from '@/types/api';

interface FilterState {
  entryType: string;
  status: string;
  personType: string;
  startDate: string;
  endDate: string;
}

export function GateAuditLog() {
  const [logs, setLogs] = useState<GateAuditEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<GateAuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<FilterState>({
    entryType: '',
    status: '',
    personType: '',
    startDate: '',
    endDate: '',
  });

  // Fetch audit logs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<GateAuditEntry[]>('/security/gate/audit-report');
        setLogs(result || []);
        setFilteredLogs(result || []);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load audit logs';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = logs;

    if (filters.entryType) {
      filtered = filtered.filter(l => l.entry_type === filters.entryType);
    }
    if (filters.status) {
      filtered = filtered.filter(l => l.action_status === filters.status);
    }
    if (filters.personType) {
      filtered = filtered.filter(l => l.person_type === filters.personType);
    }
    if (filters.startDate) {
      filtered = filtered.filter(l => new Date(l.timestamp) >= new Date(filters.startDate));
    }
    if (filters.endDate) {
      filtered = filtered.filter(l => new Date(l.timestamp) <= new Date(filters.endDate));
    }

    setFilteredLogs(filtered);
  }, [filters, logs]);

  const blockedCount = logs.filter(l => l.action_status === 'BLOCKED').length;
  const studentEntries = logs.filter(l => l.entry_type.includes('STUDENT')).length;
  const visitorEntries = logs.filter(l => l.entry_type.includes('VISITOR')).length;

  return (
    <div>
      <PageHeader
        title="Gate Security Audit Log"
        subtitle="View all entry, exit, and access events"
      />

      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
            <p className="text-sm text-[#9C3B2E] font-['IBM_Plex_Sans']">{error}</p>
          </div>
        </div>
      )}

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <KPICard label="Student Traffic" value={studentEntries} delta="entries/exits" />
        <KPICard label="Visitor Check-ins" value={visitorEntries} delta="total" />
        <KPICard
          label="Blocked Access"
          value={blockedCount}
          delta={blockedCount > 0 ? '⚠ Review needed' : '—'}
          deltaDir={blockedCount > 0 ? 'down' : 'up'}
        />
      </div>

      {/* Filters */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 mb-6">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4 flex items-center gap-2">
          <Filter size={12} /> Filters
        </p>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
              Type
            </label>
            <select
              value={filters.entryType}
              onChange={(e) => setFilters({ ...filters, entryType: e.target.value })}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">All types</option>
              <option value="STUDENT_ENTRY">Student Entry</option>
              <option value="STUDENT_EXIT">Student Exit</option>
              <option value="VISITOR_CHECKIN">Visitor Check-in</option>
              <option value="VISITOR_CHECKOUT">Visitor Check-out</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">All status</option>
              <option value="ALLOWED">Allowed</option>
              <option value="BLOCKED">Blocked</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
              Person
            </label>
            <select
              value={filters.personType}
              onChange={(e) => setFilters({ ...filters, personType: e.target.value })}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">All persons</option>
              <option value="STUDENT">Student</option>
              <option value="VISITOR">Visitor</option>
              <option value="STAFF">Staff</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
              From Date
            </label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
              To Date
            </label>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            />
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
          Audit Records ({filteredLogs.length})
        </p>

        {loading ? (
          <div className="text-center py-8">
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading audit logs...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8 bg-[#F3EFE4] rounded-sm">
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
              No audit records matching filters
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['IBM_Plex_Sans']">
              <thead>
                <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Timestamp
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Type
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Person
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Category
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide">
                    Officer
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, idx) => (
                  <tr key={idx} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs">
                      {formatDate(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {log.entry_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-semibold text-[#16241D]">{log.person_name}</p>
                        <p className="text-xs text-[#7A8078]">ID: {log.person_id}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {log.person_type}
                    </td>
                    <td className="px-4 py-3">
                      <StatusTag
                        variant={log.action_status === 'ALLOWED' ? 'ok' : 'bad'}
                        label={log.action_status}
                      />
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {log.officer_name}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Components ────────────────────────────────────────────────────────────

type StatusVariant = 'ok' | 'warn' | 'bad' | 'neutral';

function StatusTag({ variant, label }: { variant: StatusVariant; label: string }) {
  const styles: Record<StatusVariant, string> = {
    ok: 'bg-[#E7F0EA] text-[#1F6F4A]',
    warn: 'bg-[#F5EAD6] text-[#B5751F]',
    bad: 'bg-[#F7E6E2] text-[#9C3B2E]',
    neutral: 'bg-[#EBE7DC] text-[#7A8078]',
  };

  return (
    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold font-['IBM_Plex_Sans'] ${styles[variant]}`}>
      {label}
    </span>
  );
}

function KPICard({
  label,
  value,
  delta,
  deltaDir,
}: {
  label: string;
  value: number;
  delta?: string;
  deltaDir?: 'up' | 'down';
}) {
  return (
    <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
      <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">
        {label}
      </p>
      <p className="text-2xl font-bold text-[#16241D] font-['Fraunces']">
        {value}
      </p>
      {delta && (
        <p className={`text-xs mt-1 font-['IBM_Plex_Sans'] ${deltaDir === 'up' ? 'text-[#1F6F4A]' : 'text-[#9C3B2E]'}`}>
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
