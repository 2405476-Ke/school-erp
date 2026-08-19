/**
 * LeavePassApproval Component
 *
 * Manage student leave pass (exeat) approvals:
 * - Display pending leave pass requests
 * - Approve/reject with optional notes
 * - Track status and dates
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { apiGet, apiPost, tokenManager } from '@/services/api';
import { formatDate } from '@/services/formatting';
import { getErrorMessage } from '@/types/api';
import type { LeavePassRecord, LeavePassApprovalPayload } from '@/types/api';

interface ApprovalState {
  leavePassId: string;
  action: 'APPROVE' | 'REJECT';
  notes: string;
}

export function LeavePassApproval() {
  const [leaves, setLeaves] = useState<LeavePassRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedLeave, setSelectedLeave] = useState<LeavePassRecord | null>(null);
  const [approval, setApproval] = useState<ApprovalState>({
    leavePassId: '',
    action: 'APPROVE',
    notes: '',
  });
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [approvalSuccess, setApprovalSuccess] = useState(false);

  // Fetch leave passes
  useEffect(() => {
    const fetchLeaves = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<LeavePassRecord[]>('/boarding/leave-passes');
        // Filter only REQUESTED status
        const requested = (result || []).filter(l => l.status === 'REQUESTED');
        setLeaves(requested);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load leave pass requests';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchLeaves();
  }, []);

  // Handle approval submission
  const handleApprovalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedLeave) {
      setApprovalError('Please select a leave pass');
      return;
    }

    try {
      setApprovalLoading(true);
      setApprovalError(null);

      const payload: LeavePassApprovalPayload = {
        leave_pass_id: selectedLeave.id,
        action: approval.action,
        notes: approval.notes || undefined,
      };

      await apiPost('/boarding/leave-passes/approve', payload);

      setApprovalSuccess(true);
      setLeaves(leaves.filter(l => l.id !== selectedLeave.id));
      setSelectedLeave(null);
      setApproval({ leavePassId: '', action: 'APPROVE', notes: '' });

      setTimeout(() => setApprovalSuccess(false), 3000);
    } catch (err) {
      const errorMessage = (err && typeof err === 'object' && 'response' in err)
        ? getErrorMessage((err as any).response?.data)
        : 'Failed to process approval';
      setApprovalError(errorMessage);
    } finally {
      setApprovalLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Leave Pass Approval"
        subtitle="Review and approve student exeat requests"
      />

      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
            <p className="text-sm text-[#9C3B2E] font-['IBM_Plex_Sans']">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Leave Requests List */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Pending Requests ({leaves.length})
            </p>

            {loading ? (
              <div className="text-center py-8">
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading...</p>
              </div>
            ) : leaves.length === 0 ? (
              <div className="text-center py-8 bg-[#F3EFE4] rounded-sm">
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
                  No pending leave pass requests
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {leaves.map((leave) => (
                  <div
                    key={leave.id}
                    onClick={() => setSelectedLeave(leave)}
                    className={`p-4 border rounded-sm cursor-pointer transition-colors ${
                      selectedLeave?.id === leave.id
                        ? 'border-[#1F6F4A] bg-[#E7F0EA]'
                        : 'border-[#DCD6C4] bg-white hover:bg-[#F3EFE4]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans']">
                          {leave.student_name}
                        </p>
                        <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">
                          {leave.exeat_type} · {formatDate(leave.requested_date)}
                        </p>
                        <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">
                          Return: {formatDate(leave.expected_return_time)}
                        </p>
                      </div>
                      <StatusTag
                        variant="warn"
                        label="Pending"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Approval Form */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Approval Action
          </p>

          {approvalSuccess && (
            <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-3 mb-4">
              <div className="flex items-start gap-2">
                <CheckCircle size={18} className="text-[#1F6F4A] flex-shrink-0 mt-0.5" />
                <p className="text-xs text-[#1F6F4A] font-['IBM_Plex_Sans']">
                  Leave pass processed successfully
                </p>
              </div>
            </div>
          )}

          {approvalError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-3 mb-4">
              <div className="flex items-start gap-2">
                <XCircle size={18} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
                <p className="text-xs text-[#9C3B2E] font-['IBM_Plex_Sans']">
                  {approvalError}
                </p>
              </div>
            </div>
          )}

          {selectedLeave ? (
            <form onSubmit={handleApprovalSubmit} className="space-y-4">
              <div className="bg-[#F3EFE4] border border-[#DCD6C4] rounded-sm p-3">
                <p className="text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-2 font-['IBM_Plex_Sans']">
                  Selected Student
                </p>
                <p className="font-['IBM_Plex_Sans'] text-sm text-[#16241D]">
                  {selectedLeave.student_name}
                </p>
                <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">
                  Reason: {selectedLeave.reason}
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-2 font-['IBM_Plex_Sans']">
                  Action
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setApproval({ ...approval, action: 'APPROVE' })}
                    className={`flex-1 px-3 py-2 rounded-sm text-xs font-semibold font-['IBM_Plex_Sans'] transition-colors ${
                      approval.action === 'APPROVE'
                        ? 'bg-[#1F6F4A] text-white'
                        : 'bg-[#EBE7DC] text-[#16241D] hover:bg-[#DCD6C4]'
                    }`}
                  >
                    ✓ Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => setApproval({ ...approval, action: 'REJECT' })}
                    className={`flex-1 px-3 py-2 rounded-sm text-xs font-semibold font-['IBM_Plex_Sans'] transition-colors ${
                      approval.action === 'REJECT'
                        ? 'bg-[#9C3B2E] text-white'
                        : 'bg-[#EBE7DC] text-[#16241D] hover:bg-[#DCD6C4]'
                    }`}
                  >
                    ✗ Reject
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Notes (Optional)
                </label>
                <textarea
                  value={approval.notes}
                  onChange={(e) => setApproval({ ...approval, notes: e.target.value })}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="Add approval notes..."
                  rows={3}
                  disabled={approvalLoading}
                />
              </div>

              <button
                type="submit"
                disabled={approvalLoading}
                className="w-full bg-[#1F6F4A] text-white px-4 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
              >
                {approvalLoading ? (
                  <>
                    <span className="animate-spin">↻</span>
                    Processing...
                  </>
                ) : (
                  'Submit Decision'
                )}
              </button>
            </form>
          ) : (
            <div className="text-center py-8">
              <Clock size={24} className="mx-auto text-[#7A8078] mb-2" />
              <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
                Select a request to approve or reject
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Reusable Components ────────────────────────────────────────────────────

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
