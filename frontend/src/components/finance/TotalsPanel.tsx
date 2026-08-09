import { formatAmount } from '@/lib/finance-preview';

interface TotalsRow {
  label: string;
  value: number;
  negative?: boolean;
}

interface TotalsPanelProps {
  subtotal: number;
  discountAmount: number;
  taxAmount: number;
  taxRate: number | string;
  grandTotal: number;
  currencySymbol: string;
  /** Extra rows rendered after the grand total, e.g. amount paid / balance due. */
  extraRows?: TotalsRow[];
  /**
   * Marks the figures as a client-side estimate. The backend recalculates
   * every amount on save, so create/edit forms must set this.
   */
  isPreview?: boolean;
}

export function TotalsPanel({
  subtotal,
  discountAmount,
  taxAmount,
  taxRate,
  grandTotal,
  currencySymbol,
  extraRows = [],
  isPreview = false,
}: TotalsPanelProps) {
  const rate = Number(taxRate) || 0;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Totals</h2>
        {isPreview ? (
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            Preview · confirmed by server on save
          </span>
        ) : null}
      </div>

      <dl className="space-y-2 text-sm">
        <div className="flex justify-between text-slate-300">
          <dt>Subtotal</dt>
          <dd className="font-medium">{formatAmount(subtotal, currencySymbol)}</dd>
        </div>
        {discountAmount > 0 ? (
          <div className="flex justify-between text-slate-300">
            <dt>Discount</dt>
            <dd className="font-medium text-amber-300">
              -{formatAmount(discountAmount, currencySymbol)}
            </dd>
          </div>
        ) : null}
        <div className="flex justify-between text-slate-300">
          <dt>Tax ({rate}%)</dt>
          <dd className="font-medium">{formatAmount(taxAmount, currencySymbol)}</dd>
        </div>

        <div className="mt-3 flex justify-between border-t border-slate-800 pt-3 text-base">
          <dt className="font-semibold text-white">Total</dt>
          <dd className="font-bold text-white">{formatAmount(grandTotal, currencySymbol)}</dd>
        </div>

        {extraRows.map((row) => (
          <div key={row.label} className="flex justify-between text-sm text-slate-300">
            <dt>{row.label}</dt>
            <dd className={`font-semibold ${row.negative ? 'text-emerald-300' : 'text-white'}`}>
              {row.negative ? '-' : ''}
              {formatAmount(row.value, currencySymbol)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
