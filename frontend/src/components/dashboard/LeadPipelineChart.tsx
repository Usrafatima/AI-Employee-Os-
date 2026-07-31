'use client';

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { Target, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { LeadAnalyticsData } from '@/lib/api';

interface LeadPipelineChartProps {
  data: LeadAnalyticsData;
}

const STAGE_COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#10b981'];

export const LeadPipelineChart: React.FC<LeadPipelineChartProps> = ({ data }) => {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-violet-500/10 border border-violet-500/30 flex items-center justify-center text-violet-400">
              <Target className="h-4 w-4" />
            </div>
            <h2 className="text-base font-bold text-white tracking-tight">Lead Pipeline</h2>
          </div>
          <span className="text-xs font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-0.5 rounded-full font-mono">
            {data.conversion_rate}% Conversion
          </span>
        </div>

        {/* Lead Funnel KPI Grid */}
        <div className="grid grid-cols-4 gap-2 mb-4 text-center">
          <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 font-semibold uppercase">Total</div>
            <div className="text-sm font-bold text-white font-mono mt-0.5">{data.total_leads}</div>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-indigo-400 font-semibold uppercase">Qualified</div>
            <div className="text-sm font-bold text-indigo-300 font-mono mt-0.5">{data.qualified_leads}</div>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-emerald-400 font-semibold uppercase">Converted</div>
            <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">{data.converted_leads}</div>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <div className="text-[10px] text-rose-400 font-semibold uppercase">Lost</div>
            <div className="text-sm font-bold text-rose-400 font-mono mt-0.5">{data.lost_leads}</div>
          </div>
        </div>
      </div>

      {/* Horizontal Funnel Bar Chart */}
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={data.pipeline_stages} margin={{ top: 0, right: 20, left: 35, bottom: 0 }}>
            <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis type="category" dataKey="stage" stroke="#64748b" tick={{ fill: '#cbd5e1', fontSize: 11 }} width={90} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '10px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: any, name: any, item: any) => [`${val} Leads (${item.payload.value})`, 'Count']}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]}>
              {data.pipeline_stages.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={STAGE_COLORS[index % STAGE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-2.5">
        <span className="flex items-center gap-1.5 text-slate-300">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          AI Lead Auto-Scoring active
        </span>
        <span className="font-mono text-indigo-400 font-semibold">$969,000 Pipeline Value</span>
      </div>
    </div>
  );
};
