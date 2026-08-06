'use client';

import React from 'react';
import { Search, Bell, Sparkles, User, ChevronDown, Cpu } from 'lucide-react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Dashboard & Business Analytics',
  subtitle = 'Real-time performance metrics, AI workforce actions, and revenue insights',
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-base font-semibold text-white tracking-tight">{title}</h1>
        <p className="text-xs text-slate-400">{subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Global Quick Search Input */}
        <div className="relative w-64 hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search leads, reports, invoices..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/60 transition-all"
          />
        </div>

        {/* Live AI Co-Pilot Status */}
        <div className="flex items-center gap-2 bg-indigo-950/40 border border-indigo-500/30 px-3 py-1.5 rounded-xl">
          <Cpu className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
          <span className="text-xs font-medium text-indigo-200 hidden sm:inline">AI Employee OS</span>
          <span className="text-[10px] font-mono bg-indigo-500/20 text-indigo-300 px-1.5 py-0.2 rounded border border-indigo-500/30">
            v1.0
          </span>
        </div>

        {/* Notification Bell */}
        <button className="relative p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-all">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-500 ring-2 ring-slate-900"></span>
        </button>

        {/* User Profile Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 p-0.5 shadow-md">
            <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <User className="h-4 w-4 text-indigo-300" />
            </div>
          </div>
          <div className="hidden lg:block text-left">
            <div className="text-xs font-semibold text-slate-200">Business Owner</div>
            <div className="text-[10px] text-slate-400">admin@company.com</div>
          </div>
          <ChevronDown className="h-3.5 w-3.5 text-slate-500 hidden sm:block" />
        </div>
      </div>
    </header>
  );
};
