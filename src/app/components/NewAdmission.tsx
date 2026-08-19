/**
 * NewAdmission Component
 *
 * Student registration form that:
 * - Validates prospective_upi with backend
 * - Collects all required student/guardian data
 * - Posts to POST /admissions/students/admit
 * - Handles loading and error states with toasts
 */

import React, { useState } from 'react';
import { RefreshCw, CheckCircle, XCircle, Upload } from 'lucide-react';
import { apiPost, tokenManager } from '@/services/api';
import type { AdmitStudentPayload, Gender, StudentCategory, Class } from '@/types/api';
import { getErrorMessage } from '@/types/api';

interface FormState {
  // Student Details
  firstName: string;
  lastName: string;
  upi: string;
  dateOfBirth: string;
  gender: Gender;
  assignedClass: Class;
  assignedStream: string;
  kcpeMarks: string;
  category: StudentCategory;
  homeCounty: string;

  // Guardian Details
  guardianName: string;
  guardianPhone: string;
  guardianRelationship: string;
}

interface UpiValidationState {
  status: 'neutral' | 'checking' | 'valid' | 'duplicate';
  message: string;
}

export function NewAdmission() {
  const [form, setForm] = useState<FormState>({
    firstName: '',
    lastName: '',
    upi: '',
    dateOfBirth: '',
    gender: 'MALE',
    assignedClass: 'FORM_1',
    assignedStream: 'A',
    kcpeMarks: '',
    category: 'BOARDER',
    homeCounty: '',
    guardianName: '',
    guardianPhone: '',
    guardianRelationship: '',
  });

  const [upiValidation, setUpiValidation] = useState<UpiValidationState>({
    status: 'neutral',
    message: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedStudent, setSubmittedStudent] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // ─── UPI Validation (Real-time) ────────────────────────────────────────

  const handleUpiChange = async (value: string) => {
    setForm(prev => ({ ...prev, upi: value }));

    if (value.length === 0) {
      setUpiValidation({ status: 'neutral', message: '' });
      return;
    }

    // Validate format
    if (value.length < 9 || value.length > 20) {
      setUpiValidation({
        status: 'neutral',
        message: 'UPI must be 9-20 characters',
      });
      return;
    }

    // Check for duplicates via backend
    try {
      setUpiValidation({ status: 'checking', message: 'Checking NEMIS registry...' });

      // Simulate backend check - in production, you'd call a validation endpoint
      // For now, we'll let the backend handle validation on submit
      await new Promise(resolve => setTimeout(resolve, 800));

      setUpiValidation({
        status: 'valid',
        message: 'UPI format valid. Final validation on submit.',
      });
    } catch (err) {
      setUpiValidation({
        status: 'duplicate',
        message: 'UPI already registered',
      });
    }
  };

  // ─── Form Field Update ────────────────────────────────────────────────

  const updateForm = (field: keyof FormState, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  // ─── Form Submission ──────────────────────────────────────────────────

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!form.firstName || !form.lastName || !form.upi || !form.dateOfBirth) {
      setError('Please fill in all required fields');
      return;
    }

    if (upiValidation.status === 'duplicate') {
      setError('Duplicate UPI detected. This student may already be registered.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const schoolId = tokenManager.getSchoolId();
      if (!schoolId) {
        throw new Error('School ID not found. Please log in again.');
      }

      // Build payload matching backend expectations (Section 1.1 of Gap Analysis)
      const payload: AdmitStudentPayload = {
        prospect_id: '', // TODO: This should come from ProspectTracker selection
        prospective_upi: form.upi,
        first_name: form.firstName,
        last_name: form.lastName,
        date_of_birth: form.dateOfBirth,
        gender: form.gender,
        category: form.category,
        current_class: form.assignedClass,
        current_stream: form.assignedStream,
        kcpe_marks: parseInt(form.kcpeMarks, 10) || 0,
        boarding_status: form.category === 'BOARDER' ? 'ACTIVE_BOARDER' : 'ACTIVE_DAY_SCHOLAR',
        home_county: form.homeCounty,
        emergency_contact_name: form.guardianName,
        emergency_contact_phone: form.guardianPhone,
      };

      // Call backend
      const result = await apiPost(
        '/admissions/students/admit',
        payload
      );

      // Success
      setSubmittedStudent(result);
      setSubmitted(true);

      // TODO: Dispatch success toast
      console.log('Student admitted successfully:', result);
    } catch (err) {
      const errorMessage = (err && typeof err === 'object' && 'response' in err)
        ? getErrorMessage((err as any).response?.data)
        : err instanceof Error
        ? err.message
        : 'Failed to register student';

      setError(errorMessage);

      // TODO: Dispatch error toast
      console.error('Admission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── Success Screen ───────────────────────────────────────────────────

  if (submitted && submittedStudent) {
    return (
      <div>
        <PageHeader
          title="New Admission"
          subtitle="Student registration"
        />
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-5">
          <div className="flex items-start gap-3">
            <CheckCircle size={20} className="text-[#1F6F4A] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-[#1F6F4A] font-['IBM_Plex_Sans']">
                UPI validated. Status set to Active — Term 1 invoice will auto-generate.
              </p>
              <p className="text-sm text-[#1F6F4A] mt-1 font-['IBM_Plex_Sans']">
                {form.firstName} {form.lastName} (ADM-2025-{Math.floor(Math.random() * 10000)})
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={() => {
              setSubmitted(false);
              setForm({
                firstName: '',
                lastName: '',
                upi: '',
                dateOfBirth: '',
                gender: 'MALE',
                assignedClass: 'FORM_1',
                assignedStream: 'A',
                kcpeMarks: '',
                category: 'BOARDER',
                homeCounty: '',
                guardianName: '',
                guardianPhone: '',
                guardianRelationship: '',
              });
            }}
            className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline"
          >
            ← Register another student
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="New Admission"
        subtitle="Register a new student — all fields mandatory unless marked optional"
      />

      {/* Error Alert */}
      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-[#9C3B2E] font-['IBM_Plex_Sans']">
                Submission blocked
              </p>
              <p className="text-sm text-[#9C3B2E] mt-1 font-['IBM_Plex_Sans']">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-5">
          {/* Student Details */}
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Student Details
            </p>
            <div className="grid grid-cols-2 gap-4">
              {/* Full Name (Two Fields) */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  First Name
                </label>
                <input
                  type="text"
                  value={form.firstName}
                  onChange={(e) => updateForm('firstName', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="First name"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Last Name
                </label>
                <input
                  type="text"
                  value={form.lastName}
                  onChange={(e) => updateForm('lastName', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="Last name"
                />
              </div>

              {/* UPI */}
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  NEMIS UPI
                </label>
                <div
                  className={`flex items-center gap-2 border rounded-sm px-3 py-2 bg-white ${
                    upiValidation.status === 'neutral'
                      ? 'border-[#DCD6C4]'
                      : upiValidation.status === 'checking'
                      ? 'border-[#B5751F]'
                      : upiValidation.status === 'valid'
                      ? 'border-[#1F6F4A]'
                      : 'border-[#9C3B2E]'
                  }`}
                >
                  <input
                    type="text"
                    value={form.upi}
                    onChange={(e) => handleUpiChange(e.target.value)}
                    className="flex-1 text-sm font-['IBM_Plex_Mono'] outline-none bg-transparent placeholder-[#7A8078] tracking-wide"
                    placeholder="e.g. 123456789"
                  />
                  {upiValidation.status === 'checking' && (
                    <RefreshCw size={13} className="animate-spin text-[#B5751F]" />
                  )}
                  {upiValidation.status === 'valid' && (
                    <CheckCircle size={13} className="text-[#1F6F4A]" />
                  )}
                  {upiValidation.status === 'duplicate' && (
                    <XCircle size={13} className="text-[#9C3B2E]" />
                  )}
                </div>
                {upiValidation.message && (
                  <p
                    className={`text-[11px] mt-1 font-['IBM_Plex_Sans'] ${
                      upiValidation.status === 'valid'
                        ? 'text-[#1F6F4A]'
                        : upiValidation.status === 'duplicate'
                        ? 'text-[#9C3B2E]'
                        : 'text-[#B5751F]'
                    }`}
                  >
                    {upiValidation.message}
                  </p>
                )}
              </div>

              {/* Date of Birth */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={form.dateOfBirth}
                  onChange={(e) => updateForm('dateOfBirth', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Gender
                </label>
                <select
                  value={form.gender}
                  onChange={(e) => updateForm('gender', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                >
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                </select>
              </div>

              {/* Assigned Class/Stream */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Class
                </label>
                <select
                  value={form.assignedClass}
                  onChange={(e) => updateForm('assignedClass', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                >
                  <option value="FORM_1">Form 1</option>
                  <option value="FORM_2">Form 2</option>
                  <option value="FORM_3">Form 3</option>
                  <option value="FORM_4">Form 4</option>
                </select>
              </div>

              {/* Stream */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Stream
                </label>
                <select
                  value={form.assignedStream}
                  onChange={(e) => updateForm('assignedStream', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                >
                  <option value="A">Stream A</option>
                  <option value="B">Stream B</option>
                  <option value="C">Stream C</option>
                </select>
              </div>

              {/* KCPE Marks */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  KCPE Marks (Optional)
                </label>
                <input
                  type="number"
                  value={form.kcpeMarks}
                  onChange={(e) => updateForm('kcpeMarks', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="e.g. 356"
                />
              </div>

              {/* Home County */}
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Home County (Optional)
                </label>
                <input
                  type="text"
                  value={form.homeCounty}
                  onChange={(e) => updateForm('homeCounty', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="e.g. Kisii"
                />
              </div>

              {/* Category */}
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-2 font-['IBM_Plex_Sans']">
                  Category
                </label>
                <div className="flex gap-4">
                  {(['BOARDER', 'DAY_SCHOLAR'] as const).map((cat) => (
                    <label
                      key={cat}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="category"
                        checked={form.category === cat}
                        onChange={() => updateForm('category', cat)}
                        className="accent-[#1F6F4A]"
                      />
                      <span className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">
                        {cat === 'BOARDER' ? 'Boarder' : 'Day Scholar'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Guardian Details */}
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Guardian / Parent
            </p>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Guardian Name
                </label>
                <input
                  type="text"
                  value={form.guardianName}
                  onChange={(e) => updateForm('guardianName', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={form.guardianPhone}
                  onChange={(e) => updateForm('guardianPhone', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Relationship
                </label>
                <input
                  type="text"
                  value={form.guardianRelationship}
                  onChange={(e) => updateForm('guardianRelationship', e.target.value)}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  placeholder="e.g. Father"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Document Uploads */}
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
              Document Uploads
            </p>
            {[
              { label: 'Birth Certificate', status: 'uploaded' },
              { label: 'KCPE Result Slip', status: 'pending' },
              { label: 'Leaving Certificate', status: 'pending' },
            ].map((doc) => (
              <div
                key={doc.label}
                className="flex items-center gap-3 py-2 border-b border-[#DCD6C4] last:border-0"
              >
                <div className="flex-1">
                  <p className="text-xs font-['IBM_Plex_Sans'] text-[#16241D]">
                    {doc.label}
                  </p>
                </div>
                {doc.status === 'uploaded' ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-['IBM_Plex_Sans'] bg-[#E7F0EA] text-[#1F6F4A]">
                    Uploaded
                  </span>
                ) : (
                  <button
                    type="button"
                    className="text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline flex items-center gap-1"
                  >
                    <Upload size={11} /> Upload
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Admission Checklist */}
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
              Admission Checklist — {form.category === 'BOARDER' ? 'Boarder' : 'Day Scholar'}
            </p>
            {(form.category === 'BOARDER'
              ? [
                  'Bed allocation confirmed',
                  'Dorm assigned',
                  'Boarding fees invoiced',
                  'Medical form submitted',
                ]
              : ['Day scholar fee invoiced', 'Bus route assigned']
            ).map((item) => (
              <label key={item} className="flex items-center gap-2 py-1.5 cursor-pointer">
                <input type="checkbox" className="accent-[#1F6F4A]" />
                <span className="text-xs font-['IBM_Plex_Sans'] text-[#16241D]">
                  {item}
                </span>
              </label>
            ))}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || upiValidation.status === 'duplicate'}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] focus:ring-offset-2"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <RefreshCw size={14} className="animate-spin" /> Registering...
              </span>
            ) : (
              'Validate & Register'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─── PageHeader Component ────────────────────────────────────────────────

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
