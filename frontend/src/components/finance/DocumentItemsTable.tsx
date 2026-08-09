import type { DocumentItem } from '@/lib/finance-api';
import { formatAmount } from '@/lib/finance-preview';

const formatQuantity = (value: number) =>
  Number.isInteger(value) ? String(value) : String(Number(value.toFixed(3)));

export function DocumentItemsTable({
  items,
  currencySymbol,
}: {
  items: DocumentItem[];
  currencySymbol: string;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-[10px] uppercase tracking-wider text-slate-400">
            <th className="w-10 px-4 py-3 text-center font-semibold">#</th>
            <th className="px-4 py-3 font-semibold">Description</th>
            <th className="px-4 py-3 text-right font-semibold">Qty</th>
            <th className="px-4 py-3 text-right font-semibold">Unit Price</th>
            <th className="px-4 py-3 text-right font-semibold">Amount</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={item.id} className="border-b border-slate-800/60 last:border-0">
              <td className="px-4 py-3 text-center text-slate-500">{index + 1}</td>
              <td className="px-4 py-3 text-slate-200">{item.description}</td>
              <td className="px-4 py-3 text-right text-slate-300">{formatQuantity(item.quantity)}</td>
              <td className="px-4 py-3 text-right text-slate-300">
                {formatAmount(item.unit_price, currencySymbol)}
              </td>
              <td className="px-4 py-3 text-right font-medium text-slate-100">
                {formatAmount(item.line_total, currencySymbol)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
