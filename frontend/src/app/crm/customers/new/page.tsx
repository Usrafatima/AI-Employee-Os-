'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { crmApi, type CustomerStatus } from '@/lib/crm-api';

export default function NewCustomerPage() {
  const router = useRouter();
  const [form, setForm] = useState<{
    full_name: string;
    company_name: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    country: string;
    industry: string;
    notes: string;
    status: CustomerStatus;
  }>({
    full_name: '',
    company_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    country: '',
    industry: '',
    notes: '',
    status: 'active',
  });
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await crmApi.createCustomer(form);
      router.push('/crm/customers');
    } catch (error) {
      console.error('Create customer failed', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h1 className="text-2xl font-bold text-white">Create Customer</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-4 md:grid-cols-2">
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Company name" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 md:col-span-2" placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Industry" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
        <select className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as 'active' | 'inactive' })}>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <textarea className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 md:col-span-2" placeholder="Notes" rows={4} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <div className="md:col-span-2 flex justify-end">
          <button type="submit" disabled={loading} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-60">
            {loading ? 'Saving...' : 'Save Customer'}
          </button>
        </div>
      </form>
    </div>
  );
}
