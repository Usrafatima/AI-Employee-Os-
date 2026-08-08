from typing import List, Any, Optional
from pydantic import BaseModel


class ReportFilter(BaseModel):
    report_type: str  # revenue, sales, customer, lead
    timeframe: str  # today, week, month, year, custom
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ReportRow(BaseModel):
    id: str
    date: str
    category: str
    name: str
    amount_or_value: float
    status: str
    details: str


class ReportSummary(BaseModel):
    total_records: int
    total_amount: float
    average_value: float
    top_performing_category: str


class ReportDataResponse(BaseModel):
    title: str
    generated_at: str
    filter: ReportFilter
    summary: ReportSummary
    columns: List[str]
    rows: List[ReportRow]
