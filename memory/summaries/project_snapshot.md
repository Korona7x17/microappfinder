# Project Snapshot — MicroAppFinder

**Last Updated:** 2025-10-04
**Project:** MicroAppFinder - Micro app opportunity discovery system

## BRIEF_SUMMARY (2025-10-04 14:30)

C: Next.js 14 frontend; FastAPI backend; Docker-first deployment; Reddit API ToS compliance (48h cache + deletion sync); PostgreSQL + Redis for data

D: Reddit Pain Point Discovery feature planned; JWT auth with httponly cookies; PRAW client for Reddit API; Composite scoring (0.3×upvotes + 0.25×comments + 0.25×recency + 0.2×sentiment); User-scoped privacy enforcement

Δ: Memory system implemented (15 files); Feature 001-reddit-pain-point fully planned (7 design docs, 50 tasks); Reddit API credentials configured and verified working; CLAUDE.md updated with feature context

Q: None - all clarifications resolved for Reddit Pain Point Discovery feature

→: Execute setup tasks (T001-T003: dependencies + migration); Write failing tests (T004-T014); Begin implementation (T015+: models, services, endpoints)

## Active Context

**Stack:**
- Frontend: Next.js 14, Tailwind, shadcn/ui, Clerk auth
- Backend: FastAPI, SQLAlchemy, Redis/RQ
- Worker: crawl4ai, scikit-learn, OpenAI/Claude
- Data: PostgreSQL, Qdrant vector DB
- Infra: Docker, Docker Compose

**Completed:**
- Project structure scaffolding
- Claude-memory system setup (15 files: sessions, summaries, decisions, state, tools)
- Reddit Pain Point Discovery planning complete (001-reddit-pain-point branch)
  - Feature specification with 21 requirements
  - Implementation plan with 9 technical decisions
  - Data model (6 entities: User, Topic, SearchRun, RedditPost, PainPoint, JoinTable)
  - API contracts (8 endpoints in OpenAPI 3.0)
  - 50 implementation tasks (14 parallel-ready)
- Reddit API credentials configured and verified

**In Progress:**
- [ ] Reddit Pain Point Discovery implementation (Task T001-T050)
  - Next: T001-T003 (setup dependencies + migration)
  - Next: T004-T014 (write failing tests - TDD)
  - Next: T015+ (models, services, endpoints)

**Architecture Flow:**
Next.js Frontend → FastAPI Backend → Worker Pipeline → PostgreSQL/Qdrant + Redis Queue

## Reference Files
- Architecture: docs/microappfinder_system_architecture.md
- Pipeline: docs/microappfinder_pipeline_revised.md
- MVP Spec: docs/microappfinder_mvp_plus_spec.md
- Structure: PROJECT_STRUCTURE.md
