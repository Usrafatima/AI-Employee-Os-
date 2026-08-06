import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});

export interface KpiCardData {
  id: string;
  title: string;
  value: string;
  raw_value: number;
  change_percentage: number;
  is_positive: boolean;
  timeframe: string;
  icon: string;
}

export interface DashboardOverviewData {
  total_revenue: number;
  total_customers: number;
  active_leads: number;
  pending_tasks: number;
  ai_employees: number;
  new_messages: number;
  kpi_cards: KpiCardData[];
}

export interface RevenueDataPoint {
  date: string;
  revenue: number;
  expenses: number;
  net_profit: number;
}

export interface RevenueAnalyticsData {
  period: string;
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  growth_rate: number;
  chart_data: RevenueDataPoint[];
}

export interface CustomerAnalyticsData {
  new_customers: number;
  returning_customers: number;
  growth_rate: number;
  distribution: { category: string; count: number; percentage: number }[];
  monthly_trend: { month: string; new: number; returning: number }[];
}

export interface LeadAnalyticsData {
  total_leads: number;
  qualified_leads: number;
  converted_leads: number;
  lost_leads: number;
  conversion_rate: number;
  pipeline_stages: { stage: string; count: number; value: string }[];
}

export interface RecentActivityData {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  user_or_ai: string;
  status: string;
}

export interface AiInsightItemData {
  id: string;
  category: string;
  title: string;
  insight: string;
  impact_level: string;
  action_text?: string;
  confidence_score: number;
}

export interface AiInsightsData {
  revenue_prediction: string;
  sales_forecast: string;
  customer_trends: string[];
  insights: AiInsightItemData[];
}

export interface ReportRowData {
  id: string;
  date: string;
  category: string;
  name: string;
  amount_or_value: number;
  status: string;
  details: string;
}

export interface ReportDataResponse {
  title: string;
  generated_at: string;
  filter: {
    report_type: string;
    timeframe: string;
  };
  summary: {
    total_records: number;
    total_amount: number;
    average_value: number;
    top_performing_category: string;
  };
  columns: string[];
  rows: ReportRowData[];
}

// Fallback Mock Datasets for Seamless Client Preview
const MOCK_OVERVIEW: DashboardOverviewData = {
  total_revenue: 148500.0,
  total_customers: 1240,
  active_leads: 320,
  pending_tasks: 18,
  ai_employees: 6,
  new_messages: 42,
  kpi_cards: [
    {
      id: 'revenue',
      title: 'Total Revenue',
      value: '$148,500.00',
      raw_value: 148500,
      change_percentage: 14.2,
      is_positive: true,
      timeframe: 'vs previous month',
      icon: 'dollar-sign',
    },
    {
      id: 'leads',
      title: 'Active Leads',
      value: '320',
      raw_value: 320,
      change_percentage: 8.7,
      is_positive: true,
      timeframe: 'vs previous month',
      icon: 'target',
    },
    {
      id: 'customers',
      title: 'Total Customers',
      value: '1,240',
      raw_value: 1240,
      change_percentage: 12.5,
      is_positive: true,
      timeframe: 'vs previous month',
      icon: 'users',
    },
    {
      id: 'sales',
      title: 'Completed Sales',
      value: '184',
      raw_value: 184,
      change_percentage: 18.9,
      is_positive: true,
      timeframe: 'vs previous month',
      icon: 'shopping-bag',
    },
    {
      id: 'tasks',
      title: 'Pending Tasks',
      value: '18',
      raw_value: 18,
      change_percentage: -5.3,
      is_positive: true,
      timeframe: '4 urgent AI tasks',
      icon: 'check-square',
    },
    {
      id: 'ai_requests',
      title: 'AI Employee Actions',
      value: '4,850',
      raw_value: 4850,
      change_percentage: 24.8,
      is_positive: true,
      timeframe: '99.4% execution accuracy',
      icon: 'bot',
    },
  ],
};

