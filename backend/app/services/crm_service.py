from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.crm import ActivityLog, CRMUpdate, Conversation, Customer, CustomerStatus, Lead, LeadStatus


class CRMService:
    @staticmethod
    def _serialize_customer(customer: Customer) -> dict[str, Any]:
        return {
            "id": customer.id,
            "full_name": customer.full_name,
            "company_name": customer.company_name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "city": customer.city,
            "country": customer.country,
            "industry": customer.industry,
            "notes": customer.notes,
            "status": customer.status,
            "is_deleted": customer.is_deleted,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
        }

    @staticmethod
    def _create_activity(db: Session, customer_id: int, activity_type: str, description: str, created_by: str = "system") -> ActivityLog:
        activity = ActivityLog(
            customer_id=customer_id,
            activity_type=activity_type,
            description=description,
            created_by=created_by,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    @staticmethod
    def _ensure_crm_update(db: Session, customer_id: int, *, last_activity: str | None = None, last_updated_by: str | None = None, last_contact_date: datetime | None = None, next_followup_date: datetime | None = None) -> CRMUpdate:
        crm_update = db.query(CRMUpdate).filter(CRMUpdate.customer_id == customer_id).first()
        if crm_update is None:
            crm_update = CRMUpdate(customer_id=customer_id)
            db.add(crm_update)

        if last_activity is not None:
            crm_update.last_activity = last_activity
        if last_updated_by is not None:
            crm_update.last_updated_by = last_updated_by
        if last_contact_date is not None:
            crm_update.last_contact_date = last_contact_date
        if next_followup_date is not None:
            crm_update.next_followup_date = next_followup_date

        crm_update.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(crm_update)
        return crm_update

    @staticmethod
    def create_customer(db: Session, payload: dict[str, Any]) -> Customer:
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required.")

        existing = db.query(Customer).filter(Customer.email == email, Customer.is_deleted.is_(False)).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer with this email already exists.")

        duplicate_name = db.query(Customer).filter(
            Customer.full_name == payload.get("full_name"),
            Customer.company_name == payload.get("company_name"),
            Customer.is_deleted.is_(False),
        ).first()
        if duplicate_name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A customer with the same name and company already exists.")

        customer = Customer(**payload)
        db.add(customer)
        db.commit()
        db.refresh(customer)

        CRMService._create_activity(
            db,
            customer.id,
            "Customer Created",
            f"Customer {customer.full_name} was created.",
            created_by="system",
        )
        CRMService._ensure_crm_update(
            db,
            customer.id,
            last_activity="Customer Created",
            last_updated_by="system",
            last_contact_date=customer.created_at,
        )
        return customer

    @staticmethod
    def list_customers(db: Session, *, q: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        query = db.query(Customer).filter(Customer.is_deleted.is_(False))

        if q:
            query = query.filter(
                or_(
                    Customer.full_name.ilike(f"%{q}%"),
                    Customer.email.ilike(f"%{q}%"),
                    Customer.phone.ilike(f"%{q}%"),
                    Customer.company_name.ilike(f"%{q}%"),
                )
            )

        if status:
            query = query.filter(Customer.status == status)

        total = query.count()
        items = query.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "items": [CRMService._serialize_customer(item) for item in items],
        }

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Customer:
        customer = db.query(Customer).filter(Customer.id == customer_id, Customer.is_deleted.is_(False)).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
        return customer

    @staticmethod
    def update_customer(db: Session, customer_id: int, payload: dict[str, Any]) -> Customer:
        customer = CRMService.get_customer(db, customer_id)

        if payload.get("email") and payload["email"] != customer.email:
            existing = db.query(Customer).filter(Customer.email == payload["email"], Customer.id != customer_id, Customer.is_deleted.is_(False)).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer with this email already exists.")

        for field, value in payload.items():
            if value is not None and hasattr(customer, field):
                setattr(customer, field, value)

        db.commit()
        db.refresh(customer)

        CRMService._create_activity(
            db,
            customer.id,
            "Customer Updated",
            f"Customer {customer.full_name} was updated.",
            created_by="system",
        )
        CRMService._ensure_crm_update(
            db,
            customer.id,
            last_activity="Customer Edited",
            last_updated_by="system",
            last_contact_date=customer.updated_at,
        )
        return customer

    @staticmethod
    def delete_customer(db: Session, customer_id: int) -> dict[str, str]:
        customer = CRMService.get_customer(db, customer_id)
        customer.is_deleted = True
        customer.deleted_at = datetime.utcnow()
        db.commit()
        return {"message": "Customer deleted successfully."}

    @staticmethod
    def search_customers(db: Session, q: str) -> list[dict[str, Any]]:
        if not q or not q.strip():
            return []
        customers = (
            db.query(Customer)
            .filter(Customer.is_deleted.is_(False))
            .filter(
                or_(
                    Customer.full_name.ilike(f"%{q.strip()}%"),
                    Customer.email.ilike(f"%{q.strip()}%"),
                    Customer.phone.ilike(f"%{q.strip()}%"),
                    Customer.company_name.ilike(f"%{q.strip()}%"),
                )
            )
            .order_by(Customer.created_at.desc())
            .all()
        )
        return [CRMService._serialize_customer(item) for item in customers]

    @staticmethod
    def customer_profile(db: Session, customer_id: int) -> dict[str, Any]:
        customer = CRMService.get_customer(db, customer_id)
        leads = db.query(Lead).filter(Lead.customer_id == customer_id).order_by(Lead.created_at.desc()).all()
        conversations = db.query(Conversation).filter(Conversation.customer_id == customer_id).order_by(Conversation.created_at.desc()).all()
        activity_timeline = db.query(ActivityLog).filter(ActivityLog.customer_id == customer_id).order_by(ActivityLog.created_at.desc()).all()
        crm_update = db.query(CRMUpdate).filter(CRMUpdate.customer_id == customer_id).first()

        return {
            "customer": CRMService._serialize_customer(customer),
            "leads": [
                {
                    "id": lead.id,
                    "customer_id": lead.customer_id,
                    "title": lead.title,
                    "source": lead.source,
                    "assigned_to": lead.assigned_to,
                    "status": lead.status,
                    "expected_value": lead.expected_value,
                    "probability": lead.probability,
                    "next_followup_date": lead.next_followup_date,
                    "notes": lead.notes,
                    "created_at": lead.created_at,
                    "updated_at": lead.updated_at,
                }
                for lead in leads
            ],
            "conversations": [
                {
                    "id": message.id,
                    "customer_id": message.customer_id,
                    "sender": message.sender,
                    "message": message.message,
                    "ai_response": message.ai_response,
                    "created_at": message.created_at,
                }
                for message in conversations
            ],
            "activity_timeline": [
                {
                    "id": log.id,
                    "customer_id": log.customer_id,
                    "activity_type": log.activity_type,
                    "description": log.description,
                    "created_by": log.created_by,
                    "created_at": log.created_at,
                }
                for log in activity_timeline
            ],
            "crm_update": {
                "id": crm_update.id,
                "customer_id": crm_update.customer_id,
                "last_activity": crm_update.last_activity,
                "last_contact_date": crm_update.last_contact_date,
                "next_followup_date": crm_update.next_followup_date,
                "last_updated_by": crm_update.last_updated_by,
                "created_at": crm_update.created_at,
                "updated_at": crm_update.updated_at,
            } if crm_update else None,
        }

    @staticmethod
    def create_lead(db: Session, payload: dict[str, Any]) -> Lead:
        customer = CRMService.get_customer(db, payload["customer_id"])
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        lead = Lead(**payload)
        db.add(lead)
        db.commit()
        db.refresh(lead)

        CRMService._create_activity(
            db,
            customer.id,
            "Lead Created",
            f"New lead '{lead.title}' was created.",
            created_by=lead.assigned_to or "system",
        )
        CRMService._ensure_crm_update(
            db,
            customer.id,
            last_activity="New Lead",
            last_updated_by=lead.assigned_to or "system",
            last_contact_date=lead.created_at,
            next_followup_date=lead.next_followup_date,
        )
        return lead

    @staticmethod
    def get_lead(db: Session, lead_id: int) -> Lead:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
        return lead

    @staticmethod
    def list_leads(db: Session, *, customer_id: int | None = None, status: str | None = None, assigned_to: str | None = None, source: str | None = None, q: str | None = None, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        query = db.query(Lead)

        if customer_id is not None:
            query = query.filter(Lead.customer_id == customer_id)
        if status:
            query = query.filter(Lead.status == status)
        if assigned_to:
            query = query.filter(Lead.assigned_to.ilike(f"%{assigned_to}%"))
        if source:
            query = query.filter(Lead.source == source)
        if q:
            query = query.filter(or_(Lead.title.ilike(f"%{q}%"), Lead.notes.ilike(f"%{q}%")))

        total = query.count()
        items = query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "items": [
                {
                    "id": item.id,
                    "customer_id": item.customer_id,
                    "title": item.title,
                    "source": item.source,
                    "assigned_to": item.assigned_to,
                    "status": item.status,
                    "expected_value": item.expected_value,
                    "probability": item.probability,
                    "next_followup_date": item.next_followup_date,
                    "notes": item.notes,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in items
            ],
        }

    @staticmethod
    def update_lead(db: Session, lead_id: int, payload: dict[str, Any]) -> Lead:
        lead = CRMService.get_lead(db, lead_id)
        previous_status = lead.status

        if payload.get("customer_id"):
            CRMService.get_customer(db, payload["customer_id"])

        for field, value in payload.items():
            if value is not None and hasattr(lead, field):
                setattr(lead, field, value)

        db.commit()
        db.refresh(lead)

        if previous_status != lead.status:
            CRMService._create_activity(
                db,
                lead.customer_id,
                "Lead Status Changed",
                f"Lead '{lead.title}' status changed from {previous_status} to {lead.status}.",
                created_by=lead.assigned_to or "system",
            )
            CRMService._ensure_crm_update(
                db,
                lead.customer_id,
                last_activity=f"Lead Status Changed: {lead.status}",
                last_updated_by=lead.assigned_to or "system",
                last_contact_date=datetime.utcnow(),
                next_followup_date=lead.next_followup_date,
            )
        else:
            CRMService._create_activity(
                db,
                lead.customer_id,
                "Lead Updated",
                f"Lead '{lead.title}' was updated.",
                created_by=lead.assigned_to or "system",
            )
            CRMService._ensure_crm_update(
                db,
                lead.customer_id,
                last_activity="Lead Updated",
                last_updated_by=lead.assigned_to or "system",
                next_followup_date=lead.next_followup_date,
            )
        return lead

    @staticmethod
    def delete_lead(db: Session, lead_id: int) -> dict[str, str]:
        lead = CRMService.get_lead(db, lead_id)
        db.delete(lead)
        db.commit()
        return {"message": "Lead deleted successfully."}

    @staticmethod
    def add_conversation_message(db: Session, payload: dict[str, Any]) -> Conversation:
        customer = CRMService.get_customer(db, payload["customer_id"])
        message = Conversation(**payload)
        db.add(message)
        db.commit()
        db.refresh(message)

        CRMService._create_activity(
            db,
            customer.id,
            "Conversation Added",
            f"{message.sender.title()} sent a new message.",
            created_by=message.sender,
        )
        CRMService._ensure_crm_update(
            db,
            customer.id,
            last_activity="Conversation Added",
            last_updated_by=message.sender,
            last_contact_date=message.created_at,
        )
        return message

    @staticmethod
    def list_conversations(db: Session, customer_id: int | None = None) -> list[dict[str, Any]]:
        query = db.query(Conversation)
        if customer_id is not None:
            query = query.filter(Conversation.customer_id == customer_id)
        items = query.order_by(Conversation.created_at.desc()).all()
        return [
            {
                "id": item.id,
                "customer_id": item.customer_id,
                "sender": item.sender,
                "message": item.message,
                "ai_response": item.ai_response,
                "created_at": item.created_at,
            }
            for item in items
        ]

    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> dict[str, str]:
        message = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation message not found.")
        db.delete(message)
        db.commit()
        return {"message": "Conversation message deleted successfully."}

    @staticmethod
    def customer_timeline(db: Session, customer_id: int) -> list[dict[str, Any]]:
        CRMService.get_customer(db, customer_id)
        logs = db.query(ActivityLog).filter(ActivityLog.customer_id == customer_id).order_by(ActivityLog.created_at.desc()).all()
        return [
            {
                "id": log.id,
                "customer_id": log.customer_id,
                "activity_type": log.activity_type,
                "description": log.description,
                "created_by": log.created_by,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    @staticmethod
    def get_crm_update(db: Session, customer_id: int) -> CRMUpdate:
        crm_update = db.query(CRMUpdate).filter(CRMUpdate.customer_id == customer_id).first()
        if not crm_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CRM update not found for customer.")
        return crm_update

    @staticmethod
    def list_activity_logs(db: Session, customer_id: int | None = None) -> list[dict[str, Any]]:
        query = db.query(ActivityLog)
        if customer_id is not None:
            query = query.filter(ActivityLog.customer_id == customer_id)
        items = query.order_by(ActivityLog.created_at.desc()).all()
        return [
            {
                "id": item.id,
                "customer_id": item.customer_id,
                "activity_type": item.activity_type,
                "description": item.description,
                "created_by": item.created_by,
                "created_at": item.created_at,
            }
            for item in items
        ]

    @staticmethod
    def get_customer_sales_summary(db: Session) -> dict[str, Any]:
        total_customers = db.query(Customer).filter(Customer.is_deleted.is_(False)).count()
        active_customers = db.query(Customer).filter(Customer.is_deleted.is_(False), Customer.status == CustomerStatus.ACTIVE.value).count()
        total_leads = db.query(Lead).count()
        total_active_leads = db.query(Lead).filter(Lead.status.in_([LeadStatus.NEW.value, LeadStatus.CONTACTED.value, LeadStatus.QUALIFIED.value, LeadStatus.PROPOSAL_SENT.value, LeadStatus.NEGOTIATION.value])).count()
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_leads": total_leads,
            "active_leads": total_active_leads,
        }
