import axios from 'axios';
import { apiClient } from '@/lib/api';

export type CustomerStatus = 'active' | 'inactive';
export type LeadStatus =
  | 'new'
  | 'contacted'
  | 'qualified'
  | 'proposal_sent'
  | 'negotiation'
  | 'won'
  | 'lost';

export interface Customer {
  id: number;
  full_name: string;
  company_name?: string | null;
  email: string;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  industry?: string | null;
  notes?: string | null;
  status: CustomerStatus;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: number;
  customer_id: number;
  title: string;
  source: string;
  assigned_to?: string | null;
  status: LeadStatus;
  expected_value?: number | null;
  probability?: number | null;
  next_followup_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: number;
  customer_id: number;
  sender: string;
  message: string;
  ai_response?: string | null;
  created_at: string;
}

export interface ActivityLog {
  id: number;
  customer_id: number;
  activity_type: string;
  description: string;
  created_by?: string | null;
  created_at: string;
}

export interface CRMUpdate {
  id: number;
  customer_id: number;
  last_activity?: string | null;
  last_contact_date?: string | null;
  next_followup_date?: string | null;
  last_updated_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: T[];
}

export interface CustomerProfile {
  customer: Customer;
  leads: Lead[];
  conversations: Conversation[];
  activity_timeline: ActivityLog[];
  crm_update: CRMUpdate | null;
}

export const crmApi = {
  health: async () => (await apiClient.get('/crm/health')).data,

  listCustomers: async (params?: { q?: string; status?: string; page?: number; page_size?: number }) =>
    (await apiClient.get<PaginatedResponse<Customer>>('/crm/customers', { params })).data,

  getCustomer: async (id: number) => (await apiClient.get<Customer>(`/crm/customers/${id}`)).data,

  createCustomer: async (payload: Partial<Customer>) => (await apiClient.post<Customer>('/crm/customers', payload)).data,

  updateCustomer: async (id: number, payload: Partial<Customer>) =>
    (await apiClient.patch<Customer>(`/crm/customers/${id}`, payload)).data,

  deleteCustomer: async (id: number) => (await apiClient.delete(`/crm/customers/${id}`)).data,

  searchCustomers: async (q: string) => (await apiClient.get<Customer[]>(`/crm/customers/search`, { params: { q } })).data,

  getCustomerProfile: async (id: number) => (await apiClient.get<CustomerProfile>(`/crm/customers/${id}/profile`)).data,

  getCustomerTimeline: async (id: number) => (await apiClient.get<ActivityLog[]>(`/crm/customers/${id}/timeline`)).data,

  listLeads: async (params?: { q?: string; status?: string; assigned_to?: string; source?: string; customer_id?: number; page?: number; page_size?: number }) =>
    (await apiClient.get<PaginatedResponse<Lead>>('/crm/leads', { params })).data,

  getLead: async (id: number) => (await apiClient.get<Lead>(`/crm/leads/${id}`)).data,

  createLead: async (payload: Partial<Lead>) => (await apiClient.post<Lead>('/crm/leads', payload)).data,

  updateLead: async (id: number, payload: Partial<Lead>) => (await apiClient.patch<Lead>(`/crm/leads/${id}`, payload)).data,

  deleteLead: async (id: number) => (await apiClient.delete(`/crm/leads/${id}`)).data,

  listConversations: async (customerId?: number) =>
    (await apiClient.get<Conversation[]>('/crm/conversations', { params: customerId ? { customer_id: customerId } : {} })).data,

  addConversation: async (payload: Partial<Conversation>) => (await apiClient.post<Conversation>('/crm/conversations', payload)).data,

  deleteConversation: async (id: number) => (await apiClient.delete(`/crm/conversations/${id}`)).data,

  listActivity: async (customerId?: number) =>
    (await apiClient.get<ActivityLog[]>('/crm/activity', { params: customerId ? { customer_id: customerId } : {} })).data,

  getCRMUpdate: async (customerId: number) => (await apiClient.get<CRMUpdate>(`/crm/updates/${customerId}`)).data,

  getSummary: async () => (await apiClient.get('/crm/summary')).data,
};

export const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

export const formatDate = (value?: string | null) => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};
