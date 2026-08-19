/**
 * StockIssuance Component
 *
 * Issue inventory items to departments:
 * - Select items from inventory
 * - Specify quantities and departments
 * - Track stock balances
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { apiGet, apiPost } from '@/services/api';
import { formatDate } from '@/services/formatting';
import { getErrorMessage } from '@/types/api';
import type { StockItem, StockIssuePayload, StockIssueResponse } from '@/types/api';

interface IssueForm {
  itemId: string;
  quantityIssued: string;
  issuedTo: string;
  department: string;
  purpose: string;
}

export function StockIssuance() {
  const [items, setItems] = useState<StockItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<IssueForm>({
    itemId: '',
    quantityIssued: '',
    issuedTo: '',
    department: '',
    purpose: '',
  });

  const [issueLoading, setIssueLoading] = useState(false);
  const [issueError, setIssueError] = useState<string | null>(null);
  const [issueSuccess, setIssueSuccess] = useState(false);
  const [issuedData, setIssuedData] = useState<StockIssueResponse | null>(null);

  // Fetch stock items
  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiGet<StockItem[]>('/inventory/stock-items');
        setItems(result || []);
      } catch (err) {
        const errorMessage = (err && typeof err === 'object' && 'response' in err)
          ? getErrorMessage((err as any).response?.data)
          : 'Failed to load stock items';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, []);

  // Handle issue submission
  const handleIssue = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.itemId || !form.quantityIssued || !form.issuedTo || !form.department || !form.purpose) {
      setIssueError('Please fill in all required fields');
      return;
    }

    const quantity = parseInt(form.quantityIssued, 10);
    if (isNaN(quantity) || quantity <= 0) {
      setIssueError('Quantity must be a positive number');
      return;
    }

    const selectedItem = items.find(i => i.id === form.itemId);
    if (!selectedItem || quantity > selectedItem.current_quantity) {
      setIssueError(`Insufficient stock. Available: ${selectedItem?.current_quantity || 0}`);
      return;
    }

    try {
      setIssueLoading(true);
      setIssueError(null);

      const payload: StockIssuePayload = {
        item_id: form.itemId,
        quantity_issued: quantity,
        issued_to: form.issuedTo,
        department: form.department,
        purpose: form.purpose,
        issue_date: new Date().toISOString().split('T')[0],
      };

      const result = await apiPost<StockIssueResponse>('/inventory/stock-issue', payload);
      setIssuedData(result);
      setIssueSuccess(true);

      // Reset form
      setForm({
        itemId: '',
        quantityIssued: '',
        issuedTo: '',
        department: '',
        purpose: '',
      });

      // Refetch items to update stock
      const updatedItems = await apiGet<StockItem[]>('/inventory/stock-items');
      setItems(updatedItems || []);

      setTimeout(() => setIssueSuccess(false), 3000);
    } catch (err) {
      const errorMessage = (err && typeof err === 'object' && 'response' in err)
        ? getErrorMessage((err as any).response?.data)
        : 'Failed to issue stock';
      setIssueError(errorMessage);
    } finally {
      setIssueLoading(false);
    }
  };

  const selectedItem = items.find(i => i.id === form.itemId);
  const lowStockItems = items.filter(i => i.current_quantity <= i.reorder_level);

  return (
    <div>
      <PageHeader
        title="Stock Issuance"
        subtitle="Issue inventory items to departments"
      />

      {error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <div className="flex items-start gap-3">
            <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
            <p className="text-sm text-[#9C3B2E] font-['IBM_Plex_Sans']">{error}</p>
          </div>
        </div>
      )}

      {/* Stock Alerts */}
      {lowStockItems.length > 0 && (
        <div className="bg-[#F5EAD6] border border-[#B5751F] rounded-sm p-4 mb-4">
          <p className="text-sm font-semibold text-[#B5751F] font-['IBM_Plex_Sans']">
            ⚠ {lowStockItems.length} item(s) below reorder level
          </p>
          <p className="text-xs text-[#B5751F] font-['IBM_Plex_Sans'] mt-1">
            {lowStockItems.map(i => i.item_name).join(', ')}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Issue Form */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Issue Stock
          </p>

          {issueSuccess && issuedData && (
            <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
              <div className="flex items-start gap-3">
                <CheckCircle size={20} className="text-[#1F6F4A] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-[#1F6F4A] font-['IBM_Plex_Sans']">
                    Stock issued successfully
                  </p>
                  <p className="text-xs text-[#1F6F4A] font-['IBM_Plex_Mono'] mt-1">
                    Ref: {issuedData.issue_reference}
                  </p>
                </div>
              </div>
            </div>
          )}

          {issueError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <div className="flex items-start gap-3">
                <XCircle size={20} className="text-[#9C3B2E] flex-shrink-0 mt-0.5" />
                <p className="text-sm text-[#9C3B2E] font-['IBM_Plex_Sans']">{issueError}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleIssue} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Item *
              </label>
              <select
                value={form.itemId}
                onChange={(e) => setForm({ ...form, itemId: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                disabled={issueLoading}
              >
                <option value="">Select item...</option>
                {items.map(item => (
                  <option key={item.id} value={item.id}>
                    {item.item_name} ({item.current_quantity} {item.unit})
                  </option>
                ))}
              </select>
            </div>

            {selectedItem && (
              <div className="bg-[#F3EFE4] border border-[#DCD6C4] rounded-sm p-3">
                <p className="text-xs font-['IBM_Plex_Sans'] text-[#7A8078]">
                  Available: <span className="font-semibold text-[#16241D]">{selectedItem.current_quantity} {selectedItem.unit}</span>
                </p>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Quantity to Issue *
              </label>
              <input
                type="number"
                value={form.quantityIssued}
                onChange={(e) => setForm({ ...form, quantityIssued: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="0"
                min="1"
                disabled={issueLoading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Issued To *
              </label>
              <input
                type="text"
                value={form.issuedTo}
                onChange={(e) => setForm({ ...form, issuedTo: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Person or staff name"
                disabled={issueLoading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Department *
              </label>
              <select
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                disabled={issueLoading}
              >
                <option value="">Select department...</option>
                <option value="ACADEMICS">Academics</option>
                <option value="ADMIN">Admin</option>
                <option value="HEALTH">Health Center</option>
                <option value="BOARDING">Boarding</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="KITCHEN">Kitchen</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">
                Purpose of Issue *
              </label>
              <textarea
                value={form.purpose}
                onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-xs font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                placeholder="Reason for issue..."
                rows={3}
                disabled={issueLoading}
              />
            </div>

            <button
              type="submit"
              disabled={issueLoading}
              className="w-full bg-[#1F6F4A] text-white px-4 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {issueLoading ? (
                <>
                  <span className="animate-spin">↻</span>
                  Processing...
                </>
              ) : (
                'Issue Stock'
              )}
            </button>
          </form>
        </div>

        {/* Stock Inventory List */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            Inventory Status ({items.length})
          </p>

          {loading ? (
            <div className="text-center py-8">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading inventory...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 bg-[#F3EFE4] rounded-sm">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">No items in inventory</p>
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((item) => {
                const isLow = item.current_quantity <= item.reorder_level;
                return (
                  <div
                    key={item.id}
                    className={`p-3 border rounded-sm ${isLow ? 'border-[#B5751F] bg-[#FEF9F0]' : 'border-[#DCD6C4] hover:bg-[#F3EFE4]'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-semibold text-[#16241D] font-['IBM_Plex_Sans'] text-sm">
                          {item.item_name}
                        </p>
                        <p className="text-xs text-[#7A8078] font-['IBM_Plex_Mono'] mt-1">
                          {item.current_quantity} {item.unit} (Reorder: {item.reorder_level} {item.unit})
                        </p>
                      </div>
                      <StatusTag
                        variant={isLow ? 'warn' : 'ok'}
                        label={isLow ? 'Low' : 'OK'}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
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