const MOCK_REVENUE: RevenueAnalyticsData = {
  period: 'monthly',
  total_revenue: 291900.0,
  total_expenses: 110922.0,
  net_profit: 180978.0,
  growth_rate: 16.4,
  chart_data: [
    { date: 'Jan', revenue: 12500, expenses: 4750, net_profit: 7750 },
    { date: 'Feb', revenue: 14200, expenses: 5396, net_profit: 8804 },
    { date: 'Mar', revenue: 15800, expenses: 6004, net_profit: 9796 },
    { date: 'Apr', revenue: 18900, expenses: 7182, net_profit: 11718 },
    { date: 'May', revenue: 21400, expenses: 8132, net_profit: 13268 },
    { date: 'Jun', revenue: 24000, expenses: 9120, net_profit: 14880 },
    { date: 'Jul', revenue: 22800, expenses: 8664, net_profit: 14136 },
    { date: 'Aug', revenue: 26500, expenses: 10070, net_profit: 16430 },
    { date: 'Sep', revenue: 29100, expenses: 11058, net_profit: 18042 },
    { date: 'Oct', revenue: 31400, expenses: 11932, net_profit: 19468 },
    { date: 'Nov', revenue: 34800, expenses: 13224, net_profit: 21576 },
    { date: 'Dec', revenue: 38500, expenses: 14630, net_profit: 23870 },
  ],
};

const MOCK_CUSTOMERS: CustomerAnalyticsData = {
  new_customers: 340,
  returning_customers: 900,
  growth_rate: 12.5,
  distribution: [
    { category: 'Enterprise', count: 180, percentage: 14.5 },
    { category: 'Mid-Market', count: 420, percentage: 33.9 },
    { category: 'Small Business', count: 520, percentage: 41.9 },
    { category: 'Freelancers', count: 120, percentage: 9.7 },
  ],
  monthly_trend: [
    { month: 'Jan', new: 45, returning: 120 },
    { month: 'Feb', new: 52, returning: 135 },
    { month: 'Mar', new: 61, returning: 150 },
    { month: 'Apr', new: 74, returning: 165 },
    { month: 'May', new: 88, returning: 180 },
    { month: 'Jun', new: 95, returning: 200 },
  ],
};

const MOCK_LEADS: LeadAnalyticsData = {
  total_leads: 320,
  qualified_leads: 195,
  converted_leads: 98,
  lost_leads: 27,
  conversion_rate: 30.6,
  pipeline_stages: [
    { stage: 'New Inquiry', count: 85, value: '$125,000' },
    { stage: 'Discovery Call', count: 68, value: '$198,000' },
    { stage: 'Proposal Sent', count: 42, value: '$154,000' },
    { stage: 'Negotiation', count: 27, value: '$112,000' },
    { stage: 'Won / Closed', count: 98, value: '$380,000' },
  ],
};

const MOCK_ACTIVITIES: RecentActivityData[] = [
  {
    id: 'act-1',
    type: 'invoice_created',
    title: 'Invoice #INV-2026-089 Generated',
    description: 'AI Finance Assistant created invoice for Acme Corp ($14,500.00)',
    timestamp: '12 mins ago',
    user_or_ai: 'AI Finance Assistant',
    status: 'completed',
  },
  {
    id: 'act-2',
    type: 'customer_added',
    title: 'New Enterprise Lead Onboarded',
    description: 'TechCorp Global added to CRM with 50 license inquiry',
    timestamp: '45 mins ago',
    user_or_ai: 'AI Sales Manager',
    status: 'completed',
  },
  {
    id: 'act-3',
    type: 'email_sent',
    title: 'Quotation Follow-Up Sent',
    description: 'Automated smart email follow-up sent to John Doe (Apex Logistics)',
    timestamp: '1 hour ago',
    user_or_ai: 'AI Executive Assistant',
    status: 'completed',
  },
  {
    id: 'act-4',
    type: 'meeting_scheduled',
    title: 'Demo Meeting Scheduled',
    description: 'Meeting booked with Nexus Systems for Friday at 3:00 PM',
    timestamp: '2 hours ago',
    user_or_ai: 'AI Assistant',
    status: 'scheduled',
  },
  {
    id: 'act-5',
    type: 'lead_updated',
    title: 'Lead Qualified to Negotiation Stage',
    description: 'BioHealth Ltd moved to Negotiation stage ($85,000 contract)',
    timestamp: '4 hours ago',
    user_or_ai: 'Sales Team',
    status: 'completed',
  },
];

