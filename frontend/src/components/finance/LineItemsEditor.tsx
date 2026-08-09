'use client';

import { Plus, Trash2 } from 'lucide-react';
import type { DocumentItemInput } from '@/lib/finance-api';
import { formatAmount, lineTotal } from '@/lib/finance-preview';

interface LineItemsEditorProps {
  items: DocumentItemInput[];
  onChange: (items: DocumentItemInput[]) => void;
  currencySymbol: string;
  disabled?: boolean;
}

export const emptyLineItem = (): DocumentItemInput => ({ description: '', quantity: 1, unit_price: '' });

export function LineItemsEditor({ items, onChange, currencySymbol, disabled }: LineItemsEditorProps) {
  const update = (index: number, patch: Partial<DocumentItemInput>) => {
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const remove = (index: number) => {
    // Always keep one row so the form never becomes unusable.
    onChange(items.length === 1 ? [emptyLineItem()] : items.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Line Items</h2>
        <button
          type="button"
          onClick={() => onChange([...items, emptyLineItem()])}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:bg-slate-800 disabled:opacity-50"
        >
          <Plus className="h-3.5 w-3.5" /> Add item
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-[10px] uppercase tracking-wider text-slate-400">
              <th className="px-4 py-3 font-semibold">Description</th>
              <th className="w-28 px-4 py-3 text-right font-semibold">Qty</th>
              <th className="w-36 px-4 py-3 text-right font-semibold">Unit Price</th>
              <th className="w-36 px-4 py-3 text-right font-semibold">Amount</th>
              <th className="w-12 px-2 py-3" />
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index} className="border-b border-slate-800/60 last:border-0">
                <td className="px-4 py-2">
                  <input
                    value={item.description}
                    onChange={(event) => update(index, { description: event.target.value })}
                    placeholder="Product or service"
                    disabled={disabled}
                    aria-label={`Item ${index + 1} description`}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
                  />
                </td>
                <td className="px-4 py-2">
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={item.quantity}
                    onChange={(event) => update(index, { quantity: event.target.value })}
                    disabled={disabled}
                    aria-label={`Item ${index + 1} quantity`}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-right text-slate-100 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
                  />
                </td>
                <td className="px-4 py-2">
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={item.unit_price}
                    onChange={(event) => update(index, { unit_price: event.target.value })}
                    placeholder="0.00"
                    disabled={disabled}
                    aria-label={`Item ${index + 1} unit price`}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-right text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
                  />
                </td>
                <td className="px-4 py-2 text-right font-medium text-slate-200">
                  {formatAmount(lineTotal(item), currencySymbol)}
                </td>
                <td className="px-2 py-2 text-center">
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    disabled={disabled}
                    aria-label={`Remove item ${index + 1}`}
                    className="rounded-lg p-1.5 text-slate-500 transition hover:bg-rose-500/10 hover:text-rose-400 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
