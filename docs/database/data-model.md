# Database design

PostgreSQL is the authoritative relational store. Use UUID primary keys, UTC timestamps, tenant identifiers, soft-delete/audit conventions where justified, and indexed foreign keys. Alembic owns all schema evolution; this document defines relationships only, not SQL or ORM models.

## Core relationships

| Entity | Relationships |
|---|---|
| Company | Has many users/memberships, customers, leads, quotations, invoices, tasks, activities, meetings, documents, workflows, notifications |
| User | Belongs to one or more companies through memberships; creates/owns/assignees tasks, activities, meetings, documents, and notifications |
| Customer | Belongs to one company; has many leads, quotations, invoices, activities, meetings, documents, and tasks |
| Lead | Belongs to a company and optionally a customer; has an owner user; has many activities, tasks, documents, and quotations; may convert to a customer |
| Quotation | Belongs to a company, customer, and optional originating lead; has a creator/owner; has many line items, activities, documents, and may produce invoices |
| Invoice | Belongs to a company, customer, and optional quotation; has a creator/owner; has many line items, activities, documents, and payment/status events |
| Task | Belongs to a company; has creator and optional assignee users; can link to a customer, lead, quotation, invoice, meeting, document, or workflow |
| Activity | Belongs to a company and actor user; polymorphically references the relevant business object; records human, system, integration, or AI events |
| Meeting | Belongs to a company; has organizer and many participant users/contacts; can link to customer, lead, tasks, documents, and activities |
| Document | Belongs to a company; has uploader/owner user; may link to customers, leads, quotations, invoices, tasks, meetings, and workflows via association records |
| Workflow | Belongs to a company; has creator/owner user; has many workflow runs/actions and may create tasks, notifications, activities, or linked domain records |
| Notification | Belongs to a company and recipient user; may reference the resource/event that caused it |

## Supporting design decisions

- A `company_memberships` association supports users who work in multiple companies and centralizes role/permission assignment.
- Quotation and invoice line items are child entities because their details must remain historically stable.
- Meeting participants and document links use association entities, preserving role and relation metadata.
- Activities provide a unified chronological timeline. Prefer explicit foreign keys where a relationship is core; use a controlled resource-reference convention only for cross-domain audit entries.
- Workflows require definitions separate from runs so changes do not rewrite historical execution state.
- Documents store metadata and a provider object key/URL; binary content should live in external object storage.

## Integrity and access rules

All child records inherit company scope from their owning aggregate. API/service authorization must verify that every referenced record belongs to the active company. Preserve quotation and invoice snapshots after issuance. Define archival rather than hard deletion for financial and audit records.
