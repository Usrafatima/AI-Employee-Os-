# REST API plan

Base all HTTP modules under a versioned prefix such as `/api/v1`. Router paths are plural nouns; standard list endpoints support tenant-safe filtering, sorting, and pagination. Schemas consistently envelope validation errors, and services enforce authorization before returning or mutating data.

| Module | Endpoint responsibility |
|---|---|
| Authentication | Sign-in/session or token lifecycle, sign-out, refresh/revocation, current identity, password/account recovery if in scope |
| Users | Current profile, company memberships, roles, invitations, user administration |
| CRM | Customer and lead lifecycle, assignment, pipeline state, associated activities and timeline views |
| Quotations | Quotation drafting, line-item lifecycle, approval/status transitions, delivery/export orchestration |
| Invoices | Invoice lifecycle, line items, status/payment events, links to quotations and customers |
| Tasks | Task CRUD, assignment, priority/status transitions, related-resource links, personal/team views |
| Documents | Metadata, upload/download authorization workflow, categorization, ownership, related-resource links |
| Meetings | Scheduling metadata, attendees, agendas/notes, follow-up task coordination, calendar integration boundary |
| Workflows | Workflow definition, activation, execution history, manual trigger and approval-state visibility |
| AI | Tenant-scoped assistant conversations, request submission, response retrieval, approval/audit history |
| Reports | Read-only, permission-aware operational and financial aggregates plus export-job requests |

## Contract rules

- Every endpoint receives identity and active company context from authentication middleware/dependencies.
- Routers contain HTTP semantics only; they delegate business decisions to services.
- Write operations define idempotency and concurrency behavior before implementation.
- Prefer nested resource actions only when the parent relationship is unambiguous; otherwise provide filtered top-level resources.
- Files use a two-step, authorized upload/download flow; file bytes do not pass through normal JSON resource endpoints.
- API documentation is generated from schemas/routes once implementation begins and reviewed against this plan.
