from typing import Optional
from fastapi import APIRouter, Query
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/generate")
def generate_report(
    report_type: str = Query("revenue", description="Type of report: revenue, sales, customer, lead"),
    timeframe: str = Query("month", description="Timeframe: today, week, month, year, custom"),
):
    """
    FR-9: Generate custom report (Revenue, Sales, Customer, Lead Reports) with summary metrics.
    """
    return DashboardService.generate_report_data(report_type=report_type, timeframe=timeframe)


@router.get("/export")
def export_report_metadata(
    report_type: str = Query("revenue"),
    format: str = Query("pdf", description="Export format: pdf or excel"),
    timeframe: str = Query("month"),
):
    """
    FR-9: Export metadata endpoint.
    """
    data = DashboardService.generate_report_data(report_type=report_type, timeframe=timeframe)
    return {
        "status": "ready",
        "format": format,
        "filename": f"AI_Employee_OS_{report_type}_report_{timeframe}.{format}",
        "report_data": data,
    }
