'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BarChart3,
  FileSpreadsheet,
  Users,
  Target,
  Bot,
  FileText,
  Workflow,
  Settings,
  Sparkles,
  ShieldCheck,
  Briefcase,
  Cpu,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const navigationItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, badge: 'Module 2' },
    { name: 'Reports & Export', href: '/dashboard/reports', icon: FileSpreadsheet },
    { name: 'CRM & Leads', href: '/crm', icon: Target, badge: 'Module 3' },
    { name: 'AI Employees', href: '#', icon: Bot, badge: 'Module 4' },
    { name: 'Communication Hub', href: '#', icon: Users, badge: 'Module 5' },
    { name: 'Finance & Invoices', href: '#', icon: FileText, badge: 'Module 6' },
    { name: 'Productivity Suite', href: '#', icon: Briefcase, badge: 'Module 7' },
    { name: 'Workflow & System', href: '#', icon: Workflow, badge: 'Module 8' },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col h-screen sticky top-0 z-30 backdrop-blur-xl shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/20">
            <div className="h-full w-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
            </div>
          </div>
          <div>
            <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              AI Employee <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded font-mono">OS</span>
            </h1>
            <p className="text-xs text-slate-400">Enterprise AI Workforce</p>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Core Operations
        </div>

        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600/30 to-violet-600/20 text-white border border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`h-4 w-4 transition-transform duration-200 group-hover:scale-110 ${
                    isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'
                  }`}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[9px] font-mono font-medium bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <div className="pt-4 px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          System & Settings
        </div>

        <Link
          href="#"
          className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all"
        >
          <Settings className="h-4 w-4 text-slate-500" />
          <span>System Settings</span>
        </Link>
      </nav>

      {/* AI Agent Status Footer */}
      <div className="p-3.5 border-t border-slate-800/80 m-3 rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-900/40">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] font-semibold text-slate-200">AI Agents Active</span>
          </div>
          <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
        </div>
        <p className="text-[10px] text-slate-400 leading-snug">
          6 AI Assistants monitoring workspace & processing real-time tasks.
        </p>
      </div>
    </aside>
  );
};
