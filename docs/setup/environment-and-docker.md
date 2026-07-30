# Environment and Docker plan

No environment or Docker configuration is created at this phase. Store local secrets outside version control and provide a future `.env.example` containing variable names only.

## Required environment-variable categories

| Area | Required variables/purpose |
|---|---|
| Frontend | Public API base URL, application base URL, deployment environment, client-visible feature flags only |
| Backend | Environment name, API base/path settings, CORS origins, logging level, trusted hosts, secret/signing material |
| Database | PostgreSQL host, port, database name, user, password, and a complete connection URL for migrations/runtime |
| Authentication | Auth provider/client identifiers and secrets, session/JWT signing secret, token issuer/audience/expiry, callback URLs |
| AI | OpenAI API key, model selection, organization/project identifiers if used, request timeout, usage/cost limits |
| Email | SMTP/provider host, port, credentials, TLS mode, default sender/reply-to addresses |
| Optional integrations | Object-storage credentials/bucket, WhatsApp provider credentials, calendar provider credentials, webhook signing secrets |

Secrets must be injected by the deployment platform or local ignored files, never committed, logged, exposed to the browser, or included in client bundles.

## Docker topology

The future Compose deployment has three independent services: `frontend` (Next.js), `backend` (FastAPI), and `postgres` (PostgreSQL with a named persistent volume). The frontend talks to the backend through an internal service URL at runtime; browsers use the public API URL. The backend alone receives database credentials. Health checks should gate dependent startup, and migration execution should be a deliberate release step rather than an implicit side effect of every replica starting.

Container concerns to decide before implementation: development hot reload versus production images, network naming, port exposure, persistent-volume backup policy, secret injection method, non-root processes, health endpoints, and log collection.
