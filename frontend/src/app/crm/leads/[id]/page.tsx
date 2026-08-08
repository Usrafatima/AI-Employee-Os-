'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { crmApi, Lead } from '@/lib/crm-api';

export default function LeadDetailsPage() {
  const params = useParams<{ id: string }>();
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!params.id) return;
      try {
        setLoading(true);
        const data = await crmApi.getLead(Number(params.id));
        setLead(data);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [params.id]);

  if (loading) return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading lead...</div>;
  if (!lead) return <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">Lead not found.</div>;

  return (
    <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <p className="text-sm uppercase tracking-[0.14em] text-indigo-300">Lead Details</p>
      <h1 className="text-3xl font-bold text-white">{lead.title}</h1>
      <div className="grid gap-4 md:grid-cols-2 text-sm text-slate-300">
        <div>Customer ID: {lead.customer_id}</div>
        <div>Source: {lead.source}</div>
        <div>Assigned to: {lead.assigned_to ?? 'Unassigned'}</div>
        <div>Status: {lead.status}</div>
        <div>Expected value: {lead.expected_value ?? '—'}</div>
        <div>Probability: {lead.probability ?? '—'}</div>
        <div>Next followup: {lead.next_followup_date ?? '—'}</div>
        <div>Notes: {lead.notes ?? '—'}</div>
      </div>
    </div>
  );
}
