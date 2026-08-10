import Link from 'next/link';
import { Lead, formatCurrency, formatDate } from '@/lib/crm-api';

type Props = {
  leads: Lead[];
};

export function LeadTable({ leads }: Props) {
  if (!leads.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">
        No leads found.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-950/60 text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Title</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Assigned To</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Value</th>
              <th className="px-4 py-3 font-medium">Next Follow-up</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id} className="border-t border-slate-800">
                <td className="px-4 py-3 text-white">{lead.title}</td>
                <td className="px-4 py-3 text-slate-300">{lead.source}</td>
                <td className="px-4 py-3 text-slate-300">{lead.assigned_to ?? 'Unassigned'}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-indigo-500/15 px-2 py-1 text-xs text-indigo-200">{lead.status}</span>
                </td>
                <td className="px-4 py-3 text-slate-300">{formatCurrency(lead.expected_value)}</td>
                <td className="px-4 py-3 text-slate-300">{formatDate(lead.next_followup_date)}</td>
                <td className="px-4 py-3">
                  <Link href={`/crm/leads/${lead.id}`} className="text-indigo-300 hover:text-indigo-200">View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