const MOCK_INSIGHTS: AiInsightsData = {
  revenue_prediction:
    'Projected Next Quarter Revenue: $182,400 (+22.8% QoQ growth based on current lead velocity)',
  sales_forecast:
    'High probability of closing 14 Enterprise proposals in the next 14 days ($245,000 pipeline)',
  customer_trends: [
    '42% increase in inbound requests for AI Finance Assistant automation',
    'Average deal size increased by 18.5% following custom quotation PDF integration',
    'WhatsApp response automation boosted customer retention by 15.2%',
  ],
  insights: [
    {
      id: 'ins-1',
      category: 'revenue_prediction',
      title: 'Q3 Revenue Target Acceleration',
      insight:
        'AI Employee OS has processed 24% more automated quotations this month. Recommend increasing ad budget on Enterprise tier.',
      impact_level: 'High',
      action_text: 'Optimize Sales Pipeline',
      confidence_score: 0.94,
    },
    {
      id: 'ins-2',
      category: 'sales_forecast',
      title: 'Lead Conversion Bottleneck Detected',
      insight:
        'Discovery calls are pending for 12 leads for more than 48 hours. Trigger AI Executive Assistant auto-reminder.',
      impact_level: 'High',
      action_text: 'Trigger Follow-Up Bot',
      confidence_score: 0.89,
    },
    {
      id: 'ins-3',
      category: 'customer_trend',
      title: 'High Demand for Pro Tier',
      insight:
        'Small Business segment accounts for 41.9% of growth. Recommend offering annual billing discounts.',
      impact_level: 'Medium',
      action_text: 'Launch Promotion',
      confidence_score: 0.91,
    },
  ],
};

export async function fetchDashboardOverview(timeframe: string = 'month'): Promise<DashboardOverviewData> {
  try {
    const res = await apiClient.get<DashboardOverviewData>(`/dashboard/overview?timeframe=${timeframe}`);
    return res.data;
  } catch {
    return MOCK_OVERVIEW;
  }
}

export async function fetchRevenueAnalytics(period: string = 'monthly'): Promise<RevenueAnalyticsData> {
  try {
    const res = await apiClient.get<RevenueAnalyticsData>(`/dashboard/revenue?period=${period}`);
    return res.data;
  } catch {
    return MOCK_REVENUE;
  }
}

export async function fetchCustomerAnalytics(): Promise<CustomerAnalyticsData> {
  try {
    const res = await apiClient.get<CustomerAnalyticsData>('/dashboard/customers');
    return res.data;
  } catch {
    return MOCK_CUSTOMERS;
  }
}

export async function fetchLeadAnalytics(): Promise<LeadAnalyticsData> {
  try {
    const res = await apiClient.get<LeadAnalyticsData>('/dashboard/leads');
    return res.data;
  } catch {
    return MOCK_LEADS;
  }
}

export async function fetchRecentActivities(): Promise<RecentActivityData[]> {
  try {
    const res = await apiClient.get<RecentActivityData[]>('/dashboard/activities');
    return res.data;
  } catch {
    return MOCK_ACTIVITIES;
  }
}

export async function fetchAiInsights(): Promise<AiInsightsData> {
  try {
    const res = await apiClient.get<AiInsightsData>('/dashboard/insights');
    return res.data;
  } catch {
    return MOCK_INSIGHTS;
  }
}

export async function fetchReportData(reportType: string, timeframe: string): Promise<ReportDataResponse> {
  try {
    const res = await apiClient.get<ReportDataResponse>(`/reports/generate?report_type=${reportType}&timeframe=${timeframe}`);
    return res.data;
  } catch {
    return {
      title: `${reportType.toUpperCase()} Executive Summary Report`,
      generated_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
      filter: { report_type: reportType, timeframe },
      summary: {
        total_records: 5,
        total_amount: 86400.0,
        average_value: 17280.0,
        top_performing_category: 'Enterprise Subscriptions',
      },
      columns: ['ID', 'Date', 'Category', 'Customer / Subject', 'Value ($)', 'Status', 'AI Employee / Notes'],
      rows: [
        { id: 'REP-101', date: '2026-07-29', category: 'Enterprise', name: 'TechCorp Global', amount_or_value: 38000.0, status: 'Completed', details: 'AI Sales Manager' },
        { id: 'REP-102', date: '2026-07-28', category: 'Pro Plan', name: 'Apex Logistics', amount_or_value: 14500.0, status: 'Completed', details: 'AI Finance Assistant' },
        { id: 'REP-103', date: '2026-07-27', category: 'Add-On Module', name: 'BioHealth Ltd', "amount_or_value": 9800.0, status: 'Completed', details: 'WhatsApp AI Engine' },
        { id: 'REP-104', date: '2026-07-26', category: 'Pro Plan', name: 'Nexus Systems', amount_or_value: 12600.0, status: 'Pending', details: 'AI Executive Assistant' },
        { id: 'REP-105', date: '2026-07-25', category: 'Consulting', name: 'Starlight Media', amount_or_value: 11500.0, status: 'Completed', details: 'Custom AI Workflow' },
      ],
    };
  }
}
