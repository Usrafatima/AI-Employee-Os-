'use client';

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Users, UserCheck, UserPlus } from 'lucide-react';
import { CustomerAnalyticsData } from '@/lib/api';

interface CustomerAnalyticsChartProps {
  data: CustomerAnalyticsData;
}

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981'];

export const CustomerAnalyticsChart: React.FC<CustomerAnalyticsChartProps> = ({ data }) => {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Users className="h-4 w-4" />
            </div>
            <h2 className="text-base font-bold text-white tracking-tight">Customer Analytics</h2>
          </div>
          <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
            +{data.growth_rate}% MoM
          </span>
        </div>

        {/* Highlight Stats Cards */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
              <UserPlus className="h-4 w-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 font-semibold uppercase">New Customers</div>
              <div className="text-base font-bold text-white font-mono">{data.new_customers}</div>
            </div>
          </div>
          <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
              <UserCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Returning</div>
              <div className="text-base font-bold text-white font-mono">{data.returning_customers}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bar Chart for Monthly Customer Trend */}
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.monthly_trend} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="month" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '10px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="new" name="New" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="returning" name="Returning" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Customer Distribution Legend Pills */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
        {data.distribution.map((dist, idx) => (
          <div key={dist.category} className="flex items-center justify-between bg-slate-950/40 px-2.5 py-1.5 rounded-lg border border-slate-800/60">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
              <span className="text-slate-300 text-[11px] truncate max-w-[90px]">{dist.category}</span>
            </div>
            <span className="font-mono text-slate-400 text-[11px] font-semibold">{dist.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};
