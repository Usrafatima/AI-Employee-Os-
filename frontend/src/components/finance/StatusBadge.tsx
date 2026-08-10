import type { InvoiceStatus, QuotationStatus } from '@/lib/finance-api';

type AnyStatus = QuotationStatus | InvoiceStatus | string;

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-slate-800 text-slate-300 border-slate-700',
  sent: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  accepted: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  paid: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  partially_paid: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  converted: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  rejected: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  cancelled: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

export function StatusBadge({ status }: { status: AnyStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span
      className={`inline-flex items-center rounded-lg border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${style}`}
    >
      {String(status).replace(/_/g, ' ')}
    </span>
  );
}
