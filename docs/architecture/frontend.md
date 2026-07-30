# Frontend plan

## Foundation

Use Next.js 16 App Router, React, TypeScript, Tailwind CSS, and shadcn/ui. Axios is the centralized HTTP transport. React Hook Form plus Zod governs client-side form state and validation. Auth is represented through a session boundary; the final choice is Auth.js or backend-issued JWT based on the authentication decision in the environment plan.

## `frontend/src` structure

| Directory | Responsibility |
|---|---|
| `app/` | Routes, route groups, nested layouts, loading/error states, metadata |
| `components/ui/` | shadcn/ui-derived primitives; no domain rules |
| `components/layouts/` | Auth shell, workspace shell, navigation, headers |
| `components/shared/` | Reusable domain-neutral pieces: tables, filters, status badges, empty states |
| `hooks/` | Reusable view and interaction hooks |
| `lib/` | Axios setup, auth helpers, validation helpers, shared constants |
| `services/` | Domain-specific API client modules and request/response mapping |
| `types/` | Shared UI, API, and domain TypeScript contracts |
| `contexts/` | Client-side providers for session, tenant, and UI state |
| `utils/` | Pure formatters and small non-UI helpers |
| `styles/` | Tailwind entry/theme conventions and global styling ownership |

## Route organization and page responsibility

Route groups keep URLs clean: `(auth)` isolates the login experience; `(workspace)` applies the authenticated shell, tenant context, and primary navigation.

| Planned route | Folder | Responsibility |
|---|---|---|
| `/login` | `app/(auth)/login` | Start authentication and present access errors |
| `/dashboard` | `app/(workspace)/dashboard` | Role-aware activity and operational summary |
| `/crm` | `app/(workspace)/crm` | Customers, leads, pipeline, and CRM activity workspace |
| `/ai-chat` | `app/(workspace)/ai-chat` | AI conversation entry point and result history |
| `/quotations` | `app/(workspace)/quotations` | Quote listing, drafting, approval, and lifecycle views |
| `/invoices` | `app/(workspace)/invoices` | Invoice listing, status, and payment-tracking views |
| `/email` | `app/(workspace)/email` | Email inbox/outbox and CRM-linked correspondence views |
| `/whatsapp` | `app/(workspace)/whatsapp` | WhatsApp conversation and message-management views |
| `/meetings` | `app/(workspace)/meetings` | Meeting calendar, agenda, notes, and follow-up views |
| `/documents` | `app/(workspace)/documents` | Document catalog, ownership, access, and linking views |
| `/tasks` | `app/(workspace)/tasks` | Personal/team task planning and completion views |
| `/reports` | `app/(workspace)/reports` | Aggregated KPI and export-ready report views |
| `/settings` | `app/(workspace)/settings` | Company, profile, memberships, integrations, preferences |

Pages must remain composition layers. Domain views and request logic should be extracted as a page becomes non-trivial.
