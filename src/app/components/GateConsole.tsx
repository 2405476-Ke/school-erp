/**
 * GateConsole Component
 *
 * Gate Security module for:
 * - Visitor check-in and log
 * - Student entry/exit scanning (blockable on rules violation)
 * - Real-time alerts for unauthorized access
 */

import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { apiPost, tokenManager } from '@/services/api';
import { getErrorMessage } from '@/types/api';
import type { VisitorCheckInPayload, StudentScanPayload, StudentScanResponse } from '@/types/api';

// ─── Visitor Check-in Form State ──────────────────────────────────────────

interface VisitorFormState {
  visitorName: string;
  visitorPhone: string;
  purpose: string;
  studentName: string;
  expectedDurationMinutes: string;
}

// ─── Student Scan State ───────────────────────────────────────────────────

interface ScanState {
  studentId: string;
  action: 'ENTRY' | 'EXIT';
}

// ─── Main Component ───────────────────────────────────────────────────────

export function GateConsole() {
  const [visitorForm, setVisitorForm] = useState<VisitorFormState>({
    visitorName: '',
    visitorPhone: '',
    purpose: '',
    studentName: '',
    expectedDurationMinutes: '30',
  });

  const [visitorLoading, setVisitorLoading] = useState(false);
  const [visitorSuccess, setVisitorSuccess] = useState(false);
  const [visitorSuccessData, setVisitorSuccessData] = useState<any>(null);
  const [visitorError, setVisitorError] = useState<string | null>(null);

  const [scanForm, setScanForm] = useState<ScanState>({
    studentId: '',
    action: 'ENTRY',
  });

  const [scanLoading, setScanLoading] = useState(false);
  const [scanResult, setScanResult] = useState<StudentScanResponse | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);

  // ─── Visitor Check-in Handler ─────────────────────────────────────────

  const handleVisitorCheckIn = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!visitorForm.visitorName || !visitorForm.visitorPhone || !visitorForm.purpose || !visitorForm.studentName) {
      setVisitorError('Please fill in all required fields');
      return;
    }

    if (!/^\+?[\d\s\-()]{10,}$/.test(visitorForm.visitorPhone)) {
      setVisitorError('Please enter a valid phone number');
      return;
    }

    try {
      setVisitorLoading(true);
      setVisitorError(null);

      const schoolId = tokenManager.getSchoolId();
      if (!schoolId) {
        throw new Error('School ID not found. Please log in again.');
      }

      const payload: VisitorCheckInPayload = {
        visitor_name: visitorForm.visitorName,
        visitor_phone: visitorForm.visitorPhone,
        purpose: visitorForm.purpose,
        student_name: visitorForm.studentName,
        expected_duration_minutes: parseInt(visitorForm.expectedDurationMinutes, 10) || 30,
      };

      const result = await apiPost('/security/gate/visitor/check-in', payload);

      setVisitorSuccessData(result);
      setVisitorSuccess(true);

      // Reset form
      setTimeout(() => {
        setVisitorForm({
          visitorName: '',
          visitorPhone: '',
          purpose: '',
          studentName: '',
          expectedDurationMinutes: '30',
        });
        setVisitorSuccess(false);
      }, 3000);
    } catch (err) {
      const errorMessage = (err && typeof err === 'object' && 'response' in err)
        ? getErrorMessage((err as any).response?.data)
        : err instanceof Error
        ? err.message
        : 'Failed to check in visitor';

      setVisitorError(errorMessage);
    } finally {
      setVisitorLoading(false);
    }
  };

  // ─── Student Scan Handler ─────────────────────────────────────────────

  const handleStudentScan = async (action: 'ENTRY' | 'EXIT') => {
    if (!scanForm.studentId.trim()) {
      setScanError('Please enter a Student ID or UPI');
      return;
    }

    try {
      setScanLoading(true);
      setScanError(null);
      setScanResult(null);

      const schoolId = tokenManager.getSchoolId();
      if (!schoolId) {
        throw new Error('School ID not found. Please log in again.');
      }

      const payload: StudentScanPayload = {
        student_id: scanForm.studentId,
        action: action,
        scan_timestamp: new Date().toISOString(),
      };

      // Call appropriate endpoint
      const endpoint = action === 'ENTRY'
        ? '/security/gate/scan-student-entry'
        : '/security/gate/scan-student-exit';

      const result = await apiPost<StudentScanResponse>(endpoint, payload);

      setScanResult(result);

      // Auto-clear on success
      if (result.status === 'ALLOWED') {
        setTimeout(() => {
          setScanForm({ ...scanForm, studentId: '' });
          setScanResult(null);
        }, 2500);
      }
    } catch (err) {
      // Check if it's a 403 Forbidden
      if ((err && typeof err === 'object' && 'response' in err) && (err as any).response?.status === 403) {
        setScanError('Access Denied: Student not permitted to leave');
      } else {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : err instanceof Error
          ? err.message
          : 'Scan failed';

        setScanError(errorMessage);
      }
    } finally {
      setScanLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Gate Verification Console"
        subtitle="Visitor check-ins and student entry/exit scanning"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* ─── Visitor Check-in Card ─────────────────────────────────── */}

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Visitor Check-in
          </p>

          {visitorSuccess && visitorSuccessData && (
            <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
              <div className="flex items-start gap-3">
                <CheckCircle size={20} className="text-[#1F6F4A] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-[#1F6F4A] font-['IBM_Plex_Sans']">
                    Visitor checked in successfully
                  </p>
                  <p className="text-sm text-[#1F6F4A] mt-1 font-['IBM_Plex_Mono']">
                    Reference: {visitorSuccessData.check_in_reference || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {visitorError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <div className="flex items-start gap-3">
                <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-[#9C3B2E] font-['IBM_Plex_Sans']">
                    Check-in failed
                  </p>
                  <p className="text-sm text-[#9C3B2E] mt-1 font-['IBM_Plex_Sans']">
                    {visitorError}
                  </p>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleVisitorCheckIn} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Visitor Name *
              </label>
              <input
                type="text"
                value={visitorForm.visitorName}
                onChange={(e) => setVisitorForm({ ...visitorForm, visitorName: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Full name"
                disabled={visitorLoading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Phone Number *
              </label>
              <input
                type="tel"
                value={visitorForm.visitorPhone}
                onChange={(e) => setVisitorForm({ ...visitorForm, visitorPhone: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Phone number"
                disabled={visitorLoading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Student Name (Visiting) *
              </label>
              <input
                type="text"
                value={visitorForm.studentName}
                onChange={(e) => setVisitorForm({ ...visitorForm, studentName: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Student name or Form/Stream"
                disabled={visitorLoading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Purpose of Visit *
              </label>
              <select
                value={visitorForm.purpose}
                onChange={(e) => setVisitorForm({ ...visitorForm, purpose: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                disabled={visitorLoading}
              >
                <option value="">Select purpose...</option>
                <option value="PARENT_VISIT">Parent Visit</option>
                <option value="GUARDIAN_VISIT">Guardian Visit</option>
                <option value="DELIVERY">Package Delivery</option>
                <option value="MAINTENANCE">Maintenance/Repair</option>
                <option value="OFFICIAL">Official Business</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Expected Duration (minutes)
              </label>
              <input
                type="number"
                value={visitorForm.expectedDurationMinutes}
                onChange={(e) => setVisitorForm({ ...visitorForm, expectedDurationMinutes: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="30"
                min="5"
                max="480"
                disabled={visitorLoading}
              />
            </div>

            <button
              type="submit"
              disabled={visitorLoading}
              className="w-full bg-[#1F6F4A] text-white px-4 py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {visitorLoading ? (
                <>
                  <span className="animate-spin">↻</span>
                  Checking in...
                </>
              ) : (
                'Check In Visitor'
              )}
            </button>
          </form>
        </div>

        {/* ─── Student Scanner Card ──────────────────────────────────── */}

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Student Entry/Exit Scanner
          </p>

          {scanResult && (
            <div
              className={`rounded-sm p-4 mb-4 border flex items-start gap-3 ${
                scanResult.status === 'ALLOWED'
                  ? 'bg-[#E7F0EA] border-[#1F6F4A]'
                  : 'bg-[#F7E6E2] border-[#9C3B2E]'
              }`}
            >
              {scanResult.status === 'ALLOWED' ? (
                <CheckCircle
                  size={20}
                  className="text-[#1F6F4A] flex-shrink-0 mt-0.5"
                />
              ) : (
                <XCircle
                  size={20}
                  className="text-[#9C3B2E] flex-shrink-0 mt-0.5"
                />
              )}
              <div>
                <p
                  className={`font-semibold font-['IBM_Plex_Sans'] ${
                    scanResult.status === 'ALLOWED'
                      ? 'text-[#1F6F4A]'
                      : 'text-[#9C3B2E]'
                  }`}
                >
                  {scanResult.student_name}
                </p>
                <p
                  className={`text-sm mt-1 font-['IBM_Plex_Sans'] ${
                    scanResult.status === 'ALLOWED'
                      ? 'text-[#1F6F4A]'
                      : 'text-[#9C3B2E]'
                  }`}
                >
                  {scanResult.action === 'ENTRY' ? '✓ Entry allowed' : '✓ Exit allowed'}
                </p>
              </div>
            </div>
          )}

          {scanError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <div className="flex items-start gap-3">
                <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-[#9C3B2E] font-['IBM_Plex_Sans']">
                    Access Denied
                  </p>
                  <p className="text-sm text-[#9C3B2E] mt-1 font-['IBM_Plex_Sans']">
                    {scanError}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Student ID / UPI *
              </label>
              <input
                type="text"
                value={scanForm.studentId}
                onChange={(e) => {
                  setScanForm({ ...scanForm, studentId: e.target.value });
                  setScanError(null);
                  setScanResult(null);
                }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleStudentScan(scanForm.action);
                  }
                }}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Mono'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Scan or type Student ID..."
                disabled={scanLoading}
                autoFocus
              />
              <p className="text-[10px] text-[#7A8078] mt-1 font-['IBM_Plex_Sans']">
                Press Enter to scan, or click button below
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-2 font-['IBM_Plex_Sans']">
                Action
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => handleStudentScan('ENTRY')}
                  disabled={scanLoading}
                  className={`flex-1 px-3 py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] transition-colors flex items-center justify-center gap-2 ${
                    scanForm.action === 'ENTRY'
                      ? 'bg-[#1F6F4A] text-white hover:bg-[#185f3e] disabled:opacity-50'
                      : 'bg-[#EBE7DC] text-[#16241D] hover:bg-[#DCD6C4] disabled:opacity-50'
                  }`}
                >
                  {scanLoading && scanForm.action === 'ENTRY' ? (
                    <>
                      <span className="animate-spin">↻</span>
                      Scanning...
                    </>
                  ) : (
                    '↪ Entry'
                  )}
                </button>
                <button
                  onClick={() => handleStudentScan('EXIT')}
                  disabled={scanLoading}
                  className={`flex-1 px-3 py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] transition-colors flex items-center justify-center gap-2 ${
                    scanForm.action === 'EXIT'
                      ? 'bg-[#9C3B2E] text-white hover:bg-[#7a2c23] disabled:opacity-50'
                      : 'bg-[#EBE7DC] text-[#16241D] hover:bg-[#DCD6C4] disabled:opacity-50'
                  }`}
                >
                  {scanLoading && scanForm.action === 'EXIT' ? (
                    <>
                      <span className="animate-spin">↻</span>
                      Scanning...
                    </>
                  ) : (
                    '↪ Exit'
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-4 bg-[#F3EFE4] border border-[#DCD6C4] rounded-sm p-3">
            <p className="text-[10px] font-['IBM_Plex_Sans'] text-[#7A8078]">
              <Clock size={12} className="inline mr-1" />
              Last scan: Today · 14:35 UTC
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Reusable Components ────────────────────────────────────────────────────

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
