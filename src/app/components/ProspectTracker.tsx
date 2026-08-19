/**
 * ProspectTracker Component
 *
 * Displays list of prospective students with:
 * - Data fetched from GET /admissions/prospects
 * - Data transformations applied (Section 3.1-3.4 of Gap Analysis)
 * - Loading states
 * - Search & filter UI
 */

import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, X } from 'lucide-react';
import { apiGet, tokenManager } from '@/services/api';
import type { StudentProspect, ProspectStatus } from '@/types/api';
import { formatDate, formatStudentName, formatClassStream, prospectStatusToVariant } from '@/services/formatting';

interface ProspectTrackerProps {
  onNavigate: (page: string) => void;
}

export function ProspectTracker({ onNavigate }: ProspectTrackerProps) {
  const [prospects, setProspects] = useState<StudentProspect[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({ name: '', contact: '', relationship: '', appliedFor: 'FORM_1_A' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ─── Fetch prospects on component mount ────────────────────────────────

  useEffect(() => {
    const fetchProspects = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const schoolId = tokenManager.getSchoolId();
        if (!schoolId) {
          throw new Error('School ID not found. Please log in again.');
        }

        const data = await apiGet<StudentProspect[]>(
          `/admissions/prospects?school_id=${schoolId}`
        );

        setProspects(data || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load prospects';
        setError(errorMessage);
        console.error('Error fetching prospects:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProspects();
  }, []);

  // ─── Transform and filter prospects for display ─────────────────────────

  const filteredProspects = prospects.filter(p => {
    const displayName = formatStudentName(p.first_name, p.last_name);
    return displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
           p.guardian_phone.includes(searchTerm);
  });

  // ─── Build table rows with transformations ────────────────────────────

  const rows = filteredProspects.map(p => [
    // Transformation 3.1: Combine first_name + last_name
    formatStudentName(p.first_name, p.last_name),
    // Transformation 3.4: Format phone
    p.guardian_phone,
    // Transformation 3.5: Format class + stream
    formatClassStream(p.applied_class, p.applied_stream),
    // Transformation 3.2: Map status enum to variant
    p.prospect_status,
    // Transformation 3.4: Format date
    formatDate(p.created_at),
  ]);

  // ─── Render ──────────────────────────────────────────────────────────

  return (
    <div>
      <Breadcrumbs items={[{ label: "Admissions" }, { label: "Prospects" }]} />
      <PageHeader
        title="Prospect Tracker"
        subtitle="Manage prospective students through the admissions pipeline"
      />

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
            <Search size={13} className="text-[#7A8078]" />
            <input
              className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48"
              placeholder="Search prospects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-1.5 border border-[#DCD6C4] rounded-sm px-3 py-1.5 text-sm text-[#7A8078] hover:bg-[#F3EFE4] transition-colors font-['IBM_Plex_Sans']">
            <Filter size={12} /> Filter
          </button>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] focus:ring-offset-2"
        >
          <Plus size={14} /> Add Prospect
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
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
              Loading prospects...
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
            ⚠️ {error}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && prospects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
            No prospects found. Click "Add Prospect" to get started.
          </p>
        </div>
      )}

      {/* Data Table */}
      {!isLoading && prospects.length > 0 && (
        <ProspectTable
          prospects={filteredProspects}
          onRowClick={() => onNavigate('student-profile')}
        />
      )}

      {/* Add Prospect Sidebar */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-[#16241D]/40"
            onClick={() => setShowForm(false)}
          />
          <div className="relative w-[400px] h-full bg-white shadow-xl flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#DCD6C4]">
              <h2 className="font-['Fraunces'] text-lg font-medium text-[#16241D]">
                Add Prospect
              </h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-[#7A8078] hover:text-[#16241D]"
              >
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Full Name
                </label>
                <input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Student full name"
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Guardian Contact
                </label>
                <input
                  value={formData.contact}
                  onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                  placeholder="Phone or email"
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Relationship
                </label>
                <input
                  value={formData.relationship}
                  onChange={(e) => setFormData({ ...formData, relationship: e.target.value })}
                  placeholder="e.g. Father, Mother"
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                  Applied For
                </label>
                <select
                  value={formData.appliedFor}
                  onChange={(e) => setFormData({ ...formData, appliedFor: e.target.value })}
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                >
                  <option value="FORM_1_A">Form 1 · Stream A</option>
                  <option value="FORM_1_B">Form 1 · Stream B</option>
                  <option value="FORM_1_C">Form 1 · Stream C</option>
                  <option value="FORM_2_A">Form 2 · Stream A</option>
                  <option value="FORM_2_B">Form 2 · Stream B</option>
                  <option value="FORM_2_C">Form 2 · Stream C</option>
                </select>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-[#DCD6C4]">
              <button
                onClick={async () => {
                  if (!formData.name || !formData.contact) {
                    alert('Please fill in all required fields');
                    return;
                  }
                  setIsSubmitting(true);
                  try {
                    const [firstName, ...lastNameParts] = formData.name.split(' ');
                    const newProspect: StudentProspect = {
                      id: Math.random().toString(),
                      first_name: firstName,
                      last_name: lastNameParts.join(' ') || 'Unknown',
                      guardian_phone: formData.contact,
                      applied_class: (formData.appliedFor.split('_')[0] + '_' + formData.appliedFor.split('_')[1]) as any,
                      applied_stream: formData.appliedFor.split('_')[2] || 'A',
                      prospect_status: 'ENQUIRY',
                      created_at: new Date().toISOString(),
                    };
                    setProspects([newProspect, ...prospects]);
                    setFormData({ name: '', contact: '', relationship: '', appliedFor: 'FORM_1_A' });
                    setShowForm(false);
                  } finally {
                    setIsSubmitting(false);
                  }
                }}
                disabled={isSubmitting}
                className="w-full bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : 'Save Prospect'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── ProspectTable Component ───────────────────────────────────────────────

interface ProspectTableProps {
  prospects: StudentProspect[];
  onRowClick: () => void;
}

function ProspectTable({ prospects, onRowClick }: ProspectTableProps) {
  return (
    <div className="border border-[#DCD6C4] rounded-sm overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-[#F3EFE4] border-b border-[#DCD6C4]">
            {['Name', 'Guardian Contact', 'Applied For', 'Stage', 'Date Added'].map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-left text-xs font-semibold text-[#7A8078] uppercase tracking-wide font-['IBM_Plex_Sans']"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {prospects.map((prospect, idx) => (
            <tr
              key={prospect.id}
              onClick={onRowClick}
              className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] cursor-pointer transition-colors"
            >
              <td className="px-4 py-3 text-sm font-['IBM_Plex_Sans'] text-[#16241D]">
                {formatStudentName(prospect.first_name, prospect.last_name)}
              </td>
              <td className="px-4 py-3 text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
                {prospect.guardian_phone}
              </td>
              <td className="px-4 py-3 text-sm font-['IBM_Plex_Sans'] text-[#16241D]">
                {formatClassStream(prospect.applied_class, prospect.applied_stream)}
              </td>
              <td className="px-4 py-3">
                <ProspectStatusTag status={prospect.prospect_status} />
              </td>
              <td className="px-4 py-3 text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
                {formatDate(prospect.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Status Tag Component ──────────────────────────────────────────────────

interface ProspectStatusTagProps {
  status: ProspectStatus;
}

const STATUS_LABELS: Record<ProspectStatus, string> = {
  CLEARED: 'Cleared',
  INTERVIEW: 'Interview',
  DOCUMENTS_PENDING: 'Documents Pending',
  OFFER_SENT: 'Offer Sent',
  ENQUIRY: 'Enquiry',
};

function ProspectStatusTag({ status }: ProspectStatusTagProps) {
  const variant = prospectStatusToVariant(status);
  const styles: Record<string, string> = {
    ok: 'bg-[#E7F0EA] text-[#1F6F4A]',
    warn: 'bg-[#F5EAD6] text-[#B5751F]',
    bad: 'bg-[#F7E6E2] text-[#9C3B2E]',
    neutral: 'bg-[#EBE7DC] text-[#7A8078]',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold font-['IBM_Plex_Sans'] ${styles[variant]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

// ─── Placeholder Components ────────────────────────────────────────────────

function Breadcrumbs({ items }: { items: { label: string; onClick?: () => void }[] }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-2">
          {i > 0 && <span className="text-[#DCD6C4]">›</span>}
          {item.onClick ? (
            <button onClick={item.onClick} className="text-[12px] text-[#1F6F4A] hover:text-[#0d5135] font-['IBM_Plex_Sans'] font-medium transition-colors">
              {item.label}
            </button>
          ) : (
            <span className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">{item.label}</span>
          )}
        </div>
      ))}
    </div>
  );
}

function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-3xl font-bold font-['Playfair Display'] text-[#16241D] mb-1">
        {title}
      </h1>
      <p className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">{subtitle}</p>
    </div>
  );
}
