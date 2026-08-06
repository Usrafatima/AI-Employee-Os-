'use client';

import React, { useState } from 'react';
import { BookOpen, Plus, Search } from 'lucide-react';
import { KnowledgeEntry } from '@/lib/ai-api';

interface KnowledgeManagerProps {
  knowledge: KnowledgeEntry[];
  onAdd: (payload: { title: string; content: string; category?: string | null }) => Promise<void>;
  onSearch: (q: string) => Promise<void>;
}

export const KnowledgeManager: React.FC<KnowledgeManagerProps> = ({ knowledge, onAdd, onSearch }) => {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [content, setContent] = useState('');
  const [search, setSearch] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !content.trim() || submitting) return;
    setSubmitting(true);
    try {
      await onAdd({ title: title.trim(), content: content.trim(), category: category.trim() || null });
      setTitle('');
      setCategory('');
      setContent('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
      <div className="flex items-center gap-2.5">
        <BookOpen className="h-4 w-4 text-indigo-400" />
        <h3 className="text-sm font-bold text-white tracking-tight">Company Knowledge Base</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Title (e.g. Pricing policy)"
            className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
          />
          <input
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            placeholder="Category (optional)"
            className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Content the assistant should know…"
          rows={3}
          className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none resize-none"
        />
        <button
          type="submit"
          disabled={!title.trim() || !content.trim() || submitting}
          className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold disabled:opacity-40"
        >
          <Plus className="h-3.5 w-3.5" /> Add to knowledge base
        </button>
      </form>

      <div className="relative">
        <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            onSearch(event.target.value);
          }}
          placeholder="Search knowledge…"
          className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-9 pr-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
        />
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {knowledge.length === 0 && (
          <p className="text-xs text-slate-500 text-center py-4">
            No knowledge added yet. Add company info so the assistant can answer from it.
          </p>
        )}
        {knowledge.map((entry) => (
          <div key={entry.id} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold text-white">{entry.title}</p>
              {entry.category && (
                <span className="text-[9px] bg-violet-500/15 text-violet-300 border border-violet-500/25 px-1.5 py-0.5 rounded-full shrink-0">
                  {entry.category}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-3 whitespace-pre-wrap">{entry.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
