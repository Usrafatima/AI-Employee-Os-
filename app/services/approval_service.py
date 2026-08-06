from datetime import datetime

from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.schemas.approval import ApprovalCreate


class ApprovalService:

    def __init__(self, db: Session):
        self.db = db

    def create_request(
        self,
        data: ApprovalCreate,
        user_id: int,
    ):

        approval = Approval(
            request_type=data.request_type,
            reference_id=data.reference_id,
            message=data.message,
            requested_by=user_id,
        )

        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)

        return approval

    def get_all(self):
        return self.db.query(Approval).all()

    def approve(
        self,
        approval_id: int,
        admin_id: int,
    ):

        approval = (
            self.db.query(Approval)
            .filter(Approval.id == approval_id)
            .first()
        )

        if not approval:
            return None

        approval.status = "approved"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def reject(
        self,
        approval_id: int,
        admin_id: int,
    ):

        approval = (
            self.db.query(Approval)
            .filter(Approval.id == approval_id)
            .first()
        )

        if not approval:
            return None

        approval.status = "rejected"
        approval.approved_by = admin_id
        approval.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(approval)

        return approval