'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { crmApi, Lead } from '@/lib/crm-api';

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await crmApi.listLeads({ page: 1, page_size: 20 });
        setLeads(response.items);
      } catch (error) {
        console.error('Failed to load leads', error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (loading) return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading leads...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">Leads</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Lead Pipeline</h1>
        </div>
        <Link href="/crm/leads/new" className="rounded-xl bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500">Add Lead</Link>
      </div>

      <div className="space-y-3">
        {leads.map((lead) => (
          <div key={lead.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">{lead.title}</h2>
                <p className="text-sm text-slate-400">{lead.source} · {lead.assigned_to ?? 'Unassigned'}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-indigo-500/15 px-2 py-1 text-xs text-indigo-200">{lead.status}</span>
                <Link href={`/crm/leads/${lead.id}`} className="text-indigo-300">View</Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
