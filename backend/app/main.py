from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import Base, engine
from app.routers import (
    ai,
    auth,
    communication,
    crm,
    documents,
    invoices,
    meetings,
    quotations,
    reports,
    dashboard,
    tasks,
    users,
    workflows,
)
from app.services.reminder_scheduler import start_reminder_scheduler

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


@app.on_event("startup")
def on_startup():
    # Dev convenience: create any tables that don't exist yet (no-op for
    # tables already managed by Alembic migrations elsewhere).
    Base.metadata.create_all(bind=engine)
    start_reminder_scheduler()


@app.get("/")
def root():
    return {"message": "AI Employee OS Backend API", "status": "running"}


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# Include v1 REST API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(crm.router, prefix=f"{settings.API_V1_STR}/crm", tags=["CRM"])
app.include_router(quotations.router, prefix=f"{settings.API_V1_STR}/quotations", tags=["Quotations"])
app.include_router(invoices.router, prefix=f"{settings.API_V1_STR}/invoices", tags=["Invoices"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Tasks"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(meetings.router, prefix=f"{settings.API_V1_STR}/meetings", tags=["Meetings"])
app.include_router(workflows.router, prefix=f"{settings.API_V1_STR}/workflows", tags=["Workflows"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Orchestrator"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(communication.router, prefix=f"{settings.API_V1_STR}/communication", tags=["Communication Hub"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard & Analytics"])