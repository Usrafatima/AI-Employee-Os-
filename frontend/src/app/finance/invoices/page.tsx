'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle } from 'lucide-react';

import { financeApi, financeErrorMessage, type Invoice } from '@/lib/finance-api';
import { useFinanceSettings } from '@/lib/use-finance-settings';
import { DocumentTable } from '@/components/finance/DocumentTable';

const STATUSES = ['', 'draft', 'sent', 'partially_paid', 'paid', 'cancelled'];

export default function InvoicesPage() {
  const { currencySymbol } = useFinanceSettings();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await financeApi.listInvoices({
        page,
        page_size: 20,
        status: status || undefined,
        q: search || undefined,
      });
      setInvoices(response.items);
      setTotalPages(response.total_pages || 1);
      setTotal(response.total);
    } catch (loadError) {
      setError(financeErrorMessage(loadError, 'Could not load invoices.'));
    } finally {
      setLoading(false);
    }
  }, [page, status, search]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Finance</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Invoices</h1>
        </div>
        <Link
          href="/finance/invoices/new"
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          + New Invoice
        </Link>
      </div>

      <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <input
          value={search}
          onChange={(event) => {
            setPage(1);
            setSearch(event.target.value);
          }}
          placeholder="Search by invoice number…"
          aria-label="Search invoices"
          className="min-w-[220px] flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none"
        />
        <select
          value={status}
          onChange={(event) => {
            setPage(1);
            setStatus(event.target.value);
          }}
          aria-label="Filter by status"
          className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
        >
          {STATUSES.map((value) => (
            <option key={value || 'all'} value={value}>
              {value ? value.replace(/_/g, ' ') : 'All statuses'}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-slate-400">
          Loading invoices…
        </div>
      ) : (
        <DocumentTable
          documents={invoices}
          currencySymbol={currencySymbol}
          emptyMessage={search || status ? 'No invoices match these filters.' : 'No invoices yet.'}
          emptyActionHref={search || status ? undefined : '/finance/invoices/new'}
          emptyActionLabel={search || status ? undefined : 'Create the first invoice'}
        />
      )}

      {totalPages > 1 ? (
        <div className="flex items-center justify-between text-sm text-slate-400">
          <span>
            Page {page} of {totalPages} · {total} total
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 transition hover:bg-slate-800 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page >= totalPages}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 transition hover:bg-slate-800 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
