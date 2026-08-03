'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { crmApi, type LeadStatus } from '@/lib/crm-api';

export default function NewLeadPage() {
  const router = useRouter();
  const [form, setForm] = useState<{
    customer_id: string;
    title: string;
    source: string;
    assigned_to: string;
    status: LeadStatus;
    expected_value: string;
    probability: string;
    notes: string;
  }>({
    customer_id: '',
    title: '',
    source: 'website',
    assigned_to: '',
    status: 'new',
    expected_value: '',
    probability: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await crmApi.createLead({
        ...form,
        customer_id: Number(form.customer_id),
        expected_value: form.expected_value ? Number(form.expected_value) : null,
        probability: form.probability ? Number(form.probability) : null,
      });
      router.push('/crm/leads');
    } catch (error) {
      console.error('Create lead failed', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h1 className="text-2xl font-bold text-white">Create Lead</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-4 md:grid-cols-2">
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Customer ID" value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} required />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Source" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} required />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Assigned To" value={form.assigned_to} onChange={(e) => setForm({ ...form, assigned_to: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Expected Value" value={form.expected_value} onChange={(e) => setForm({ ...form, expected_value: e.target.value })} />
        <input className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="Probability %" value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })} />
        <select className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as any })}>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="qualified">Qualified</option>
          <option value="proposal_sent">Proposal Sent</option>
          <option value="negotiation">Negotiation</option>
          <option value="won">Won</option>
          <option value="lost">Lost</option>
        </select>
        <textarea className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 md:col-span-2" placeholder="Notes" rows={4} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <div className="md:col-span-2 flex justify-end">
          <button type="submit" disabled={loading} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-60">
            {loading ? 'Saving...' : 'Save Lead'}
          </button>
        </div>
      </form>
    </div>
  );
}
