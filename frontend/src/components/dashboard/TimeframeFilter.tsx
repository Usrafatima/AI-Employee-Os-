'use client';

import React from 'react';
import { Calendar, Clock, RefreshCw } from 'lucide-react';

interface TimeframeFilterProps {
  selectedTimeframe: string;
  onSelectTimeframe: (tf: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const TimeframeFilter: React.FC<TimeframeFilterProps> = ({
  selectedTimeframe,
  onSelectTimeframe,
  onRefresh,
  isLoading = false,
}) => {
  const timeframes = [
    { id: 'today', label: 'Today' },
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'year', label: 'This Year' },
    { id: 'custom', label: 'Custom Date' },
  ];

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/70 border border-slate-800 p-2 rounded-2xl backdrop-blur-md">
      <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
        <div className="flex items-center gap-1.5 px-3 py-1 text-slate-400 text-xs font-medium border-r border-slate-800 mr-1">
          <Clock className="h-3.5 w-3.5 text-indigo-400" />
          <span>Period:</span>
        </div>

        {timeframes.map((tf) => {
          const isActive = selectedTimeframe === tf.id;
          return (
            <button
              key={tf.id}
              onClick={() => onSelectTimeframe(tf.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 whitespace-nowrap ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-500/25 border border-indigo-400/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {tf.label}
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-2">
        {selectedTimeframe === 'custom' && (
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1 rounded-xl text-xs text-slate-300">
            <Calendar className="h-3.5 w-3.5 text-indigo-400" />
            <span>Jul 01, 2026 - Jul 30, 2026</span>
          </div>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-xl text-xs font-medium transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 text-indigo-400 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Analytics</span>
          </button>
        )}
      </div>
    </div>
  );
};
