# Architecture overview

AI Employee OS is a modular, multi-tenant business workspace. The browser application owns presentation, session-aware navigation, and form interaction. FastAPI owns business rules, authorization, persistence orchestration, integration boundaries, and AI orchestration. PostgreSQL is the system of record.

## Boundary model

`Next.js client -> REST API -> services -> SQLAlchemy repositories/database -> PostgreSQL`

AI requests follow a separate service path: `UI/API request -> AI orchestrator -> specialist selection -> approved domain service context/actions -> OpenAI integration -> persisted activity/audit result`. Specialists never access the database directly; domain services enforce tenant scope and authorization.

## Ownership and conventions

- Every business record belongs to a company (tenant) unless explicitly global.
- API routers translate HTTP only; services own use cases; models describe persistence; schemas describe request/response contracts.
- Frontend feature pages compose reusable layout and UI primitives, while `services/` is the sole HTTP boundary.
- Cross-cutting concerns—configuration, security, logging, error handling, and observability—belong in backend `core/` and frontend `lib/`.
- Keep integrations (email, WhatsApp, calendar, storage, OpenAI) behind service interfaces so they can be stubbed during the prototype.

## Package responsibilities

| Area | Responsibility |
|---|---|
| `frontend/src/app` | App Router routes, route groups, page ownership, layouts |
| `frontend/src/components` | Reusable UI primitives, layouts, and shared application components |
| `frontend/src/services` | Typed API clients grouped by domain |
| `backend/app/routers` | Versioned REST module routing and dependency wiring |
| `backend/app/services` | Domain use cases, authorization checks, external integrations |
| `backend/app/models` / `schemas` | Database entities / external data contracts |
| `backend/app/ai` | Orchestrator, specialist contracts, context and audit policy |
| `database` | Alembic migration and non-production seed ownership |
