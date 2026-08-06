from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
)
from app.services.company_service import CompanyService

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.post(
    "/",
    response_model=CompanyResponse,
)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
):
    service = CompanyService(db)

    return service.create_company(company)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    service = CompanyService(db)

    return service.get_company(company_id)


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
)
def update_company(
    company_id: int,
    company: CompanyUpdate,
    db: Session = Depends(get_db),
):
    service = CompanyService(db)

    return service.update_company(
        company_id,
        company,
    )
@router.get(
    "/",
    response_model=list[CompanyResponse],
)
def get_all_companies(
    db: Session = Depends(get_db),
):
    service = CompanyService(db)

    return service.get_all_companies()

@router.delete(
    "/{company_id}"
)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
):
    service = CompanyService(db)

    result = service.delete_company(company_id)

    if not result:
        return {
            "message": "Company not found"
        }
   
    return result