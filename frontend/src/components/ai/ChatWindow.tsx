'use client';

import React, { useRef, useState } from 'react';
import { Bot, Check, Mic, Send, Square, User, X } from 'lucide-react';
import { AIMessage, ProposedAction } from '@/lib/ai-api';

interface ChatWindowProps {
  messages: AIMessage[];
  loading: boolean;
  pendingProposal: ProposedAction | null;
  lastPlan: string[];
  onSend: (text: string) => Promise<void>;
  onConfirm: () => Promise<void>;
  onDecline: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  loading,
  pendingProposal,
  lastPlan,
  onSend,
  onConfirm,
  onDecline,
}) => {
  const [input, setInput] = useState('');
  const [recording, setRecording] = useState(false);
  const finalTranscript = useRef('');
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    finalTranscript.current = '';
    await onSend(text);
  };

  const toggleMic = () => {
    if (recording) {
      recognitionRef.current?.stop();
      return;
    }
    const SpeechRecognitionCtor = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      alert('Voice typing is not supported in this browser. Please use Chrome or Edge.');
      return;
    }
    const recognition = new SpeechRecognitionCtor() as SpeechRecognition;
    recognitionRef.current = recognition;
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;
    finalTranscript.current = '';

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0]?.transcript ?? '';
        if (result.isFinal) {
          finalTranscript.current += (finalTranscript.current ? ' ' : '') + text;
        } else {
          interim += text;
        }
      }
      setInput(`${finalTranscript.current}${interim ? ` ${interim}` : ''}`.trim());
    };
    recognition.onend = () => setRecording(false);
    recognition.onerror = () => setRecording(false);

    recognition.start();
    setRecording(true);
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 bg-slate-900/60 flex flex-col h-[70vh] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 p-[1px]">
            <div className="h-full w-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <Bot className="h-4 w-4 text-indigo-400" />
            </div>
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">AI Executive Assistant</h2>
            <p className="text-[11px] text-slate-400">Natural language • tasks • memory • voice • knowledge</p>
          </div>
        </div>
        {recording && (
          <span className="flex items-center gap-1.5 text-[11px] text-rose-400 font-medium">
            <Square className="h-3 w-3" /> Recording… (speak now)
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
            <Bot className="h-10 w-10 text-indigo-500/40" />
            <p className="text-sm">Ask me anything — summaries, follow-ups, tasks, or company questions.</p>
            <p className="text-xs">E.g. “What is our enterprise pricing?” or “Add a customer for Acme Corp”</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-br-md'
                  : 'bg-slate-950/80 border border-slate-800 text-slate-200 rounded-bl-md'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-1 text-[10px] uppercase tracking-wider opacity-70">
                {message.role === 'user' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                {message.role === 'user' ? 'You' : 'Assistant'}
              </div>
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {lastPlan.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pl-2">
            {lastPlan.map((step, index) => (
              <span
                key={index}
                className="text-[10px] bg-indigo-500/15 text-indigo-300 border border-indigo-500/25 px-2 py-0.5 rounded-full"
              >
                {index + 1}. {step}
              </span>
            ))}
          </div>
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm text-slate-400 flex items-center gap-2">
              <span className="h-2 w-2 bg-indigo-400 rounded-full animate-pulse" />
              Thinking…
            </div>
          </div>
        )}

        {/* Pending proposal (approval gate) */}
        {pendingProposal && (
          <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-4">
            <p className="text-xs font-bold text-amber-300 uppercase tracking-wider mb-1.5">
              Proposed business task
            </p>
            <p className="text-sm text-slate-200">
              Execute <span className="font-semibold text-white">{pendingProposal.action}</span>?
            </p>
            <div className="mt-3 flex gap-2">
              <button
                onClick={onConfirm}
                className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold"
              >
                <Check className="h-3.5 w-3.5" /> Confirm
              </button>
              <button
                onClick={onDecline}
                className="flex items-center gap-1.5 border border-slate-700 text-slate-300 hover:bg-slate-800 px-3.5 py-1.5 rounded-xl text-xs font-medium"
              >
                <X className="h-3.5 w-3.5" /> Decline
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800/80 flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMic}
          title={recording ? 'Stop recording' : 'Voice input (types what you say)'}
          className={`h-11 w-11 rounded-xl flex items-center justify-center transition-all shrink-0 ${
            recording
              ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          {recording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your message… (or tap the mic and speak)"
          disabled={loading}
          className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="h-11 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white flex items-center gap-1.5 text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
        >
          <Send className="h-4 w-4" /> Send
        </button>
      </form>
    </div>
  );
};
