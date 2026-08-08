from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
)


class CompanyService:

    def __init__(self, db: Session):
        self.db = db

    def create_company(
        self,
        company: CompanyCreate
    ):

        db_company = Company(
            company_name=company.company_name,
            industry=company.industry,
            website=company.website,
            address=company.address,
        )

        self.db.add(db_company)
        self.db.commit()
        self.db.refresh(db_company)

        return db_company

    def get_company(
        self,
        company_id: int
    ):

        return (
            self.db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

    def update_company(
        self,
        company_id: int,
        company: CompanyUpdate
    ):

        db_company = self.get_company(company_id)

        if not db_company:
            return None

        update_data = company.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_company, key, value)

        self.db.commit()
        self.db.refresh(db_company)

        return db_company

    def delete_company(
        self,
        company_id: int
    ):

        company = (
            self.db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

        if not company:
            return None

        self.db.delete(company)
        self.db.commit()

        return {
            "message": "Company deleted successfully"
        }
    def get_all_companies(self):

        return (
           self.db.query(Company)
           .all()
    )