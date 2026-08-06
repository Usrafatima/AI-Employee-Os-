'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { crmApi, Customer } from '@/lib/crm-api';

export default function CustomerListPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const response = await crmApi.listCustomers({ page, page_size: 10 });
        setCustomers(response.items);
      } catch (error) {
        console.error('Failed to load customers', error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [page]);

  if (loading) return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading customers...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Customers</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Customer Directory</h1>
        </div>
        <Link href="/crm/customers/new" className="rounded-xl bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500">Add Customer</Link>
      </div>

      {customers.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">
          No customers available.
        </div>
      ) : (
        <div className="space-y-3">
          {customers.map((customer) => (
            <div key={customer.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">{customer.full_name}</h2>
                  <p className="text-sm text-slate-400">{customer.company_name ?? 'Independent'} · {customer.email}</p>
                </div>
                <div className="flex gap-3 text-sm">
                  <Link href={`/crm/customers/${customer.id}`} className="text-indigo-300">Details</Link>
                  <Link href={`/crm/customers/${customer.id}/edit`} className="text-cyan-300">Edit</Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-between">
        <button onClick={() => setPage((value) => Math.max(1, value - 1))} className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200">Prev</button>
        <span className="text-sm text-slate-300">Page {page}</span>
        <button onClick={() => setPage((value) => value + 1)} className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200">Next</button>
      </div>
    </div>
  );
}
