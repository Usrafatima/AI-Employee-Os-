'use client';

import React from 'react';
import {
  DollarSign,
  Target,
  Users,
  ShoppingBag,
  CheckSquare,
  Bot,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { KpiCardData } from '@/lib/api';

interface KpiCardGroupProps {
  cards: KpiCardData[];
}

const iconMap: Record<string, React.ElementType> = {
  'dollar-sign': DollarSign,
  target: Target,
  users: Users,
  'shopping-bag': ShoppingBag,
  'check-square': CheckSquare,
  bot: Bot,
};

export const KpiCardGroup: React.FC<KpiCardGroupProps> = ({ cards }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card) => {
        const Icon = iconMap[card.icon] || DollarSign;

        return (
          <div
            key={card.id}
            className="glass-panel rounded-2xl p-4.5 relative overflow-hidden group hover:-translate-y-1 transition-all duration-300"
          >
            {/* Card Ambient Glow Accent */}
            <div className="absolute -right-6 -bottom-6 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all"></div>

            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 group-hover:text-slate-200 transition-colors">
                {card.title}
              </span>
              <div className="h-9 w-9 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/50 group-hover:text-indigo-300 transition-all">
                <Icon className="h-4.5 w-4.5" />
              </div>
            </div>

            <div className="flex items-baseline justify-between gap-1 mb-2">
              <div className="text-xl font-bold text-white tracking-tight font-mono">
                {card.value}
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px]">
              <div
                className={`flex items-center gap-1 font-semibold ${
                  card.is_positive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {card.is_positive ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span>
                  {card.change_percentage > 0 ? `+${card.change_percentage}%` : `${card.change_percentage}%`}
                </span>
              </div>
              <span className="text-slate-500 truncate max-w-[100px]">{card.timeframe}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
