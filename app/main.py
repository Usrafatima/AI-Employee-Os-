from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    users,
    password_reset,
    company,
    approval,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# CORS Middleware Configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    return {
        "message": "AI Employee OS Backend API",
        "status": "running",
    }


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


# ===========================
# Routers
# ===========================

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"],
)

app.include_router(
    password_reset.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["Password Reset"],
)


app.include_router(
    company.router,
    prefix=f"{settings.API_V1_STR}/companies",
    tags=["Company"],
)

app.include_router(
    approval.router,
    prefix=f"{settings.API_V1_STR}/approvals",
    tags=["Admin Approval"],
)
# ===========================
# Other modules (Temporary Disabled)
# Uncomment when those routers are added
# ===========================

# app.include_router(crm.router, prefix=f"{settings.API_V1_STR}/crm", tags=["CRM"])
# app.include_router(quotations.router, prefix=f"{settings.API_V1_STR}/quotations", tags=["Quotations"])
# app.include_router(invoices.router, prefix=f"{settings.API_V1_STR}/invoices", tags=["Invoices"])
# app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Tasks"])
# app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
# app.include_router(meetings.router, prefix=f"{settings.API_V1_STR}/meetings", tags=["Meetings"])
# app.include_router(workflows.router, prefix=f"{settings.API_V1_STR}/workflows", tags=["Workflows"])
# app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Orchestrator"])
# app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])


