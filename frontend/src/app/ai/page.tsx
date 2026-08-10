'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { MessageSquare, Plus, RotateCcw, Sparkles } from 'lucide-react';
import { ChatWindow } from '@/components/ai/ChatWindow';
import { KnowledgeManager } from '@/components/ai/KnowledgeManager';
import {
  ActivityLog,
  AIConversation,
  AIMessage,
  ChatResponse,
  KnowledgeEntry,
  ProposedAction,
  aiApi,
} from '@/lib/ai-api';

type LeftTab = 'conversations' | 'knowledge' | 'activities';

export default function AIPage() {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeEntry[]>([]);
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [leftTab, setLeftTab] = useState<LeftTab>('conversations');
  const [loading, setLoading] = useState(false);
  const [pendingProposal, setPendingProposal] = useState<ProposedAction | null>(null);
  const [lastPlan, setLastPlan] = useState<string[]>([]);
  const lastUserText = useRef<string>('');

  const loadConversations = useCallback(async () => {
    try {
      setConversations(await aiApi.listConversations());
    } catch (error) {
      console.error('Failed to load conversations', error);
    }
  }, []);

  const loadKnowledge = useCallback(async (q?: string) => {
    try {
      setKnowledge(await aiApi.listKnowledge(q));
    } catch (error) {
      console.error('Failed to load knowledge', error);
    }
  }, []);

  const loadActivities = useCallback(async () => {
    try {
      setActivities(await aiApi.listActivities());
    } catch (error) {
      console.error('Failed to load activities', error);
    }
  }, []);

  useEffect(() => {
    loadConversations();
    loadKnowledge();
  }, [loadConversations, loadKnowledge]);

  const selectConversation = async (conversationId: number) => {
    setActiveConversationId(conversationId);
    setPendingProposal(null);
    setLastPlan([]);
    try {
      setMessages(await aiApi.listMessages(conversationId));
    } catch (error) {
      console.error('Failed to load messages', error);
    }
  };

  const newChat = async () => {
    setPendingProposal(null);
    setLastPlan([]);
    setMessages([]);
    setActiveConversationId(null);
    setLeftTab('conversations');
  };

  const handleChatResponse = (response: ChatResponse) => {
    const now = new Date().toISOString();
    const userMsg: AIMessage = {
      id: -Date.now(),
      conversation_id: response.conversation_id,
      role: 'user',
      content: lastUserText.current,
      created_at: now,
    };
    const assistantMsg: AIMessage = {
      id: -Date.now() - 1,
      conversation_id: response.conversation_id,
      role: 'assistant',
      content: response.reply,
      created_at: now,
    };
    setMessages((previous) => [...previous, userMsg, assistantMsg]);
    setLastPlan(response.plan ?? []);
    setPendingProposal(response.proposed_action ?? null);
    setActiveConversationId((current) => current ?? response.conversation_id);
  };

  const sendMessage = async (text: string) => {
    lastUserText.current = text;
    setLoading(true);
    setPendingProposal(null);
    try {
      const response = await aiApi.chat(text, activeConversationId);
      handleChatResponse(response);
      if (response.conversation_id) await loadConversations();
    } catch (error) {
      console.error('Chat failed', error);
    } finally {
      setLoading(false);
    }
  };

  const confirmProposal = async () => {
    if (!pendingProposal || activeConversationId === null) return;
    setLoading(true);
    try {
      const result = await aiApi.confirmAction(activeConversationId, pendingProposal.action, pendingProposal.arguments);
      const now = new Date().toISOString();
      setMessages((previous) => [
        ...previous,
        {
          id: -Date.now(),
          conversation_id: activeConversationId,
          role: 'assistant',
          content: `[Action result] ${result.message}`,
          created_at: now,
        },
      ]);
    } catch (error) {
      console.error('Action confirmation failed', error);
    } finally {
      setPendingProposal(null);
      setLoading(false);
    }
  };

  const addKnowledge = async (payload: { title: string; content: string; category?: string | null }) => {
    await aiApi.addKnowledge(payload);
    await loadKnowledge();
  };

  const searchKnowledge = async (q: string) => {
    await loadKnowledge(q);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-white tracking-tight">AI Executive Assistant</h1>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-indigo-400" />
              Module 4
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Natural language • business tasks • multi-step reasoning • memory • voice • knowledge base
          </p>
        </div>
        <button
          onClick={newChat}
          className="flex items-center justify-center gap-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/20 transition-all shrink-0"
        >
          <Plus className="h-4 w-4" /> New Chat
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panel: conversations / knowledge / activities */}
        <div className="space-y-4">
          <div className="glass-panel rounded-2xl border border-slate-800 bg-slate-900/60 p-3 flex gap-1">
            {(
              [
                ['conversations', 'Chats'],
                ['knowledge', 'Knowledge'],
                ['activities', 'Audit'],
              ] as [LeftTab, string][]
            ).map(([tab, label]) => (
              <button
                key={tab}
                onClick={() => {
                  setLeftTab(tab);
                  if (tab === 'knowledge') loadKnowledge();
                  if (tab === 'activities') loadActivities();
                }}
                className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  leftTab === tab
                    ? 'bg-indigo-600/30 text-white border border-indigo-500/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {leftTab === 'conversations' && (
            <div className="glass-panel rounded-2xl border border-slate-800 bg-slate-900/60 p-3 space-y-1 max-h-[70vh] overflow-y-auto">
              {conversations.length === 0 && (
                <p className="text-xs text-slate-500 text-center py-6">No conversations yet. Start a new chat!</p>
              )}
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => selectConversation(conversation.id)}
                  className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs transition-all ${
                    activeConversationId === conversation.id
                      ? 'bg-indigo-600/20 text-white border border-indigo-500/30'
                      : 'text-slate-300 hover:bg-slate-800/50'
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                  <span className="truncate">{conversation.title ?? `Chat #${conversation.id}`}</span>
                </button>
              ))}
            </div>
          )}

          {leftTab === 'knowledge' && (
            <KnowledgeManager knowledge={knowledge} onAdd={addKnowledge} onSearch={searchKnowledge} />
          )}

          {leftTab === 'activities' && (
            <div className="glass-panel rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 max-h-[70vh] overflow-y-auto">
              {activities.length === 0 && <p className="text-xs text-slate-500 text-center py-6">No activity yet.</p>}
              {activities.map((activity) => (
                <div key={activity.id} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[11px] font-semibold text-white">{activity.kind}</p>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                        activity.status === 'approved'
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25'
                          : 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/25'
                      }`}
                    >
                      {activity.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{activity.request}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{activity.response}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chat window */}
        <div className="lg:col-span-2">
          <ChatWindow
            messages={messages}
            loading={loading}
            pendingProposal={pendingProposal}
            lastPlan={lastPlan}
            onSend={sendMessage}
            onConfirm={confirmProposal}
            onDecline={() => setPendingProposal(null)}
          />
        </div>
      </div>

      {/* Refresh helper */}
      <div className="flex justify-end">
        <button
          onClick={() => {
            loadConversations();
            loadKnowledge();
          }}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300"
        >
          <RotateCcw className="h-3 w-3" /> Refresh data
        </button>
      </div>
    </div>
  );
}
