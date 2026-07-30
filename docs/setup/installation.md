# Installation plan

This document defines the future onboarding sequence; it does not provide executable setup commands in the planning phase.

## Prerequisites to standardize

- Node.js version compatible with Next.js 16 and a single chosen package manager.
- Python version compatible with the chosen FastAPI/SQLAlchemy toolchain and a single virtual-environment workflow.
- PostgreSQL version, local access method, and a database naming convention.
- Docker and Docker Compose version for the containerized development path.
- Access to the team secret manager and any required OpenAI, email, WhatsApp, calendar, and storage accounts.

## Future onboarding checklist

1. Clone the repository and review the architecture, standards, and environment-variable documentation.
2. Create local ignored environment files from the approved variable-name template and obtain secrets through the team channel.
3. Start PostgreSQL through the chosen local or containerized approach and apply the approved migration baseline.
4. Install frontend and backend dependencies using their locked toolchains.
5. Start frontend and backend development processes; verify health, authentication, and a tenant-scoped sample flow.
6. Run the agreed formatting, linting, type-checking, and test checks before opening a pull request.

Before implementation, document exact supported versions, commands, lockfile policy, migration command, seed-data procedure, and troubleshooting guidance here.
