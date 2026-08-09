import Link from 'next/link';
import type { Invoice, Quotation } from '@/lib/finance-api';
import { formatAmount, formatDocumentDate } from '@/lib/finance-preview';
import { StatusBadge } from '@/components/finance/StatusBadge';

const isInvoice = (doc: Quotation | Invoice): doc is Invoice => 'invoice_number' in doc;

interface DocumentTableProps {
  documents: (Quotation | Invoice)[];
  currencySymbol: string;
  emptyMessage: string;
  emptyActionHref?: string;
  emptyActionLabel?: string;
}

export function DocumentTable({
  documents,
  currencySymbol,
  emptyMessage,
  emptyActionHref,
  emptyActionLabel,
}: DocumentTableProps) {
  if (documents.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-10 text-center">
        <p className="text-sm text-slate-400">{emptyMessage}</p>
        {emptyActionHref && emptyActionLabel ? (
          <Link
            href={emptyActionHref}
            className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            {emptyActionLabel}
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-[10px] uppercase tracking-wider text-slate-400">
            <th className="px-4 py-3 font-semibold">Number</th>
            <th className="px-4 py-3 font-semibold">Customer</th>
            <th className="px-4 py-3 font-semibold">Date</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 text-right font-semibold">Total</th>
            <th className="px-4 py-3 text-right font-semibold">Balance</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => {
            const invoice = isInvoice(doc);
            const href = invoice ? `/finance/invoices/${doc.id}` : `/finance/quotations/${doc.id}`;
            const number = invoice ? doc.invoice_number : (doc as Quotation).quotation_number;

            return (
              <tr key={`${number}`} className="border-b border-slate-800/60 transition last:border-0 hover:bg-slate-800/30">
                <td className="px-4 py-3">
                  <Link href={href} className="font-mono text-xs font-semibold text-indigo-300 hover:underline">
                    {number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-200">
                  {doc.customer?.full_name ?? '—'}
                  {doc.customer?.company_name ? (
                    <span className="block text-xs text-slate-500">{doc.customer.company_name}</span>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-slate-400">{formatDocumentDate(doc.issue_date)}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-100">
                  {formatAmount(doc.grand_total, currencySymbol)}
                </td>
                <td className="px-4 py-3 text-right text-slate-300">
                  {invoice ? formatAmount(doc.balance_due, currencySymbol) : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
