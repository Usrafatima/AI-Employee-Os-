from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.crm import (
    ActivityLogResponse,
    CRMUpdateResponse,
    ConversationCreate,
    ConversationResponse,
    CustomerCreate,
    CustomerProfileResponse,
    CustomerResponse,
    CustomerUpdate,
    LeadCreate,
    LeadResponse,
    LeadUpdate,
)
from app.services.crm_service import CRMService

router = APIRouter()


@router.get("/health")
def get_crm_status():
    return {"module": "CRM", "status": "active"}


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = CRMService.create_customer(db, payload.model_dump())
    return customer


@router.get("/customers", response_model=dict)
def list_customers(
    q: Optional[str] = Query(default=None, description="Search by name, email, phone, or company"),
    status: Optional[str] = Query(default=None, description="Filter by customer status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return CRMService.list_customers(db, q=q, status=status, page=page, page_size=page_size)


@router.get("/customers/search", response_model=list[CustomerResponse])
def search_customers(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return CRMService.search_customers(db, q)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return CRMService.get_customer(db, customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    return CRMService.update_customer(db, customer_id, payload.model_dump(exclude_unset=True))


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    return CRMService.delete_customer(db, customer_id)


@router.get("/customers/{customer_id}/profile", response_model=CustomerProfileResponse)
def customer_profile(customer_id: int, db: Session = Depends(get_db)):
    return CRMService.customer_profile(db, customer_id)


@router.get("/customers/{customer_id}/timeline", response_model=list[ActivityLogResponse])
def customer_timeline(customer_id: int, db: Session = Depends(get_db)):
    return CRMService.customer_timeline(db, customer_id)


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    return CRMService.create_lead(db, payload.model_dump())


@router.get("/leads", response_model=dict)
def list_leads(
    q: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    customer_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return CRMService.list_leads(db, q=q, status=status, assigned_to=assigned_to, source=source, customer_id=customer_id, page=page, page_size=page_size)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return CRMService.get_lead(db, lead_id)


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    return CRMService.update_lead(db, lead_id, payload.model_dump(exclude_unset=True))


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    return CRMService.delete_lead(db, lead_id)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def add_conversation_message(payload: ConversationCreate, db: Session = Depends(get_db)):
    return CRMService.add_conversation_message(db, payload.model_dump())


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(customer_id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    return CRMService.list_conversations(db, customer_id=customer_id)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    return CRMService.delete_conversation(db, conversation_id)


@router.get("/activity", response_model=list[ActivityLogResponse])
def list_activity(customer_id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    return CRMService.list_activity_logs(db, customer_id=customer_id)


@router.get("/summary", response_model=dict)
def crm_summary(db: Session = Depends(get_db)):
    return CRMService.get_customer_sales_summary(db)


@router.get("/updates/{customer_id}", response_model=CRMUpdateResponse)
def get_customer_crm_update(customer_id: int, db: Session = Depends(get_db)):
    return CRMService.get_crm_update(db, customer_id)
