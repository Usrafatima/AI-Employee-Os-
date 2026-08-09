"""Finance overview endpoints.

Exposes the module's aggregates so the Dashboard module can surface finance
KPIs without querying finance tables directly, and reports the branding /
currency configuration the frontend needs to render amounts consistently with
the generated PDFs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import CurrentUser, get_current_user
from app.database.session import get_db
from app.schemas.finance import FinanceSummaryResponse
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/health")
def get_finance_status():
    return {"module": "Finance", "status": "active"}


@router.get("/summary", response_model=FinanceSummaryResponse)
def get_finance_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Revenue, outstanding balance and document counts by status."""
    return FinanceService.get_finance_summary(db)


@router.get("/settings", response_model=dict)
def get_finance_settings(current_user: CurrentUser = Depends(get_current_user)):
    """Currency and company branding applied to generated documents."""
    return {
        "currency_code": settings.CURRENCY_CODE,
        "currency_symbol": settings.CURRENCY_SYMBOL,
        "company_name": settings.COMPANY_NAME,
        "company_address": settings.COMPANY_ADDRESS,
        "company_email": settings.COMPANY_EMAIL,
        "company_phone": settings.COMPANY_PHONE,
        "company_website": settings.COMPANY_WEBSITE,
        "document_terms": settings.DOCUMENT_TERMS,
    }
