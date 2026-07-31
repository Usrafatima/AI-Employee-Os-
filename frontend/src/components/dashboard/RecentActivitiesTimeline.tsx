'use client';

import React from 'react';
import {
  FileText,
  UserPlus,
  Mail,
  Calendar,
  RefreshCw,
  Activity,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { RecentActivityData } from '@/lib/api';

interface RecentActivitiesTimelineProps {
  activities: RecentActivityData[];
}

const typeIconMap: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  invoice_created: { icon: FileText, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' },
  customer_added: { icon: UserPlus, color: 'text-indigo-400', bg: 'bg-indigo-500/10 border-indigo-500/30' },
  email_sent: { icon: Mail, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' },
  meeting_scheduled: { icon: Calendar, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
  lead_updated: { icon: RefreshCw, color: 'text-violet-400', bg: 'bg-violet-500/10 border-violet-500/30' },
};

export const RecentActivitiesTimeline: React.FC<RecentActivitiesTimelineProps> = ({ activities }) => {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Activity className="h-4 w-4" />
          </div>
          <h2 className="text-base font-bold text-white tracking-tight">Recent Activities Timeline</h2>
        </div>
        <span className="text-[10px] text-slate-400 font-mono bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
          Live Feed
        </span>
      </div>

      <div className="space-y-3 relative before:absolute before:left-4 before:top-2 before:bottom-2 before:w-[1px] before:bg-slate-800">
        {activities.map((act) => {
          const style = typeIconMap[act.type] || {
            icon: Activity,
            color: 'text-indigo-400',
            bg: 'bg-indigo-500/10 border-indigo-500/30',
          };
          const Icon = style.icon;

          return (
            <div key={act.id} className="relative flex items-start gap-3 pl-1 group">
              <div
                className={`h-7 w-7 rounded-lg border flex items-center justify-center shrink-0 z-10 ${style.bg} ${style.color} shadow-sm`}
              >
                <Icon className="h-3.5 w-3.5" />
              </div>

              <div className="flex-1 bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <h4 className="text-xs font-semibold text-white tracking-tight">{act.title}</h4>
                  <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                    <Clock className="h-2.5 w-2.5" />
                    {act.timestamp}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug">{act.description}</p>
                <div className="mt-2 flex items-center justify-between text-[10px]">
                  <span className="text-indigo-400 font-medium bg-indigo-500/10 px-1.5 py-0.2 rounded border border-indigo-500/20">
                    By: {act.user_or_ai}
                  </span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    {act.status}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
