import { apiClient } from '@/lib/api';

export interface AIConversation {
  id: number;
  title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIMessage {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface KnowledgeEntry {
  id: number;
  title: string;
  content: string;
  category?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ActivityLog {
  id: number;
  kind: string;
  request: string;
  response: string;
  intent?: string | null;
  status: string;
  created_at: string;
}

export interface ProposedAction {
  action: string;
  arguments: Record<string, unknown>;
  requires_approval: boolean;
}

export interface ChatResponse {
  reply: string;
  conversation_id: number;
  plan: string[];
  proposed_action?: ProposedAction | null;
  created_at: string;
}

export interface ActionConfirmResponse {
  success: boolean;
  tool: string;
  message: string;
  result?: Record<string, unknown> | null;
}

export const aiApi = {
  chat: async (message: string, conversationId?: number | null): Promise<ChatResponse> =>
    (
      await apiClient.post<ChatResponse>(
        '/ai/chat',
        { message, conversation_id: conversationId ?? null },
        { timeout: 90000 }, // LLM replies can take longer than the shared 5s timeout
      )
    ).data,

  listConversations: async (): Promise<AIConversation[]> =>
    (await apiClient.get<AIConversation[]>('/ai/conversations')).data,

  createConversation: async (title?: string): Promise<AIConversation> =>
    (await apiClient.post<AIConversation>('/ai/conversations', { title: title ?? null })).data,

  listMessages: async (conversationId: number): Promise<AIMessage[]> =>
    (await apiClient.get<AIMessage[]>(`/ai/conversations/${conversationId}/messages`)).data,

  listKnowledge: async (q?: string): Promise<KnowledgeEntry[]> =>
    (await apiClient.get<KnowledgeEntry[]>('/ai/knowledge', { params: q ? { q } : {} })).data,

  addKnowledge: async (payload: { title: string; content: string; category?: string | null }): Promise<KnowledgeEntry> =>
    (await apiClient.post<KnowledgeEntry>('/ai/knowledge', payload)).data,

  listActivities: async (): Promise<ActivityLog[]> =>
    (await apiClient.get<ActivityLog[]>('/ai/activities')).data,

  confirmAction: async (
    conversationId: number,
    action: string,
    arguments_: Record<string, unknown>,
  ): Promise<ActionConfirmResponse> =>
    (
      await apiClient.post<ActionConfirmResponse>(
        '/ai/actions/confirm',
        {
          conversation_id: conversationId,
          action,
          arguments: arguments_,
        },
        { timeout: 90000 },
      )
    ).data,

  sendVoice: async (audioBlob: Blob, conversationId?: number | null): Promise<ChatResponse> => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice.webm');
    if (conversationId) formData.append('conversation_id', String(conversationId));
    // Transcription + LLM can be slow on first use.
    return (await apiClient.post<ChatResponse>('/ai/voice', formData, { timeout: 120000 })).data;
  },
};
