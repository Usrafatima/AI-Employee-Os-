import { apiClient } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/crm-api';

export type QuotationStatus =
  | 'draft'
  | 'sent'
  | 'accepted'
  | 'rejected'
  | 'converted'
  | 'cancelled';

export type InvoiceStatus = 'draft' | 'sent' | 'partially_paid' | 'paid' | 'cancelled';
export type DiscountType = 'percentage' | 'fixed';
export type PaymentMethod = 'cash' | 'bank_transfer' | 'card' | 'online';

export const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'cash', label: 'Cash' },
  { value: 'card', label: 'Card' },
  { value: 'online', label: 'Online Payment' },
];

export interface FinanceCustomer {
  id: number;
  full_name: string;
  company_name?: string | null;
  email: string;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface DocumentItem {
  id: number;
  position: number;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface DocumentItemInput {
  description: string;
  quantity: number | string;
  unit_price: number | string;
}

interface DocumentBase {
  id: number;
  customer_id: number;
  customer?: FinanceCustomer | null;
  issue_date: string;
  currency: string;
  discount_type: DiscountType;
  discount_value: number;
  tax_rate: number;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  grand_total: number;
  notes?: string | null;
  terms?: string | null;
  items: DocumentItem[];
  sent_at?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Quotation extends DocumentBase {
  quotation_number: string;
  status: QuotationStatus;
  valid_until?: string | null;
}

export interface Invoice extends DocumentBase {
  invoice_number: string;
  status: InvoiceStatus;
  due_date?: string | null;
  quotation_id?: number | null;
  amount_paid: number;
  balance_due: number;
}

export interface Receipt {
  id: number;
  receipt_number: string;
  payment_id: number;
  balance_after: number;
  issued_at: string;
  created_at: string;
}

export interface ReceiptDetail extends Receipt {
  payment?: Payment | null;
  invoice_id?: number | null;
  invoice_number?: string | null;
  customer?: FinanceCustomer | null;
}

export interface Payment {
  id: number;
  invoice_id: number;
  amount: number;
  method: PaymentMethod;
  reference?: string | null;
  payment_date: string;
  notes?: string | null;
  recorded_by?: string | null;
  created_at: string;
  receipt?: Receipt | null;
}

export interface FinanceSummary {
  currency: string;
  total_quotations: number;
  quotations_by_status: Record<string, number>;
  total_quoted_value: number;
  total_invoices: number;
  invoices_by_status: Record<string, number>;
  total_invoiced_value: number;
  total_collected: number;
  total_outstanding: number;
  paid_invoices: number;
  unpaid_invoices: number;
  partially_paid_invoices: number;
}

export interface FinanceSettings {
  currency_code: string;
  currency_symbol: string;
  company_name: string;
  company_address: string;
  company_email: string;
  company_phone: string;
  company_website: string;
  document_terms: string;
}

export interface DocumentPayload {
  customer_id: number;
  items: DocumentItemInput[];
  discount_type: DiscountType;
  discount_value: number | string;
  tax_rate: number | string;
  notes?: string | null;
  terms?: string | null;
  issue_date?: string | null;
}

export interface QuotationPayload extends DocumentPayload {
  valid_until?: string | null;
}

export interface InvoicePayload extends DocumentPayload {
  due_date?: string | null;
  quotation_id?: number | null;
}

export interface SendResult {
  sent: boolean;
  to_email: string;
  subject: string;
  document_number: string;
  email_log_id?: number | null;
}

type ListParams = { q?: string; status?: string; customer_id?: number; page?: number; page_size?: number };

export const financeApi = {
  getSummary: async () => (await apiClient.get<FinanceSummary>('/finance/summary')).data,
  getSettings: async () => (await apiClient.get<FinanceSettings>('/finance/settings')).data,

  // --- Quotations ---
  listQuotations: async (params?: ListParams) =>
    (await apiClient.get<PaginatedResponse<Quotation>>('/quotations', { params })).data,
  getQuotation: async (id: number) => (await apiClient.get<Quotation>(`/quotations/${id}`)).data,
  createQuotation: async (payload: QuotationPayload) =>
    (await apiClient.post<Quotation>('/quotations', payload)).data,
  updateQuotation: async (id: number, payload: Partial<QuotationPayload>) =>
    (await apiClient.patch<Quotation>(`/quotations/${id}`, payload)).data,
  setQuotationStatus: async (id: number, status: QuotationStatus) =>
    (await apiClient.patch<Quotation>(`/quotations/${id}/status`, { status })).data,
  cancelQuotation: async (id: number) => (await apiClient.delete<Quotation>(`/quotations/${id}`)).data,
  convertQuotation: async (id: number, payload?: { due_date?: string | null }) =>
    (await apiClient.post<Invoice>(`/quotations/${id}/invoice`, payload ?? {})).data,
  sendQuotation: async (id: number, payload?: { to_email?: string; subject?: string; message?: string }) =>
    (await apiClient.post<SendResult>(`/quotations/${id}/send`, payload ?? {})).data,

  // --- Invoices ---
  listInvoices: async (params?: ListParams) =>
    (await apiClient.get<PaginatedResponse<Invoice>>('/invoices', { params })).data,
  getInvoice: async (id: number) => (await apiClient.get<Invoice>(`/invoices/${id}`)).data,
  createInvoice: async (payload: InvoicePayload) =>
    (await apiClient.post<Invoice>('/invoices', payload)).data,
  updateInvoice: async (id: number, payload: Partial<InvoicePayload>) =>
    (await apiClient.patch<Invoice>(`/invoices/${id}`, payload)).data,
  setInvoiceStatus: async (id: number, status: InvoiceStatus) =>
    (await apiClient.patch<Invoice>(`/invoices/${id}/status`, { status })).data,
  cancelInvoice: async (id: number) => (await apiClient.delete<Invoice>(`/invoices/${id}`)).data,
  listInvoicePayments: async (id: number) =>
    (await apiClient.get<PaginatedResponse<Payment>>(`/invoices/${id}/payments`)).data,
  sendInvoice: async (id: number, payload?: { to_email?: string; subject?: string; message?: string }) =>
    (await apiClient.post<SendResult>(`/invoices/${id}/send`, payload ?? {})).data,

  // --- Payments & receipts ---
  recordPayment: async (payload: {
    invoice_id: number;
    amount: number | string;
    method: PaymentMethod;
    reference?: string | null;
    payment_date?: string | null;
    notes?: string | null;
  }) => (await apiClient.post<Payment>('/payments', payload)).data,
  listPayments: async (params?: { invoice_id?: number; method?: string; page?: number; page_size?: number }) =>
    (await apiClient.get<PaginatedResponse<Payment>>('/payments', { params })).data,
  listReceipts: async (params?: { page?: number; page_size?: number }) =>
    (await apiClient.get<PaginatedResponse<Receipt>>('/receipts', { params })).data,
  getReceipt: async (id: number) => (await apiClient.get<ReceiptDetail>(`/receipts/${id}`)).data,
  sendReceipt: async (id: number, payload?: { to_email?: string }) =>
    (await apiClient.post<SendResult>(`/receipts/${id}/send`, payload ?? {})).data,
};

/**
 * Open a document PDF in a new tab.
 *
 * Fetched through the API client rather than a plain link so the request
 * carries the bearer token, then handed to the browser as a blob URL.
 */
export const openDocumentPdf = async (path: string, filename: string) => {
  const response = await apiClient.get(path, { responseType: 'blob' });
  const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const opened = window.open(url, '_blank');
  if (!opened) {
    // Popup blocked — fall back to a direct download.
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  }
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
};

/** Extract a readable message from a FastAPI error response. */
export const financeErrorMessage = (error: unknown, fallback = 'Something went wrong.'): string => {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { loc?: unknown[]; msg?: string } | undefined;
    if (first?.msg) {
      const field = Array.isArray(first.loc) ? first.loc.slice(1).join('.') : '';
      return field ? `${field}: ${first.msg}` : first.msg;
    }
  }
  return fallback;
};
