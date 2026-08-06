'use client';

import React from 'react';
import {
  Sparkles,
  TrendingUp,
  BrainCircuit,
  Zap,
  ArrowRight,
  ShieldAlert,
  Lightbulb,
} from 'lucide-react';
import { AiInsightsData } from '@/lib/api';

interface AiInsightsPanelProps {
  data: AiInsightsData;
}

export const AiInsightsPanel: React.FC<AiInsightsPanelProps> = ({ data }) => {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-indigo-500/30 bg-gradient-to-br from-slate-900/90 via-indigo-950/20 to-slate-900/90 relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex items-center justify-between mb-5 border-b border-indigo-500/20 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 p-[1px] shadow-lg shadow-indigo-500/20">
            <div className="h-full w-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <BrainCircuit className="h-4.5 w-4.5 text-indigo-400 animate-pulse" />
            </div>
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              AI Insights & Recommendations
              <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono">
                Real-Time AI
              </span>
            </h2>
            <p className="text-xs text-slate-400">Autonomous business forecasting & optimizations</p>
          </div>
        </div>
      </div>

      {/* Main Predictions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        {/* Revenue Prediction Card */}
        <div className="bg-slate-950/80 border border-indigo-500/30 p-4 rounded-xl relative">
          <div className="flex items-center gap-2 mb-2 text-indigo-300 font-semibold text-xs">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <span>AI Revenue Forecast</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-medium">
            {data.revenue_prediction}
          </p>
          <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400">
            <span>Confidence: 94.2%</span>
            <span className="text-emerald-400 font-semibold">+22.8% QoQ</span>
          </div>
        </div>

        {/* Sales Forecast Card */}
        <div className="bg-slate-950/80 border border-indigo-500/30 p-4 rounded-xl relative">
          <div className="flex items-center gap-2 mb-2 text-violet-300 font-semibold text-xs">
            <Zap className="h-4 w-4 text-amber-400" />
            <span>Sales Conversion Pipeline</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-medium">
            {data.sales_forecast}
          </p>
          <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400">
            <span>Confidence: 89.5%</span>
            <span className="text-amber-400 font-semibold">$245,000 Expected</span>
          </div>
        </div>
      </div>

      {/* Actionable Recommendations List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
          Recommended Actions
        </h3>

        {data.insights.map((item) => (
          <div
            key={item.id}
            className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-indigo-500/40 transition-all"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
                    item.impact_level === 'High'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  {item.impact_level} Impact
                </span>
                <h4 className="text-xs font-bold text-white">{item.title}</h4>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">{item.insight}</p>
            </div>

            {item.action_text && (
              <button className="flex items-center justify-center gap-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all shrink-0">
                <span>{item.action_text}</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
