/**
 * Client-side preview of document totals.
 *
 * IMPORTANT: these numbers are for on-screen feedback only. The backend
 * recomputes every amount from the line items before persisting anything
 * (see `app/services/finance_calculator.py`), and its result is what is
 * stored and printed. Nothing here is ever sent as an authoritative total.
 *
 * The rule mirrors the backend exactly so the preview matches what will be
 * saved:
 *
 *   line_total   = quantity x unit_price
 *   subtotal     = sum(line_totals)
 *   discount     = % of subtotal, or a fixed amount (capped at subtotal)
 *   taxable_base = subtotal - discount
 *   tax          = taxable_base x tax_rate%
 *   grand_total  = taxable_base + tax
 *
 * Amounts are rounded to 2 decimal places at each step, half away from zero,
 * matching the backend's ROUND_HALF_UP.
 */

import type { DiscountType, DocumentItemInput } from '@/lib/finance-api';

export interface PreviewTotals {
  subtotal: number;
  discountAmount: number;
  taxAmount: number;
  grandTotal: number;
  lineTotals: number[];
}

const toNumber = (value: number | string | null | undefined): number => {
  const parsed = typeof value === 'number' ? value : Number.parseFloat(String(value ?? '').trim());
  return Number.isFinite(parsed) ? parsed : 0;
};

/** Round to 2dp, half away from zero (JS `toFixed` is unreliable near .005). */
const round2 = (value: number): number => {
  const scaled = value * 100;
  const rounded = Math.sign(scaled) * Math.round(Math.abs(scaled) + Number.EPSILON);
  return rounded / 100;
};

export const lineTotal = (item: DocumentItemInput): number =>
  round2(Math.max(0, toNumber(item.quantity)) * Math.max(0, toNumber(item.unit_price)));

export const previewTotals = (
  items: DocumentItemInput[],
  discountType: DiscountType,
  discountValue: number | string,
  taxRate: number | string,
): PreviewTotals => {
  const lineTotals = items.map(lineTotal);
  const subtotal = round2(lineTotals.reduce((sum, value) => sum + value, 0));

  const rawDiscount = Math.max(0, toNumber(discountValue));
  const discountAmount =
    discountType === 'percentage'
      ? round2((subtotal * Math.min(rawDiscount, 100)) / 100)
      : Math.min(round2(rawDiscount), subtotal);

  const taxableBase = subtotal - discountAmount;
  const taxAmount = round2((taxableBase * Math.max(0, Math.min(toNumber(taxRate), 100))) / 100);

  return {
    subtotal,
    discountAmount,
    taxAmount,
    grandTotal: round2(taxableBase + taxAmount),
    lineTotals,
  };
};

/** Format an amount using the currency configured by the backend. */
export const formatAmount = (value: number | null | undefined, symbol = '$'): string => {
  if (value === null || value === undefined || !Number.isFinite(value)) return `${symbol}0.00`;
  return `${symbol}${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
};

export const formatDocumentDate = (value?: string | null): string => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};
