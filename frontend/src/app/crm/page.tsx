'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CustomerTable } from '@/components/crm/CustomerTable';
import { LeadTable } from '@/components/crm/LeadTable';
import { StatCard } from '@/components/crm/StatCard';
import { crmApi, Customer, Lead } from '@/lib/crm-api';

export default function CRMPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [customerRes, leadRes, summary] = await Promise.all([
          crmApi.listCustomers({ page: 1, page_size: 10 }),
          crmApi.listLeads({ page: 1, page_size: 10 }),
          crmApi.getSummary(),
        ]);

        setCustomers(customerRes.items);
        setLeads(leadRes.items);
        console.log('crm summary', summary);
      } catch (error) {
        console.error('CRM dashboard loading failed', error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const filteredCustomers = customers.filter((customer) => {
    if (!search) return true;
    const value = search.toLowerCase();
    return [customer.full_name, customer.email, customer.company_name ?? '', customer.phone ?? '']
      .join(' ')
      .toLowerCase()
      .includes(value);
  });

  const filteredLeads = leads.filter((lead) => {
    if (!search) return true;
    const value = search.toLowerCase();
    return [lead.title, lead.source, lead.assigned_to ?? '', lead.notes ?? ''].join(' ').toLowerCase().includes(value);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-indigo-300">CRM & Lead Management</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Customer Relationship Dashboard</h1>
        </div>
        <div className="flex gap-3">
          <Link href="/crm/customers/new" className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
            + New Customer
          </Link>
          <Link href="/crm/leads/new" className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800">
            + New Lead
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard title="Total Customers" value={String(customers.length)} hint="Active roster" />
        <StatCard title="Open Leads" value={String(leads.length)} hint="Pipeline" />
        <StatCard title="Search" value={String(filteredCustomers.length + filteredLeads.length)} hint="Matched records" />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search customers and leads..."
          className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Customers</h2>
            <Link href="/crm/customers" className="text-sm text-indigo-300">View all</Link>
          </div>
          {loading ? <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading customers...</div> : <CustomerTable customers={filteredCustomers} />}
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">Leads</h2>
            <Link href="/crm/leads" className="text-sm text-indigo-300">View all</Link>
          </div>
          {loading ? <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading leads...</div> : <LeadTable leads={filteredLeads} />}
        </section>
      </div>
    </div>
  );
}
