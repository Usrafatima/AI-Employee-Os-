import Link from 'next/link';
import { Customer, formatDate } from '@/lib/crm-api';

type Props = {
  customers: Customer[];
};

export function CustomerTable({ customers }: Props) {
  if (!customers.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center text-slate-300">
        No customers found.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-950/60 text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((customer) => (
              <tr key={customer.id} className="border-t border-slate-800">
                <td className="px-4 py-3 text-white">{customer.full_name}</td>
                <td className="px-4 py-3 text-slate-300">{customer.company_name ?? '—'}</td>
                <td className="px-4 py-3 text-slate-300">{customer.email}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-xs ${customer.status === 'active' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
                    {customer.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">{formatDate(customer.updated_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Link href={`/crm/customers/${customer.id}`} className="text-indigo-300 hover:text-indigo-200">View</Link>
                    <Link href={`/crm/customers/${customer.id}/edit`} className="text-cyan-300 hover:text-cyan-200">Edit</Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
