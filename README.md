# AI Employee OS

Planning-only foundation for a two-week, intern-built prototype. This repository intentionally contains no application source, runtime configuration, database schema, API implementation, Dockerfiles, or CI workflows.

## Documentation map

- [Architecture](docs/architecture/overview.md)
- [Frontend plan](docs/architecture/frontend.md)
- [Backend and AI plan](docs/architecture/backend-and-ai.md)
- [Database design](docs/database/data-model.md)
- [API plan](docs/api/rest-api.md)
- [Environment and Docker plan](docs/setup/environment-and-docker.md)
- [Development roadmap](docs/setup/roadmap.md)
- [Coding and API standards](docs/standards/coding-and-api-standards.md)
- [Team workflow](docs/team/development-guidelines.md)

## Repository layout

`frontend/` holds the planned Next.js application, organized under `src/`. `backend/` reserves the FastAPI application layers. `database/` reserves migration and seed ownership; `docker/` reserves container assets. `docs/` is the source of truth for prototype planning. `.github/` is reserved for future issue, pull-request, and CI metadata.

The root names `docker-compose.yml`, `.gitignore`, and the runtime entry/configuration files shown in the target design are intentionally not created in this planning-only phase.
