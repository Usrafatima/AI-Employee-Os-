'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { AlertCircle, CheckCircle2, Download, FileText, Loader2, Mail, XCircle } from 'lucide-react';

import {
  financeApi,
  financeErrorMessage,
  openDocumentPdf,
  type Quotation,
  type QuotationStatus,
} from '@/lib/finance-api';
import { formatDocumentDate } from '@/lib/finance-preview';
import { useFinanceSettings } from '@/lib/use-finance-settings';
import { CustomerCard } from '@/components/finance/CustomerCard';
import { DocumentItemsTable } from '@/components/finance/DocumentItemsTable';
import { StatusBadge } from '@/components/finance/StatusBadge';
import { TotalsPanel } from '@/components/finance/TotalsPanel';

const actionClass =
  'inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50';

export default function QuotationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const quotationId = Number(params.id);
  const { currencySymbol } = useFinanceSettings();

  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setQuotation(await financeApi.getQuotation(quotationId));
    } catch (loadError) {
      setError(financeErrorMessage(loadError, 'Could not load this quotation.'));
    } finally {
      setLoading(false);
    }
  }, [quotationId]);

  useEffect(() => {
    if (Number.isFinite(quotationId)) load();
    else {
      setError('Invalid quotation reference.');
      setLoading(false);
    }
  }, [quotationId, load]);

  const run = async (label: string, action: () => Promise<unknown>, success?: string) => {
    setBusy(label);
    setError(null);
    setNotice(null);
    try {
      await action();
      if (success) setNotice(success);
      await load();
    } catch (actionError) {
      setError(financeErrorMessage(actionError));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-slate-400">
        Loading quotation…
      </div>
    );
  }

  if (!quotation) {
    return (
      <div className="space-y-4">
        <div role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error ?? 'Quotation not found.'}
        </div>
        <Link href="/finance/quotations" className="text-sm text-indigo-300 hover:underline">
          ← Back to quotations
        </Link>
      </div>
    );
  }

  const isCancelled = quotation.status === 'cancelled';
  const isConverted = quotation.status === 'converted';
  const canDecide = !isCancelled && !isConverted;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/finance/quotations" className="text-xs text-slate-400 hover:text-slate-200">
            ← Quotations
          </Link>
          <div className="mt-2 flex items-center gap-3">
            <h1 className="font-mono text-3xl font-bold text-white">{quotation.quotation_number}</h1>
            <StatusBadge status={quotation.status} />
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Issued {formatDocumentDate(quotation.issue_date)}
            {quotation.valid_until ? ` · Valid until ${formatDocumentDate(quotation.valid_until)}` : ''}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={actionClass}
            disabled={busy !== null}
            onClick={() =>
              run('pdf', () =>
                openDocumentPdf(`/quotations/${quotation.id}/pdf`, `${quotation.quotation_number}.pdf`),
              )
            }
          >
            {busy === 'pdf' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            PDF
          </button>

          <button
            type="button"
            className={actionClass}
            disabled={busy !== null || isCancelled}
            onClick={() =>
              run(
                'send',
                () => financeApi.sendQuotation(quotation.id),
                `Quotation emailed to ${quotation.customer?.email ?? 'the customer'}.`,
              )
            }
          >
            {busy === 'send' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
            Send by email
          </button>

          {canDecide ? (
            <>
              <button
                type="button"
                className={actionClass}
                disabled={busy !== null}
                onClick={() =>
                  run('accept', () => financeApi.setQuotationStatus(quotation.id, 'accepted' as QuotationStatus))
                }
              >
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Mark accepted
              </button>
              <button
                type="button"
                className={actionClass}
                disabled={busy !== null}
                onClick={() =>
                  run('reject', () => financeApi.setQuotationStatus(quotation.id, 'rejected' as QuotationStatus))
                }
              >
                <XCircle className="h-4 w-4 text-rose-400" />
                Mark rejected
              </button>
            </>
          ) : null}

          {!isConverted && !isCancelled ? (
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              disabled={busy !== null}
              onClick={async () => {
                setBusy('convert');
                setError(null);
                try {
                  const invoice = await financeApi.convertQuotation(quotation.id);
                  router.push(`/finance/invoices/${invoice.id}`);
                } catch (convertError) {
                  setError(financeErrorMessage(convertError));
                  setBusy(null);
                }
              }}
            >
              {busy === 'convert' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Convert to invoice
            </button>
          ) : null}
        </div>
      </div>

      {error ? (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      {notice ? (
        <div role="status" className="flex items-start gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{notice}</span>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-4">
          <DocumentItemsTable items={quotation.items} currencySymbol={currencySymbol} />
          {quotation.notes ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Notes</p>
              <p className="whitespace-pre-line text-sm text-slate-300">{quotation.notes}</p>
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          <CustomerCard customer={quotation.customer} />
          <TotalsPanel
            subtotal={quotation.subtotal}
            discountAmount={quotation.discount_amount}
            taxAmount={quotation.tax_amount}
            taxRate={quotation.tax_rate}
            grandTotal={quotation.grand_total}
            currencySymbol={currencySymbol}
          />
        </div>
      </div>
    </div>
  );
}
