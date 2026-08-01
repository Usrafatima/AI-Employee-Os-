from pydantic import BaseModel


class CompanyCreate(BaseModel):
    company_name: str
    industry: str | None = None
    website: str | None = None
    address: str | None = None


class CompanyUpdate(BaseModel):
    company_name: str | None = None
    industry: str | None = None
    website: str | None = None
    address: str | None = None


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    industry: str | None = None
    website: str | None = None
    address: str | None = None

    class Config:
        from_attributes = True