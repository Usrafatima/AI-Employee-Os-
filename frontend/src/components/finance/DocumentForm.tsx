'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AlertCircle, Loader2 } from 'lucide-react';

import { crmApi, type Customer } from '@/lib/crm-api';
import {
  financeApi,
  financeErrorMessage,
  type DiscountType,
  type DocumentItemInput,
} from '@/lib/finance-api';
import { previewTotals } from '@/lib/finance-preview';
import { LineItemsEditor, emptyLineItem } from '@/components/finance/LineItemsEditor';
import { TotalsPanel } from '@/components/finance/TotalsPanel';

type DocumentKind = 'quotation' | 'invoice';

const inputClass =
  'w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50';
const labelClass = 'mb-1.5 block text-xs font-medium text-slate-400';

/**
 * Shared create form for quotations and invoices.
 *
 * The two documents take the same inputs and differ only in their secondary
 * date field and destination endpoint, so a single component keeps their
 * validation and layout identical.
 */
export function DocumentForm({ kind, currencySymbol }: { kind: DocumentKind; currencySymbol: string }) {
  const router = useRouter();
  const isQuotation = kind === 'quotation';

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loadingCustomers, setLoadingCustomers] = useState(true);
  const [customerError, setCustomerError] = useState<string | null>(null);

  const [customerId, setCustomerId] = useState('');
  const [items, setItems] = useState<DocumentItemInput[]>([emptyLineItem()]);
  const [discountType, setDiscountType] = useState<DiscountType>('percentage');
  const [discountValue, setDiscountValue] = useState('0');
  const [taxRate, setTaxRate] = useState('0');
  const [secondaryDate, setSecondaryDate] = useState('');
  const [notes, setNotes] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    crmApi
      .listCustomers({ page: 1, page_size: 100 })
      .then((response) => setCustomers(response.items))
      .catch(() => setCustomerError('Could not load customers from the CRM.'))
      .finally(() => setLoadingCustomers(false));
  }, []);

  const totals = useMemo(
    () => previewTotals(items, discountType, discountValue, taxRate),
    [items, discountType, discountValue, taxRate],
  );

  const hasCompleteItem = items.some(
    (item) => item.description.trim() !== '' && Number(item.quantity) > 0,
  );
  const canSubmit = customerId !== '' && hasCompleteItem && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const payloadItems = items
      .filter((item) => item.description.trim() !== '')
      .map((item) => ({
        description: item.description.trim(),
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price || 0),
      }));

    if (payloadItems.length === 0) {
      setError('Add at least one line item with a description.');
      return;
    }

    setSubmitting(true);
    try {
      const base = {
        customer_id: Number(customerId),
        items: payloadItems,
        discount_type: discountType,
        discount_value: Number(discountValue || 0),
        tax_rate: Number(taxRate || 0),
        notes: notes.trim() || null,
      };

      if (isQuotation) {
        const created = await financeApi.createQuotation({
          ...base,
          valid_until: secondaryDate || null,
        });
        router.push(`/finance/quotations/${created.id}`);
      } else {
        const created = await financeApi.createInvoice({
          ...base,
          due_date: secondaryDate || null,
        });
        router.push(`/finance/invoices/${created.id}`);
      }
    } catch (submitError) {
      setError(financeErrorMessage(submitError, `Could not create the ${kind}.`));
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Finance</p>
          <h1 className="mt-2 text-3xl font-bold text-white">
            New {isQuotation ? 'Quotation' : 'Invoice'}
          </h1>
        </div>
        <Link
          href={`/finance/${isQuotation ? 'quotations' : 'invoices'}`}
          className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
        >
          Cancel
        </Link>
      </div>

      {error ? (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 md:grid-cols-2">
        <div>
          <label htmlFor="customer" className={labelClass}>
            Customer <span className="text-rose-400">*</span>
          </label>
          <select
            id="customer"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            disabled={loadingCustomers || submitting}
            required
            className={inputClass}
          >
            <option value="">
              {loadingCustomers ? 'Loading customers…' : 'Select a customer from the CRM'}
            </option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.full_name}
                {customer.company_name ? ` — ${customer.company_name}` : ''}
              </option>
            ))}
          </select>
          {customerError ? (
            <p className="mt-1.5 text-xs text-rose-300">{customerError}</p>
          ) : (
            <p className="mt-1.5 text-xs text-slate-500">
              Customers are managed in the{' '}
              <Link href="/crm/customers" className="text-indigo-300 hover:underline">
                CRM module
              </Link>
              .
            </p>
          )}
        </div>

        <div>
          <label htmlFor="secondary-date" className={labelClass}>
            {isQuotation ? 'Valid until' : 'Due date'}
          </label>
          <input
            id="secondary-date"
            type="date"
            value={secondaryDate}
            onChange={(event) => setSecondaryDate(event.target.value)}
            disabled={submitting}
            className={inputClass}
          />
        </div>
      </div>

      <LineItemsEditor
        items={items}
        onChange={setItems}
        currencySymbol={currencySymbol}
        disabled={submitting}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label htmlFor="discount-type" className={labelClass}>
                Discount type
              </label>
              <select
                id="discount-type"
                value={discountType}
                onChange={(event) => setDiscountType(event.target.value as DiscountType)}
                disabled={submitting}
                className={inputClass}
              >
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed amount</option>
              </select>
            </div>
            <div>
              <label htmlFor="discount-value" className={labelClass}>
                Discount value
              </label>
              <input
                id="discount-value"
                type="number"
                min="0"
                step="0.01"
                value={discountValue}
                onChange={(event) => setDiscountValue(event.target.value)}
                disabled={submitting}
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="tax-rate" className={labelClass}>
                Tax rate (%)
              </label>
              <input
                id="tax-rate"
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={taxRate}
                onChange={(event) => setTaxRate(event.target.value)}
                disabled={submitting}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label htmlFor="notes" className={labelClass}>
              Notes
            </label>
            <textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Optional note printed on the document"
              disabled={submitting}
              className={inputClass}
            />
          </div>
        </div>

        <div className="space-y-4">
          <TotalsPanel
            subtotal={totals.subtotal}
            discountAmount={totals.discountAmount}
            taxAmount={totals.taxAmount}
            taxRate={taxRate}
            grandTotal={totals.grandTotal}
            currencySymbol={currencySymbol}
            isPreview
          />
          <button
            type="submit"
            disabled={!canSubmit}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {submitting ? 'Creating…' : `Create ${isQuotation ? 'Quotation' : 'Invoice'}`}
          </button>
        </div>
      </div>
    </form>
  );
}
