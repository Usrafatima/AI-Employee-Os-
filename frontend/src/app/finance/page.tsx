'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, FileText, Receipt as ReceiptIcon, TrendingUp, Wallet } from 'lucide-react';

import {
  financeApi,
  financeErrorMessage,
  type FinanceSummary,
  type Invoice,
  type Quotation,
} from '@/lib/finance-api';
import { formatAmount } from '@/lib/finance-preview';
import { useFinanceSettings } from '@/lib/use-finance-settings';
import { DocumentTable } from '@/components/finance/DocumentTable';

function KpiCard({
  title,
  value,
  hint,
  icon: Icon,
}: {
  title: string;
  value: string;
  hint?: string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-sm shadow-slate-950/20">
      <div className="flex items-start justify-between">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-400">{title}</p>
        <Icon className="h-4 w-4 text-indigo-400" />
      </div>
      <h3 className="mt-3 text-2xl font-bold text-white">{value}</h3>
      {hint ? <p className="mt-1 text-xs text-indigo-300">{hint}</p> : null}
    </div>
  );
}

export default function FinancePage() {
  const { currencySymbol } = useFinanceSettings();
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [summaryData, quotationData, invoiceData] = await Promise.all([
          financeApi.getSummary(),
          financeApi.listQuotations({ page: 1, page_size: 5 }),
          financeApi.listInvoices({ page: 1, page_size: 5 }),
        ]);
        setSummary(summaryData);
        setQuotations(quotationData.items);
        setInvoices(invoiceData.items);
      } catch (loadError) {
        setError(financeErrorMessage(loadError, 'Could not load finance data.'));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-slate-400">
        Loading finance overview…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Finance Module</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Quotations, Invoices & Payments</h1>
        </div>
        <div className="flex gap-3">
          <Link
            href="/finance/quotations/new"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            + New Quotation
          </Link>
          <Link
            href="/finance/invoices/new"
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
          >
            + New Invoice
          </Link>
        </div>
      </div>

      {error ? (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p>{error}</p>
            <p className="mt-1 text-xs text-rose-300/80">
              Finance endpoints require an access token from the Authentication module. See the module
              README for how to sign in or relax this for a local demo.
            </p>
          </div>
        </div>
      ) : null}

      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="Invoiced"
            value={formatAmount(summary.total_invoiced_value, currencySymbol)}
            hint={`${summary.total_invoices} invoice${summary.total_invoices === 1 ? '' : 's'}`}
            icon={FileText}
          />
          <KpiCard
            title="Collected"
            value={formatAmount(summary.total_collected, currencySymbol)}
            hint={`${summary.paid_invoices} fully paid`}
            icon={Wallet}
          />
          <KpiCard
            title="Outstanding"
            value={formatAmount(summary.total_outstanding, currencySymbol)}
            hint={`${summary.partially_paid_invoices} partially paid`}
            icon={ReceiptIcon}
          />
          <KpiCard
            title="Quoted"
            value={formatAmount(summary.total_quoted_value, currencySymbol)}
            hint={`${summary.total_quotations} quotation${summary.total_quotations === 1 ? '' : 's'}`}
            icon={TrendingUp}
          />
        </div>
      ) : null}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Recent Quotations</h2>
          <Link href="/finance/quotations" className="text-sm text-indigo-300 hover:underline">
            View all
          </Link>
        </div>
        <DocumentTable
          documents={quotations}
          currencySymbol={currencySymbol}
          emptyMessage="No quotations yet."
          emptyActionHref="/finance/quotations/new"
          emptyActionLabel="Create the first quotation"
        />
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Recent Invoices</h2>
          <Link href="/finance/invoices" className="text-sm text-indigo-300 hover:underline">
            View all
          </Link>
        </div>
        <DocumentTable
          documents={invoices}
          currencySymbol={currencySymbol}
          emptyMessage="No invoices yet."
          emptyActionHref="/finance/invoices/new"
          emptyActionLabel="Create the first invoice"
        />
      </section>
    </div>
  );
}
