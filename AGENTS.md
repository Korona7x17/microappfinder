# Repository Guidelines

## Project Structure & Modules
MicroAppFinder is a monorepo with core services in `apps/`: `web/` (Next.js routes in `src/app`, UI parts in `src/components`, helpers in `src/lib`), `api/` (FastAPI with routers, services, and models inside `app/`), and `worker/` (RQ jobs in `worker/pipeline` and `worker/tasks`). Shared contracts live in `packages/types` and `packages/schemas`. Operational assets stay in `infra/` (Alembic + Docker), long-form docs in `docs/`, and research notes in `specs/`.

## Build, Test, and Development Commands
- `make install` boots JS and Python dependencies for every app.
- `make dev` starts Postgres/Redis/Qdrant; run `make dev-web`, `make dev-api`, and `make dev-worker` in separate shells for live reload.
- `make start`/`make stop` control the docker-compose stack, `docker-compose logs -f` tails services.
- `make migrate` executes `alembic upgrade head` from `infra/migrations`.
- `make test` launches `pytest` then the web test script; supplement with `npm run lint`, `npm run type-check`, or `pytest -k <pattern>` when iterating locally.

## Coding Style & Naming Conventions
`.editorconfig` keeps LF endings, trims trailing whitespace, and enforces 2-space TS/JS and 4-space Python indents. Format TS/JS with Prettier (`npx prettier --write`) using the repo defaults (100 char width, semicolons, single quotes). Python code should satisfy PEP 8, include type hints, and be formatted with `black`. Use PascalCase for React components, camelCase for hooks and utilities, and snake_case for Python modules, SQLAlchemy models, and test files.

## Testing Guidelines
API tests live under `apps/api/tests/{unit,integration,contract}`; create new modules as `test_*.py` and rely on the shared fixtures in `conftest.py`. Uphold the 80% coverage expectation from `CONTRIBUTING.md` and call out any intentional gaps in your PR. Frontend assertions belong in `apps/web/src/__tests__` (React Testing Library recommended). Until a Jest runner is wired to `npm test`, guard changes with `npm run lint` + `npm run type-check` in CI and add Playwright or Vitest scripts when UI coverage is added.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) and branch names such as `feature/<slug>` or `fix/<ticket>`. PRs should summarise the change, link issues, list migrations, and attach screenshots or JSON samples when you touch UI or API contracts. Keep docs in sync—update `docs/` or `PROJECT_STRUCTURE.md` when architecture moves—and ensure all Makefile commands pass before requesting review.
