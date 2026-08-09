'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { AlertCircle, CheckCircle2, Download, Loader2, Mail, Receipt as ReceiptIcon } from 'lucide-react';

import {
  financeApi,
  financeErrorMessage,
  openDocumentPdf,
  type Invoice,
  type Payment,
} from '@/lib/finance-api';
import { formatAmount, formatDocumentDate } from '@/lib/finance-preview';
import { useFinanceSettings } from '@/lib/use-finance-settings';
import { CustomerCard } from '@/components/finance/CustomerCard';
import { DocumentItemsTable } from '@/components/finance/DocumentItemsTable';
import { RecordPaymentForm } from '@/components/finance/RecordPaymentForm';
import { StatusBadge } from '@/components/finance/StatusBadge';
import { TotalsPanel } from '@/components/finance/TotalsPanel';

const actionClass =
  'inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50';

const METHOD_LABELS: Record<string, string> = {
  cash: 'Cash',
  bank_transfer: 'Bank Transfer',
  card: 'Card',
  online: 'Online Payment',
};

export default function InvoiceDetailPage() {
  const params = useParams<{ id: string }>();
  const invoiceId = Number(params.id);
  const { currencySymbol } = useFinanceSettings();

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [invoiceData, paymentData] = await Promise.all([
        financeApi.getInvoice(invoiceId),
        financeApi.listInvoicePayments(invoiceId),
      ]);
      setInvoice(invoiceData);
      setPayments(paymentData.items);
    } catch (loadError) {
      setError(financeErrorMessage(loadError, 'Could not load this invoice.'));
    } finally {
      setLoading(false);
    }
  }, [invoiceId]);

  useEffect(() => {
    if (Number.isFinite(invoiceId)) load();
    else {
      setError('Invalid invoice reference.');
      setLoading(false);
    }
  }, [invoiceId, load]);

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
        Loading invoice…
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="space-y-4">
        <div role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error ?? 'Invoice not found.'}
        </div>
        <Link href="/finance/invoices" className="text-sm text-indigo-300 hover:underline">
          ← Back to invoices
        </Link>
      </div>
    );
  }

  const isCancelled = invoice.status === 'cancelled';
  const isSettled = invoice.balance_due <= 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/finance/invoices" className="text-xs text-slate-400 hover:text-slate-200">
            ← Invoices
          </Link>
          <div className="mt-2 flex items-center gap-3">
            <h1 className="font-mono text-3xl font-bold text-white">{invoice.invoice_number}</h1>
            <StatusBadge status={invoice.status} />
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Issued {formatDocumentDate(invoice.issue_date)}
            {invoice.due_date ? ` · Due ${formatDocumentDate(invoice.due_date)}` : ''}
            {invoice.quotation_id ? (
              <>
                {' · '}
                <Link
                  href={`/finance/quotations/${invoice.quotation_id}`}
                  className="text-indigo-300 hover:underline"
                >
                  From quotation
                </Link>
              </>
            ) : null}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={actionClass}
            disabled={busy !== null}
            onClick={() =>
              run('pdf', () =>
                openDocumentPdf(`/invoices/${invoice.id}/pdf`, `${invoice.invoice_number}.pdf`),
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
                () => financeApi.sendInvoice(invoice.id),
                `Invoice emailed to ${invoice.customer?.email ?? 'the customer'}.`,
              )
            }
          >
            {busy === 'send' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
            Send by email
          </button>
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
          <DocumentItemsTable items={invoice.items} currencySymbol={currencySymbol} />

          {!isCancelled && !isSettled ? (
            <RecordPaymentForm
              invoiceId={invoice.id}
              balanceDue={invoice.balance_due}
              currencySymbol={currencySymbol}
              onRecorded={(receiptNumber) => {
                setNotice(
                  receiptNumber
                    ? `Payment recorded. Receipt ${receiptNumber} was issued automatically.`
                    : 'Payment recorded.',
                );
                load();
              }}
            />
          ) : null}

          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-white">Payment History</h2>
            {payments.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-center text-sm text-slate-400">
                No payments recorded yet.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
                <table className="w-full min-w-[600px] text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-left text-[10px] uppercase tracking-wider text-slate-400">
                      <th className="px-4 py-3 font-semibold">Date</th>
                      <th className="px-4 py-3 font-semibold">Method</th>
                      <th className="px-4 py-3 font-semibold">Reference</th>
                      <th className="px-4 py-3 font-semibold">Receipt</th>
                      <th className="px-4 py-3 text-right font-semibold">Amount</th>
                      <th className="px-4 py-3 text-right font-semibold">PDF</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((payment) => (
                      <tr key={payment.id} className="border-b border-slate-800/60 last:border-0">
                        <td className="px-4 py-3 text-slate-300">
                          {formatDocumentDate(payment.payment_date)}
                        </td>
                        <td className="px-4 py-3 text-slate-300">
                          {METHOD_LABELS[payment.method] ?? payment.method}
                        </td>
                        <td className="px-4 py-3 text-slate-400">{payment.reference || '—'}</td>
                        <td className="px-4 py-3 font-mono text-xs text-indigo-300">
                          {payment.receipt?.receipt_number ?? '—'}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-slate-100">
                          {formatAmount(payment.amount, currencySymbol)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {payment.receipt ? (
                            <button
                              type="button"
                              aria-label={`Download receipt ${payment.receipt.receipt_number}`}
                              disabled={busy !== null}
                              onClick={() =>
                                run('receipt', () =>
                                  openDocumentPdf(
                                    `/receipts/${payment.receipt!.id}/pdf`,
                                    `${payment.receipt!.receipt_number}.pdf`,
                                  ),
                                )
                              }
                              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
                            >
                              <ReceiptIcon className="h-3.5 w-3.5" />
                              Receipt
                            </button>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {invoice.notes ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Notes</p>
              <p className="whitespace-pre-line text-sm text-slate-300">{invoice.notes}</p>
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          <CustomerCard customer={invoice.customer} />
          <TotalsPanel
            subtotal={invoice.subtotal}
            discountAmount={invoice.discount_amount}
            taxAmount={invoice.tax_amount}
            taxRate={invoice.tax_rate}
            grandTotal={invoice.grand_total}
            currencySymbol={currencySymbol}
            extraRows={[
              { label: 'Amount Paid', value: invoice.amount_paid, negative: true },
              { label: 'Balance Due', value: invoice.balance_due },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
