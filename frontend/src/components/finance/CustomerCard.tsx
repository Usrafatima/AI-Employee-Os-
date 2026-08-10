import Link from 'next/link';
import type { FinanceCustomer } from '@/lib/finance-api';

/** Customer details shown on a finance document. Data is owned by the CRM. */
export function CustomerCard({ customer }: { customer?: FinanceCustomer | null }) {
  if (!customer) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-400">
        Customer details unavailable.
      </div>
    );
  }

  const location = [customer.city, customer.country].filter(Boolean).join(', ');

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Bill To</p>
      <p className="text-base font-semibold text-white">{customer.full_name}</p>
      {customer.company_name ? (
        <p className="text-sm text-slate-400">{customer.company_name}</p>
      ) : null}
      <div className="mt-3 space-y-0.5 text-xs text-slate-400">
        {customer.address ? <p>{customer.address}</p> : null}
        {location ? <p>{location}</p> : null}
        <p>{customer.email}</p>
        {customer.phone ? <p>{customer.phone}</p> : null}
      </div>
      <Link
        href={`/crm/customers/${customer.id}`}
        className="mt-3 inline-block text-xs text-indigo-300 hover:underline"
      >
        View in CRM →
      </Link>
    </div>
  );
}
