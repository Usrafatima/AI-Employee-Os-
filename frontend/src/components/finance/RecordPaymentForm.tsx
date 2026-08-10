'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { PAYMENT_METHODS, financeApi, financeErrorMessage, type PaymentMethod } from '@/lib/finance-api';
import { formatAmount } from '@/lib/finance-preview';

const inputClass =
  'w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50';
const labelClass = 'mb-1.5 block text-xs font-medium text-slate-400';

interface RecordPaymentFormProps {
  invoiceId: number;
  balanceDue: number;
  currencySymbol: string;
  onRecorded: (receiptNumber: string | null) => void;
}

/**
 * Records a payment against an invoice. A receipt is issued automatically by
 * the backend, so there is no separate receipt step.
 */
export function RecordPaymentForm({
  invoiceId,
  balanceDue,
  currencySymbol,
  onRecorded,
}: RecordPaymentFormProps) {
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<PaymentMethod>('bank_transfer');
  const [reference, setReference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numericAmount = Number(amount);
  const exceedsBalance = Number.isFinite(numericAmount) && numericAmount > balanceDue;
  const canSubmit = numericAmount > 0 && !exceedsBalance && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payment = await financeApi.recordPayment({
        invoice_id: invoiceId,
        amount: numericAmount,
        method,
        reference: reference.trim() || null,
      });
      setAmount('');
      setReference('');
      onRecorded(payment.receipt?.receipt_number ?? null);
    } catch (submitError) {
      setError(financeErrorMessage(submitError, 'Could not record the payment.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Record a Payment</h2>
        <span className="text-xs text-slate-400">
          Balance {formatAmount(balanceDue, currencySymbol)}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="amount" className={labelClass}>
            Amount <span className="text-rose-400">*</span>
          </label>
          <input
            id="amount"
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="0.00"
            required
            disabled={submitting}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="method" className={labelClass}>
            Method
          </label>
          <select
            id="method"
            value={method}
            onChange={(event) => setMethod(event.target.value as PaymentMethod)}
            disabled={submitting}
            className={inputClass}
          >
            {PAYMENT_METHODS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="reference" className={labelClass}>
            Reference
          </label>
          <input
            id="reference"
            value={reference}
            onChange={(event) => setReference(event.target.value)}
            placeholder="Transaction ID"
            disabled={submitting}
            className={inputClass}
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setAmount(String(balanceDue))}
            disabled={submitting || balanceDue <= 0}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
          >
            Pay full balance
          </button>
        </div>
        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {submitting ? 'Recording…' : 'Record payment'}
        </button>
      </div>

      {exceedsBalance ? (
        <p className="text-xs text-amber-300">
          Amount exceeds the outstanding balance of {formatAmount(balanceDue, currencySymbol)}.
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="text-xs text-rose-300">
          {error}
        </p>
      ) : null}
    </form>
  );
}
