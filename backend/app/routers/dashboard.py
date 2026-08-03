from typing import Optional
from fastapi import APIRouter, Query
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(
    timeframe: Optional[str] = Query("month", description="Timeframe: today, week, month, year, custom")
):
    """
    FR-1 & FR-2: Display Total Revenue, Customers, Active Leads, Tasks, AI Employees, and KPI cards.
    """
    return DashboardService.get_overview(timeframe=timeframe)


@router.get("/revenue")
def get_revenue_analytics(
    period: Optional[str] = Query("monthly", description="Period: daily, weekly, monthly, yearly")
):
    """
    FR-3: Revenue Report & Line Chart data (Daily, Weekly, Monthly, Yearly).
    """
    return DashboardService.get_revenue_analytics(period=period)


@router.get("/customers")
def get_customer_analytics():
    """
    FR-4: Customer Analytics (New, Returning, Customer Growth, Distribution).
    """
    return DashboardService.get_customer_analytics()


@router.get("/leads")
def get_lead_analytics():
    """
    FR-5: Lead Analytics (Total, Qualified, Converted, Lost, Funnel Pipeline Chart).
    """
    return DashboardService.get_lead_analytics()


@router.get("/activities")
def get_recent_activities():
    """
    FR-7: Recent Activities Timeline (Customer Added, Invoice Created, Lead Updated, Email Sent, Meeting Scheduled).
    """
    return DashboardService.get_recent_activities()


@router.get("/insights")
def get_ai_insights():
    """
    FR-6: AI Insights (Revenue Prediction, Sales Forecast, Customer Trends, AI Recommendations).
    """
    return DashboardService.get_ai_insights()
