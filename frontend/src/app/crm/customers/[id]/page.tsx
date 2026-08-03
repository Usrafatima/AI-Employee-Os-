'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { crmApi, CustomerProfile } from '@/lib/crm-api';

export default function CustomerDetailsPage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!params.id) return;
      try {
        setLoading(true);
        const data = await crmApi.getCustomerProfile(Number(params.id));
        setProfile(data);
      } catch (error) {
        console.error('Failed to load customer profile', error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [params.id]);

  if (loading) return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading customer profile...</div>;
  if (!profile) return <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">Customer not found.</div>;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-sm uppercase tracking-[0.14em] text-indigo-300">Customer Profile</p>
        <h1 className="mt-3 text-3xl font-bold text-white">{profile.customer.full_name}</h1>
        <p className="mt-1 text-slate-400">{profile.customer.company_name ?? 'Independent'} · {profile.customer.email}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-xl font-semibold text-white">Details</h2>
          <dl className="mt-4 space-y-3 text-sm text-slate-300">
            <div className="flex justify-between gap-4"><dt>Phone</dt><dd>{profile.customer.phone ?? '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt>City</dt><dd>{profile.customer.city ?? '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt>Country</dt><dd>{profile.customer.country ?? '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt>Industry</dt><dd>{profile.customer.industry ?? '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt>Status</dt><dd>{profile.customer.status}</dd></div>
          </dl>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-xl font-semibold text-white">Latest CRM Update</h2>
          {profile.crm_update ? (
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <p><span className="text-slate-400">Last Activity:</span> {profile.crm_update.last_activity}</p>
              <p><span className="text-slate-400">Next Follow-up:</span> {profile.crm_update.next_followup_date ?? '—'}</p>
              <p><span className="text-slate-400">Last Updated By:</span> {profile.crm_update.last_updated_by ?? '—'}</p>
            </div>
          ) : (
            <p className="mt-4 text-slate-400">No CRM update recorded yet.</p>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-xl font-semibold text-white">Leads</h2>
          <div className="mt-4 space-y-3">
            {profile.leads.map((lead) => (
              <div key={lead.id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-sm text-slate-300">
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-white">{lead.title}</strong>
                  <span className="rounded-full bg-indigo-500/15 px-2 py-1 text-xs text-indigo-200">{lead.status}</span>
                </div>
                <p className="mt-2">Source: {lead.source}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-xl font-semibold text-white">Conversation History</h2>
          <div className="mt-4 space-y-3">
            {profile.conversations.map((message) => (
              <div key={message.id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-sm text-slate-300">
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-medium text-white">{message.sender}</span>
                  <span className="text-xs text-slate-500">{new Date(message.created_at).toLocaleDateString()}</span>
                </div>
                <p>{message.message}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="text-xl font-semibold text-white">Activity Timeline</h2>
        <div className="mt-4 space-y-3">
          {profile.activity_timeline.map((activity) => (
            <div key={activity.id} className="border-l border-indigo-500/40 pl-4 text-sm text-slate-300">
              <div className="font-medium text-white">{activity.activity_type}</div>
              <p className="mt-1">{activity.description}</p>
              <p className="mt-1 text-xs text-slate-500">{new Date(activity.created_at).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
