# Backend and AI plan

## FastAPI layering

| Directory | Responsibility |
|---|---|
| `app/api/` | API version assembly, shared dependencies, response/error policy |
| `app/routers/` | Authentication, users, CRM, quotations, invoices, tasks, documents, meetings, workflows, AI, reports routers |
| `app/models/` | SQLAlchemy persistence entity definitions and relationship metadata |
| `app/schemas/` | Pydantic request, response, filter, pagination, and error contracts |
| `app/services/` | Transactional domain use cases and integration adapters |
| `app/database/` | Engine/session lifecycle, repository conventions, Alembic linkage |
| `app/core/` | Settings, authentication/authorization policy, logging, exceptions, middleware |
| `app/utils/` | Framework-independent helpers |
| `app/ai/` | AI orchestration, specialist interfaces, context assembly, output validation, audit logging |

`main.py` is reserved as the future FastAPI composition entry point; `requirements.txt` is reserved for dependency pinning. Neither is created during planning.

## AI orchestration

The AI gateway accepts an authenticated, tenant-scoped request and creates an AI activity record. An orchestrator classifies intent, selects one specialist, gathers minimal approved context through domain services, invokes the OpenAI provider adapter, validates the structured result, and returns a human-reviewable response. Any state-changing recommendation must be proposed first and executed only through the normal domain API/service after explicit approval.

| Specialist | Scope |
|---|---|
| Executive Assistant | Daily priorities, cross-module summaries, follow-up coordination |
| Sales Assistant | Lead qualification, customer context, quotation assistance, pipeline guidance |
| HR Assistant | Employee-oriented tasks, policy/document retrieval, meeting support |
| Finance Assistant | Invoice/quotation insights, payment follow-ups, financial summaries |
| Marketing Assistant | Campaign planning, audience context, approved content workflow support |

Specialists communicate through typed orchestration contracts, not direct calls to one another. Shared context and action capabilities are permission-scoped, tenant-scoped, logged, and versioned. OpenAI access stays behind one provider adapter to support retries, rate limits, redaction, cost tracking, and replacement later.
