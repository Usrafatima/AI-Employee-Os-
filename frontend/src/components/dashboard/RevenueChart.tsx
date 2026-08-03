'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { DollarSign, ArrowUpRight, Filter } from 'lucide-react';
import { RevenueAnalyticsData } from '@/lib/api';

interface RevenueChartProps {
  data: RevenueAnalyticsData;
  onPeriodChange?: (period: string) => void;
}

export const RevenueChart: React.FC<RevenueChartProps> = ({ data, onPeriodChange }) => {
  const [activePeriod, setActivePeriod] = useState(data.period || 'monthly');
  const [viewType, setViewType] = useState<'revenue' | 'net_profit'>('revenue');

  const handlePeriodClick = (p: string) => {
    setActivePeriod(p);
    if (onPeriodChange) onPeriodChange(p);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 relative">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <DollarSign className="h-4 w-4" />
            </div>
            <h2 className="text-base font-bold text-white tracking-tight">Revenue Analytics</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Historical revenue performance, operating expenses, and net profit margins
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* View Toggle */}
          <div className="bg-slate-950 p-1 rounded-xl border border-slate-800 flex items-center">
            <button
              onClick={() => setViewType('revenue')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                viewType === 'revenue'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Revenue & Expenses
            </button>
            <button
              onClick={() => setViewType('net_profit')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                viewType === 'net_profit'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Net Profit Only
            </button>
          </div>

          {/* Period Selector */}
          <div className="bg-slate-950 p-1 rounded-xl border border-slate-800 flex items-center gap-1">
            {['daily', 'weekly', 'monthly', 'yearly'].map((p) => (
              <button
                key={p}
                onClick={() => handlePeriodClick(p)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition-all ${
                  activePeriod === p
                    ? 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary KPI Highlights Header */}
      <div className="grid grid-cols-3 gap-3 mb-5 p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
        <div>
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Period Revenue</div>
          <div className="text-lg font-bold text-white font-mono">${data.total_revenue.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Expenses</div>
          <div className="text-lg font-bold text-rose-400 font-mono">${data.total_expenses.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Net Profit</div>
          <div className="text-lg font-bold text-emerald-400 font-mono">${data.net_profit.toLocaleString()}</div>
        </div>
      </div>

      {/* Recharts Area Chart */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data.chart_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(val) => `$${val >= 1000 ? `${val / 1000}k` : val}`} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '12px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(value: any) => [`$${Number(value).toLocaleString()}`, '']}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

            {viewType === 'revenue' ? (
              <>
                <Area type="monotone" dataKey="revenue" name="Revenue ($)" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRevenue)" />
                <Area type="monotone" dataKey="expenses" name="Expenses ($)" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorExpenses)" />
              </>
            ) : (
              <Area type="monotone" dataKey="net_profit" name="Net Profit ($)" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorProfit)" />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
