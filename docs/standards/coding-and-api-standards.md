# Coding and API standards

## Frontend

- TypeScript strictness and explicit domain/API types are the default; avoid untyped boundaries.
- Prefer server components by default, using client components only for browser state and interactivity.
- Build from shadcn/ui primitives and shared components before creating feature-specific variants.
- Keep API calls in `services/`, validation schemas near the relevant form/domain, and side effects out of presentational components.
- Use accessible labels, keyboard behavior, loading states, empty states, and error states for every user-facing flow.

## Backend

- Route handlers handle transport; services own use cases; persistence models never leak directly into API responses.
- Use schemas for all request/response boundaries and a consistent error format.
- Every service operation accepts/derives tenant and actor context, and records relevant activities/audits.
- Keep external providers behind adapters and ensure retry, timeout, idempotency, and failure behavior are defined.
- Use database migrations for every schema change; never edit deployed databases manually.

## REST standards

- Version public endpoints, use resource-oriented nouns, and use conventional HTTP semantics/status codes.
- Paginate collection responses and define filter/sort field allow-lists per module.
- Define authorization, validation, and lifecycle transitions in the endpoint/module documentation before coding.
- Return stable public identifiers and ISO-8601 UTC timestamps.
- Treat compatibility changes as versioned or additive; document deprecation before removal.

## Security baseline

- Enforce company isolation at every query and related-resource lookup.
- Never place secrets or private AI/provider data in browser-accessible variables.
- Audit sensitive access and all AI-proposed or approved actions.
- Validate file type/size and authorize both upload and download.
