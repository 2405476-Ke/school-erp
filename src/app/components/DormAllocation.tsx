/**
 * DormAllocation Component
 *
 * Manage dormitory bed allocations:
 * - View dorm layout with bed status
 * - Assign students to beds
 * - Track occupancy and maintenance status
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { apiGet, apiPost } from '@/services/api';
import { getErrorMessage } from '@/types/api';
import type { BedAllocation } from '@/types/api';

interface AllocationForm {
  studentId: string;
  dormName: string;
  bedNumber: string;
}

export function DormAllocation() {
  const [allocations, setAllocations] = useState<BedAllocation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<AllocationForm>({
    studentId: '',
    dormName: '',
    bedNumber: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch allocations
  useEffect(() => {
    const fetchAllocations = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<BedAllocation[]>('/boarding/bed-allocations');
        setAllocations(result || []);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load allocations';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchAllocations();
  }, []);

  // Handle allocation submission
  const handleAllocate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.studentId || !form.dormName || !form.bedNumber) {
      setSubmitError('Please fill in all fields');
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError(null);

      await apiPost('/boarding/bed-allocations', {
        student_id: form.studentId,
        dorm_name: form.dormName,
        bed_number: form.bedNumber,
      });

      setSubmitSuccess(true);
      setForm({ studentId: '', dormName: '', bedNumber: '' });
      
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (err) {
      const errorMessage = (err && typeof err === 'object' && 'response' in err)
        ? getErrorMessage((err as any).response?.data)
        : 'Failed to allocate bed';
      setSubmitError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const dorms = [...new Set(allocations.map(a => a.dorm_name))];
  const occupied = allocations.filter(a => a.status === 'ACTIVE').length;
  const vacant = allocations.filter(a => a.status === 'VACANT').length;
  const maintenance = allocations.filter(a => a.status === 'MAINTENANCE').length;

  return (
    <div>
      <PageHeader
        title="Dorm & Bed Allocation"
        subtitle="Manage student housing assignments"
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
        <KPICard label="Occupied" value={occupied} delta="Active beds" deltaDir="up" />
        <KPICard label="Vacant" value={vacant} delta="Available" deltaDir="up" />
        <KPICard label="Maintenance" value={maintenance} delta="Out of service" deltaDir="down" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Allocation Form */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Allocate Bed
          </p>

          {submitSuccess && (
            <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-3 mb-4">
              <div className="flex items-start gap-2">
                <CheckCircle size={18} className="text-[#1F6F4A] flex-shrink-0 mt-0.5" />
                <p className="text-xs text-[#1F6F4A] font-['IBM_Plex_Sans']">
                  Bed allocated successfully
                </p>
              </div>
            </div>
          )}

          {submitError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-3 mb-4">
              <div className="flex items-start gap-2">
                <XCircle size={18} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
                <p className="text-xs text-[#9C3B2E] font-['IBM_Plex_Sans']">
                  {submitError}
                </p>
              </div>
            </div>
          )}

          <form onSubmit={handleAllocate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Student ID *
              </label>
              <input
                type="text"
                value={form.studentId}
                onChange={(e) => setForm({ ...form, studentId: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Student ID / UPI"
                disabled={submitting}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Dormitory *
              </label>
              <select
                value={form.dormName}
                onChange={(e) => setForm({ ...form, dormName: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                disabled={submitting}
              >
                <option value="">Select dorm...</option>
                <option value="Maisha">Maisha Dorm</option>
                <option value="Amani">Amani Dorm</option>
                <option value="Furaha">Furaha Dorm</option>
                <option value="Uhuru">Uhuru Dorm</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Bed Number *
              </label>
              <input
                type="text"
                value={form.bedNumber}
                onChange={(e) => setForm({ ...form, bedNumber: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="e.g., 14 or A-14"
                disabled={submitting}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#1F6F4A] text-white px-4 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <span className="animate-spin">↻</span>
                  Allocating...
                </>
              ) : (
                'Allocate Bed'
              )}
            </button>
          </form>
        </div>

        {/* Allocations List */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Current Allocations ({allocations.length})
            </p>

            {loading ? (
              <div className="text-center py-8">
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading...</p>
              </div>
            ) : allocations.length === 0 ? (
              <div className="text-center py-8 bg-[#F3EFE4] rounded-sm">
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
                  No bed allocations yet
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {allocations.map((alloc) => (
                  <div
                    key={alloc.id}
                    className="p-3 border border-[#DCD6C4] rounded-sm flex items-start justify-between hover:bg-[#F3EFE4]"
                  >
                    <div className="flex-1">
                      <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans'] text-sm">
                        {alloc.student_name}
                      </p>
                      <p className="text-xs text-[#7A8078] font-['IBM_Plex_Mono'] mt-1">
                        {alloc.dorm_name} · Bed {alloc.bed_number} (Room {alloc.room_number})
                      </p>
                    </div>
                    <StatusTag variant={alloc.status === 'ACTIVE' ? 'ok' : alloc.status === 'MAINTENANCE' ? 'bad' : 'neutral'} label={alloc.status} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
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
