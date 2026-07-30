# Team development guidelines

## Git workflow

- `main` is protected and always deployable/demo-ready.
- `develop` is the integration branch for the prototype.
- Create short-lived branches from `develop`: `feature/<module>-<summary>`, `fix/<module>-<summary>`, or `docs/<summary>`.
- Open a pull request into `develop`; use a release pull request from `develop` into `main` for the demo milestone.
- Do not push directly to protected branches.

## Pull-request process

1. Link the task/issue and state the user-visible outcome, scope, and test evidence.
2. Keep changes focused; separate unrelated refactors and generated files.
3. Request one peer review minimum; require module-owner review for cross-cutting changes.
4. Reviewer checks architecture boundaries, tenant authorization, error/loading states, migration impact, and documentation impact.
5. Resolve review threads, ensure checks pass, then squash merge unless the team agrees otherwise.

## Team operating rules

- Maintain a module-owner/deputy matrix to avoid conflicting edits.
- Sync daily on dependencies, API contract changes, database migrations, and blockers.
- Discuss schema and shared-contract changes before coding; update the appropriate planning document in the same pull request.
- Keep commits small and descriptive. Rebase or merge `develop` before handoff according to team preference.
- Use issues to record scope, acceptance criteria, dependencies, and test/demo scenario.
- Record material shortcuts, known risks, and deferred work in a visible backlog.

## Documentation responsibilities

| Document area | Maintainer responsibility |
|---|---|
| `docs/setup` | Onboarding, runtime assumptions, release/demo instructions |
| `docs/architecture` | Module boundaries, technical decisions, dependency map |
| `docs/database` | Relationship changes, migration notes, data ownership |
| `docs/api` | Endpoint contracts, lifecycle rules, compatibility notes |
| `docs/standards` | Code review expectations and shared conventions |
| `docs/team` | Workflow, ownership, meeting cadence, decision log |
