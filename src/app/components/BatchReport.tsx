/**
 * BatchCommunicationReport Component
 *
 * View communication batch delivery reports:
 * - SMS, Email, WhatsApp delivery status
 * - Success/failure metrics
 * - Detailed recipient breakdown
 * - Retry failed messages
 */

import React, { useState, useEffect } from 'react';
import { XCircle, BarChart3 } from 'lucide-react';
import { apiGet } from '@/services/api';
import { formatDate } from '@/services/formatting';
import { getErrorMessage } from '@/types/api';
import type { BatchCommunicationReport } from '@/types/api';

interface BatchListItem {
  id: string;
  batch_type: 'SMS' | 'EMAIL' | 'WHATSAPP';
  sent_date: string;
  delivery_status: {
    total_sent: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  subject: string;
  sent_by: string;
}

export function BatchReport() {
  const [batches, setBatches] = useState<BatchListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedBatch, setSelectedBatch] = useState<BatchCommunicationReport | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);

  // Fetch batches list
  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<BatchListItem[]>('/communication/batches');
        setBatches(result || []);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load batches';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchBatches();
  }, []);

  // Fetch batch details
  const handleBatchSelect = async (batchId: string) => {
    try {
      setBatchLoading(true);
      const result = await apiGet<BatchCommunicationReport>(
        `/communication/batches/${batchId}/report`
      );
      setSelectedBatch(result);
    } catch (err) {
      const msg = (err && typeof err === 'object' && 'response' in err) ? getErrorMessage((err as any).response?.data) : 'Failed to load batch details';
      alert(msg);
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Batch Communication Report"
        subtitle="View SMS, Email, and WhatsApp delivery status"
      />

      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
            <p className="text-sm text-[#9C3B2E] font-['IBM_Plex_Sans']">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Batches List */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Batch List ({batches.length})
          </p>

          {loading ? (
            <div className="text-center py-8">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading batches...</p>
            </div>
          ) : batches.length === 0 ? (
            <div className="text-center py-8 bg-[#F3EFE4] rounded-sm">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
                No communication batches found
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {batches.map((batch) => {
                const deliveryRate = batch.delivery_status.total_sent
                  ? Math.round((batch.delivery_status.delivered / batch.delivery_status.total_sent) * 100)
                  : 0;

                return (
                  <div
                    key={batch.id}
                    onClick={() => handleBatchSelect(batch.id)}
                    className={`p-3 border rounded-sm cursor-pointer transition-colors ${
                      selectedBatch?.id === batch.id
                        ? 'border-[#1F6F4A] bg-[#E7F0EA]'
                        : 'border-[#DCD6C4] bg-white hover:bg-[#F3EFE4]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold font-['IBM_Plex_Sans'] ${
                            batch.batch_type === 'SMS' ? 'bg-[#1F6F4A] text-white' :
                            batch.batch_type === 'EMAIL' ? 'bg-[#B5751F] text-white' :
                            'bg-[#1F6F4A] text-white'
                          }`}>
                            {batch.batch_type}
                          </span>
                          <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans'] text-sm flex-1">
                            {batch.subject}
                          </p>
                        </div>
                        <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">
                          Sent by {batch.sent_by} · {formatDate(batch.sent_date)}
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <div className="flex-1 bg-[#EBE7DC] rounded-full h-1.5 overflow-hidden">
                            <div
                              className="h-1.5 bg-[#1F6F4A] rounded-full transition-all"
                              style={{ width: `${deliveryRate}%` }}
                            />
                          </div>
                          <span className="text-xs font-['IBM_Plex_Mono'] text-[#7A8078]">
                            {deliveryRate}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Batch Details */}
        {selectedBatch ? (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
                Delivery Summary
              </p>

              <div className="grid grid-cols-2 gap-3">
                <KPICard
                  label="Total Sent"
                  value={selectedBatch.delivery_status.total_sent}
                />
                <KPICard
                  label="Delivered"
                  value={selectedBatch.delivery_status.delivered}
                  delta="Success"
                  deltaDir="up"
                />
                <KPICard
                  label="Failed"
                  value={selectedBatch.delivery_status.failed}
                  delta="Needs retry"
                  deltaDir={selectedBatch.delivery_status.failed > 0 ? 'down' : 'up'}
                />
                <KPICard
                  label="Pending"
                  value={selectedBatch.delivery_status.pending}
                  delta="In progress"
                />
              </div>
            </div>

            {/* Recipients Table */}
            {selectedBatch.recipients && selectedBatch.recipients.length > 0 && (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
                <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
                  Recipients ({selectedBatch.recipients.length})
                </p>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-['IBM_Plex_Sans']">
                    <thead>
                      <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                        <th className="px-3 py-2 text-left font-semibold text-[#7A8078] uppercase tracking-wide">
                          Recipient
                        </th>
                        <th className="px-3 py-2 text-left font-semibold text-[#7A8078] uppercase tracking-wide">
                          Contact
                        </th>
                        <th className="px-3 py-2 text-left font-semibold text-[#7A8078] uppercase tracking-wide">
                          Status
                        </th>
                        <th className="px-3 py-2 text-left font-semibold text-[#7A8078] uppercase tracking-wide">
                          Time
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBatch.recipients.map((recipient, idx) => (
                        <tr key={idx} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                          <td className="px-3 py-2">
                            <p className="font-semibold text-[#16241D]">{recipient.recipient_name}</p>
                          </td>
                          <td className="px-3 py-2 font-['IBM_Plex_Mono'] text-[#7A8078]">
                            {recipient.recipient_contact}
                          </td>
                          <td className="px-3 py-2">
                            <StatusTag
                              variant={
                                recipient.delivery_status === 'DELIVERED' ? 'ok' :
                                recipient.delivery_status === 'FAILED' ? 'bad' : 'warn'
                              }
                              label={recipient.delivery_status}
                            />
                          </td>
                          <td className="px-3 py-2 font-['IBM_Plex_Mono']">
                            {formatDate(recipient.timestamp)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 flex items-center justify-center">
            <div className="text-center">
              <BarChart3 size={32} className="mx-auto text-[#7A8078] mb-2" />
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
                Select a batch to view delivery details
              </p>
            </div>
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
    <div className="bg-[#F3EFE4] border border-[#DCD6C4] rounded-sm p-3">
      <p className="text-[10px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans']">
        {label}
      </p>
      <p className="text-xl font-bold text-[#16241D] font-['Fraunces'] mt-1">
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
