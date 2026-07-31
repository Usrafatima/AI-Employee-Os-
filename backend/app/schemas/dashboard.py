from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class KpiCard(BaseModel):
    id: str
    title: str
    value: str
    raw_value: float
    change_percentage: float
    is_positive: bool
    timeframe: str
    icon: str


class DashboardOverview(BaseModel):
    total_revenue: float
    total_customers: int
    active_leads: int
    pending_tasks: int
    ai_employees: int
    new_messages: int
    kpi_cards: List[KpiCard]


class RevenueDataPoint(BaseModel):
    date: str
    revenue: float
    expenses: float
    net_profit: float


class RevenueReportResponse(BaseModel):
    period: str  # daily, weekly, monthly, yearly
    total_revenue: float
    total_expenses: float
    net_profit: float
    growth_rate: float
    chart_data: List[RevenueDataPoint]


class CustomerAnalytics(BaseModel):
    new_customers: int
    returning_customers: int
    growth_rate: float
    distribution: List[dict]
    monthly_trend: List[dict]


class LeadAnalytics(BaseModel):
    total_leads: int
    qualified_leads: int
    converted_leads: int
    lost_leads: int
    conversion_rate: float
    pipeline_stages: List[dict]


class RecentActivity(BaseModel):
    id: str
    type: str  # customer_added, invoice_created, lead_updated, email_sent, meeting_scheduled
    title: str
    description: str
    timestamp: str
    user_or_ai: str
    status: str


class AiInsightItem(BaseModel):
    id: str
    category: str  # revenue_prediction, sales_forecast, customer_trend, recommendation
    title: str
    insight: str
    impact_level: str  # High, Medium, Low
    action_text: Optional[str] = None
    confidence_score: float


class AiInsightsResponse(BaseModel):
    revenue_prediction: str
    sales_forecast: str
    customer_trends: List[str]
    insights: List[AiInsightItem]
