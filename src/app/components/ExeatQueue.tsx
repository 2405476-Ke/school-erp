/**
 * ExeatQueue Component
 *
 * Display students currently on exeat (leave):
 * - Show departure and expected return times
 * - Mark students as returned
 * - Alert for overdue returns
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { apiGet, apiPost } from '@/services/api';
import { formatDate } from '@/services/formatting';
import { getErrorMessage } from '@/types/api';
import type { ExeatQueueEntry } from '@/types/api';

export function ExeatQueue() {
  const [queue, setQueue] = useState<ExeatQueueEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markingReturned, setMarkingReturned] = useState<string | null>(null);

  useEffect(() => {
    const fetchQueue = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<ExeatQueueEntry[]>('/boarding/exeat-queue');
        setQueue(result || []);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load exeat queue';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchQueue();
  }, []);

  const handleMarkReturned = async (studentId: string) => {
    try {
      setMarkingReturned(studentId);
      await apiPost(`/boarding/exeat-queue/${studentId}/mark-returned`, {});
      setQueue(queue.filter(q => q.student_id !== studentId));
    } catch (err) {
      const msg = (err && typeof err === 'object' && 'response' in err) ? getErrorMessage((err as any).response?.data) : 'Failed to mark student as returned';
      alert(msg);
    } finally {
      setMarkingReturned(null);
    }
  };

  const departed = queue.filter(q => q.status === 'DEPARTED');
  const overdue = queue.filter(q => q.status === 'OVERDUE');
  const returned = queue.filter(q => q.status === 'RETURNED');

  return (
    <div>
      <PageHeader
        title="Exeat Queue"
        subtitle="Students currently on leave or overdue"
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
        <KPICard
          label="Currently Out"
          value={departed.length}
          delta={`${departed.length} students`}
          deltaDir="down"
        />
        <KPICard
          label="Overdue"
          value={overdue.length}
          delta={overdue.length > 0 ? '⚠ Action needed' : '—'}
          deltaDir={overdue.length > 0 ? 'down' : 'up'}
        />
        <KPICard
          label="Returned Today"
          value={returned.length}
          delta={`${returned.length} checked in`}
          deltaDir="up"
        />
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading queue...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Overdue Section */}
          {overdue.length > 0 && (
            <div className="bg-white border border-[#9C3B2E] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#9C3B2E] font-['IBM_Plex_Sans'] mb-4 flex items-center gap-2">
                <AlertTriangle size={14} /> Overdue Returns ({overdue.length})
              </p>
              <div className="space-y-3">
                {overdue.map((entry) => (
                  <QueueCard
                    key={entry.id}
                    entry={entry}
                    isMarking={markingReturned === entry.student_id}
                    onMarkReturned={handleMarkReturned}
                    variant="overdue"
                  />
                ))}
              </div>
            </div>
          )}

          {/* Current Out Section */}
          {departed.length > 0 && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
                Currently Out ({departed.length})
              </p>
              <div className="space-y-3">
                {departed.map((entry) => (
                  <QueueCard
                    key={entry.id}
                    entry={entry}
                    isMarking={markingReturned === entry.student_id}
                    onMarkReturned={handleMarkReturned}
                    variant="normal"
                  />
                ))}
              </div>
            </div>
          )}

          {queue.length === 0 && (
            <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-8 text-center">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">
                ✓ All students accounted for
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Queue Card Component ──────────────────────────────────────────────────

function QueueCard({
  entry,
  isMarking,
  onMarkReturned,
  variant,
}: {
  entry: ExeatQueueEntry;
  isMarking: boolean;
  onMarkReturned: (studentId: string) => void;
  variant: 'normal' | 'overdue';
}) {
  return (
    <div
      className={`p-4 border rounded-sm flex items-start justify-between ${
        variant === 'overdue'
          ? 'border-[#9C3B2E] bg-[#FEF8F5]'
          : 'border-[#DCD6C4] bg-white hover:bg-[#F3EFE4]'
      }`}
    >
      <div className="flex-1">
        <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans']">
          {entry.student_name}
        </p>
        <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">
          {entry.class} · Stream {entry.stream}
        </p>
        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
          <div>
            <p className="text-[10px] text-[#7A8078] uppercase tracking-wide font-['IBM_Plex_Sans']">
              Left
            </p>
            <p className="font-['IBM_Plex_Mono'] text-[#16241D]">
              {formatDate(entry.departure_time)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-[#7A8078] uppercase tracking-wide font-['IBM_Plex_Sans']">
              Due Back
            </p>
            <p className={`font-['IBM_Plex_Mono'] ${variant === 'overdue' ? 'text-[#9C3B2E] font-semibold' : 'text-[#16241D]'}`}>
              {formatDate(entry.expected_return_time)}
            </p>
          </div>
        </div>
        {entry.remarks && (
          <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-2 italic">
            {entry.remarks}
          </p>
        )}
      </div>

      <button
        onClick={() => onMarkReturned(entry.student_id)}
        disabled={isMarking}
        className="ml-4 px-3 py-2 bg-[#1F6F4A] text-white rounded-sm text-xs font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 transition-colors whitespace-nowrap flex items-center gap-1"
      >
        {isMarking ? (
          <>
            <span className="animate-spin">↻</span>
            Marking...
          </>
        ) : (
          '✓ Mark Returned'
        )}
      </button>
    </div>
  );
}

// ─── KPI Card Component ────────────────────────────────────────────────────

function KPICard({
  label,
  value,
  delta,
  deltaDir,
}: {
  label: string;
  value: number | string;
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

// ─── Page Header Component ────────────────────────────────────────────────

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
