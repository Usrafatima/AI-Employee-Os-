'use client';

import { useState } from 'react';
import { crmApi, Customer } from '@/lib/crm-api';

export default function CustomerSearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);

  const onSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await crmApi.searchCustomers(query.trim());
      setResults(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <h1 className="text-2xl font-bold text-white">Find Customer</h1>
        <div className="mt-4 flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, email, phone or company"
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100"
          />
          <button onClick={onSearch} className="rounded-xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {results.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">
            {query ? 'No matches found.' : 'Enter a search query to find customers.'}
          </div>
        ) : (
          results.map((customer) => (
            <div key={customer.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-white">{customer.full_name}</h2>
                  <p className="text-sm text-slate-400">{customer.company_name ?? 'Independent'} · {customer.email}</p>
                </div>
                <span className="rounded-full bg-emerald-500/15 px-2 py-1 text-xs text-emerald-300">{customer.status}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
